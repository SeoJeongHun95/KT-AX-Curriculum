import os

from datetime import datetime
from dotenv import load_dotenv, find_dotenv

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool

load_dotenv(find_dotenv(usecwd=True))
if not os.environ.get("OPENAI_API_KEY"):
    raise SystemExit("agentic-ai 폴더의 .env 파일에 OPENAI_API_KEY 한 줄을 넣습니다.")

llm = init_chat_model("openai/gpt-5.6-luna", model_provider="litellm")

FAQ = {
    "운영시간": "매일 09:30~21:00에 운영합니다.",
    "주차": "주차장은 4,000대 규모이며 최초 30분은 무료입니다.",
    "환불": "이용일 전날까지 전액 환불, 당일은 50% 환불입니다.",
}

@tool(parse_docstring=True)
def faq_lookup(topic: str) -> str:
    """구름월드 FAQ에서 항목을 조회한다. 시설 이용에 관한 질문이면 먼저 이 도구로 항목을 찾아본다.
 
    Args:
        topic: 조회할 항목 이름. 예: 운영시간, 주차, 환불
    """
    return FAQ[topic]
 
@tool
def get_now() -> str:
    """현재 날짜와 시각을 돌려준다."""
    return datetime.now().strftime("%Y-%m-%d %H:%M")


llm_tools = llm.bind_tools([faq_lookup, get_now])
TOOLS = {t.name: t for t in [faq_lookup, get_now]}


def run_agent(question: str, max_turn: int = 4) -> str:
    messages = [HumanMessage(question)]
    for _ in range(max_turn):
        res = llm_tools.invoke(messages)
        if not res.tool_calls:
            return res.content
        messages.append(res)
        for call in res.tool_calls:
            try :    
                result = TOOLS[call["name"]].invoke(call["args"])
            except Exception as e:
                result = f"도구 실행 오류 :{type(e).__name__} :{e}"
            messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))
    return "반복 한도 초과"

QUESTIONS = [
    "운영시간이 어떻게 되나요?",
    "지금 몇 시인가요?",
    "애완동물이랑 탈수있는 놀이기구는 뭔가요",
]

for i in (QUESTIONS):
    print(f"=== {i} ===")
    answer = run_agent(i)
    print(f"  [최종 답] {answer}")
    print()