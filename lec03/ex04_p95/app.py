# -*- coding: utf-8 -*-
"""구름월드 RAG 에이전트 서비스 — 서비스 표준 템플릿 구성 (실행: fastapi dev app.py --port 8031)."""

import os

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI
from langchain.chat_models import init_chat_model
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel

load_dotenv(find_dotenv(usecwd=True))

THRESHOLD = 1.5
NO_EVIDENCE = "문서에서 근거를 찾지 못했습니다. 안내 창구로 문의해 주세요."
SYSTEM = ("너는 시설 안내 담당자다. 인사말처럼 검색이 필요 없는 말에는 바로 답한다. "
          "그 밖의 모든 질문은 반드시 faq_search 도구로 근거를 먼저 찾고, 도구 결과에 있는 내용으로만 답한다. "
          "도구 결과가 '검색 결과 없음'이면 네가 아는 지식으로 답하지 말고 "
          f"'{NO_EVIDENCE}'라고만 답한다.")

emb = OpenAIEmbeddings(model="text-embedding-3-small")
db = Chroma(persist_directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db"), embedding_function=emb)


def retrieve(query: str, k: int = 2):
    return db.similarity_search_with_score(query, k=k)


@tool(parse_docstring=True)
def faq_search(query: str) -> str:
    """시설 FAQ 문서에서 질문과 관련된 청크를 검색한다. 시설 이용, 요금, 환불, 운영 관련 질문에 쓴다.

    Args:
        query: 검색할 질의문. 결과가 없으면 표현을 바꿔 재검색할 수 있다.
    """
    hits = retrieve(query)
    good = [(d, s) for d, s in hits if s <= THRESHOLD]
    if not good:
        return f"검색 결과 없음 (최고 유사도 점수 {hits[0][1]:.2f}가 임계값 {THRESHOLD}를 넘음). 질의를 바꿔 다시 검색하거나, 모른다고 답하라."
    return "\n---\n".join(f"[score {s:.2f}] {d.page_content}" for d, s in good)


llm = init_chat_model("openai/gpt-5.6-luna", model_provider="litellm")
llm_tools = llm.bind_tools([faq_search])


# ── ① 입출력 모양 선언
class AskIn(BaseModel):
    question: str


class AskOut(BaseModel):
    answer: str


# ── ② 처리 함수 구현
def run_rag_agent(question: str, max_turn: int = 5) -> str:
    messages = [SystemMessage(content=SYSTEM), HumanMessage(content=question)]
    searched, found = False, False
    for _ in range(max_turn):
        res = llm_tools.invoke(messages)
        if not res.tool_calls:
            if searched and not found:
                return NO_EVIDENCE
            return res.content
        messages.append(res)
        for call in res.tool_calls:
            searched = True
            result = faq_search.invoke(call["args"])
            if not result.startswith("검색 결과 없음"):
                found = True
            messages.append(ToolMessage(content=result, tool_call_id=call["id"]))
    return "반복 한도 초과"


# ── ③ 앱 생성·엔드포인트 등록
app = FastAPI(title="구름월드 RAG 에이전트 서비스")


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=AskOut)
def ask_endpoint(req: AskIn) -> AskOut:
    return AskOut(answer=run_rag_agent(req.question))


# ── ④ 기동·호출 확인: 터미널에서 `fastapi dev app.py --port 8031` 뒤 `python run_samples.py 8031`
