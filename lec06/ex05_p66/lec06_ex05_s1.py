import operator
import os

from dotenv import load_dotenv, find_dotenv
from typing import Annotated, TypedDict

from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from pydantic import BaseModel, Field

load_dotenv(find_dotenv(usecwd=True))
if not os.environ.get("OPENAI_API_KEY"):
    raise SystemExit("agentic-ai 폴더의 .env 파일에 OPENAI_API_KEY 한 줄을 넣습니다.")

llm = init_chat_model("openai/gpt-5.6-luna", model_provider="litellm")
print("모델 준비를 마쳤습니다.")

class Section(BaseModel):
    name: str = Field(description="문단 제목")
    description: str = Field(description="이 문단에 담을 내용 한 줄")


class Sections(BaseModel):
    sections: list[Section] = Field(description="안내문 문단 계획")


class GuideState(TypedDict):
    topic: str                                # 안내문 주제
    sections: list                            # orchestrator가 세운 문단 계획
    written: Annotated[list, operator.add]    # worker들이 동시에 덧붙이는 부분 결과 (리듀서 필수)
    guide: str                                # 완성 안내문


class WorkerState(TypedDict):                 # worker 하나가 받는 자기 작업 단위
    section: Section
    written: Annotated[list, operator.add]


print("부모 상태의 키:", list(GuideState.__annotations__))
print("worker 상태의 키:", list(WorkerState.__annotations__))

planner = llm.with_structured_output(Sections)


def orchestrator(state: GuideState) -> dict:
    """주제를 보고 문단 계획을 세운다. 계획의 길이가 worker 수가 된다."""
    plan = planner.invoke([
        SystemMessage("사내 안내문 문단 계획을 필요한 만큼(2~4개) 세운다."),
        HumanMessage(f"주제: {state['topic']}"),
    ])
    print(f"  [orchestrator] 진입 -> 문단 {len(plan.sections)}개 계획")
    return {"sections": plan.sections}


def worker(state: WorkerState) -> dict:
    """자기 문단 하나를 두 문장으로 쓴다."""
    sec = state["section"]
    print(f"    [worker] 진입: {sec.name}")
    res = llm.invoke([
        SystemMessage("받은 문단 하나를 두 문장으로 쓴다."),
        HumanMessage(f"{sec.name}\n{sec.description}"),
    ])
    return {"written": [f"## {sec.name}\n{res.content.strip()}"]}


def synthesizer(state: GuideState) -> dict:
    """부분 결과 전부를 순서대로 이어 붙인다 (모델을 부르지 않는다)."""
    print(f"  [synthesizer] 진입 -> 부분 결과 {len(state['written'])}개 합침")
    return {"guide": "\n\n".join(state["written"])}

g = StateGraph(GuideState)
g.add_node("orchestrator", orchestrator)
g.add_node("worker", worker)          # 한 번만 등록한다. 팬아웃되는 수는 실행 시점에 정해진다
g.add_node("synthesizer", synthesizer)

print("등록한 노드:", list(g.nodes))

def assign_workers(state: GuideState):
    """노드 이름 대신 Send 목록을 돌려준다. 목록의 길이가 이번 실행의 worker 수다."""
    return [Send("worker", {"section": sec}) for sec in state["sections"]]


g.add_edge(START, "orchestrator")
g.add_conditional_edges("orchestrator", assign_workers, ["worker"])
g.add_edge("worker", "synthesizer")
g.add_edge("synthesizer", END)

print("고정 엣지 수:", len(g.edges))

graph = g.compile()

TOPIC = "사내 메신저 보안 수칙 안내"

print(f"=== 주제: {TOPIC} ===")
out = graph.invoke({"topic": TOPIC, "sections": [], "written": [], "guide": ""})

print()
print(f"[최종 상태] 계획한 문단 {len(out['sections'])}개 / 팬아웃된 worker {len(out['written'])}개")
print("--- 안내문 ---")
print(out["guide"])