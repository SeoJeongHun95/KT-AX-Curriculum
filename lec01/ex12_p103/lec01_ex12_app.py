# 단계 ①~③을 파일 하나에 모은 서비스 파일. `fastapi dev lec01_ex12_app.py` 로 켠다.
from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI
from litellm import completion
from pydantic import BaseModel

load_dotenv(find_dotenv(usecwd=True))
MODEL = "openai/gpt-5.6-luna"
# 같은 OPENAI 키로 호출되는 대체 모델(2026-09-05 확인): openai/gpt-4o-mini · openai/gpt-4.1-mini · openai/gpt-5-mini · openai/gpt-5.4-mini


# ① 입출력 모양 선언
class AskRequest(BaseModel):
    question: str


# ② 처리 함수 구현
def ask(question: str, model: str = MODEL) -> str:
    """질문을 받아 모델의 답변 문자열을 돌려준다."""
    response = completion(
        model=model,
        messages=[{"role": "user", "content": question}],
    )
    return response.choices[0].message.content


# ③ 앱 생성·엔드포인트 등록
app = FastAPI()


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.post("/ask")
def ask_endpoint(req: AskRequest) -> dict:
    return {"answer": ask(req.question)}
