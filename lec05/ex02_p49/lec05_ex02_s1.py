import io
import os
import warnings
from contextlib import redirect_stdout

from dotenv import load_dotenv, find_dotenv

from langchain.chat_models import init_chat_model
from langsmith import Client
from pydantic import BaseModel, Field

warnings.filterwarnings("ignore", message="Pydantic serializer warnings")
warnings.filterwarnings("ignore", message="IProgress not found")

load_dotenv(find_dotenv(usecwd=True))
if not os.environ.get("OPENAI_API_KEY"):
    raise SystemExit("agentic-ai 폴더의 .env 파일에 OPENAI_API_KEY 한 줄을 넣습니다.")
if not os.environ.get("LANGSMITH_API_KEY"):
    raise SystemExit("agentic-ai 폴더의 .env 파일에 LANGSMITH_API_KEY 한 줄을 넣습니다.")

os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_PROJECT"] = "sesac-lec05-ex02"

MODEL = "openai/gpt-5.6-luna"

llm = init_chat_model(MODEL, model_provider="litellm")

FAQ = """
[환불] Q: 자유이용권 환불 규정 알려 주세요
A: 이용일 전날까지 취소하면 전액 환불됩니다. 이용일 당일 취소는 50%만 환불됩니다. 입장 뒤에는 환불되지 않습니다.
[운영] Q: 운영 시간이 어떻게 되나요?
A: 평일은 10시부터 19시까지, 주말은 10시부터 21시까지 운영합니다.
[야간] Q: 야간개장은 언제 하나요?
A: 금요일과 토요일에는 22시까지 야간개장을 합니다. 야간개장 날에는 20시 30분에 야간 퍼레이드가 있습니다.
[주차] Q: 주차 요금은 얼마인가요?
A: 자유이용권 소지자는 4시간까지 무료이고, 그 뒤로는 시간당 2,000원입니다.
"""

SERVICE_GUIDE = (
    "너는 놀이공원 구름월드의 안내 담당자다. 아래 FAQ에 적힌 내용만 근거로 두 문장 안에서 답한다. "
    "인사말에는 짧은 인사로 답한다. "
    "FAQ에 없는 내용을 물으면 '해당 내용은 확인할 수 없습니다.'라고만 답한다.\n"
    "=== FAQ ===\n" + FAQ
)

def answer(question: str) -> str:
    """안내 서비스: 질문을 받아 FAQ만 근거로 답을 돌려준다."""
    res = llm.invoke([("system", SERVICE_GUIDE), ("human", question)])
    return res.content.strip()

client = Client()
DATASET = "sesac-lec05-ex02-golden"

GOLDEN = [
    {"question": "안녕하세요!",
     "expect": "인사에 짧게 답한다", "must_know": True},
    {"question": "자유이용권 환불 규정 알려 주세요",
     "expect": "전날까지 전액 환불, 당일 50% 환불, 입장 뒤 환불 불가로 답한다", "must_know": True},
    {"question": "야간개장 때 퍼레이드 하나요?",
     "expect": "야간개장 날 20시 30분에 야간 퍼레이드가 있다고 답한다", "must_know": True},
    {"question": "파이썬 리스트 정렬은 어떻게 하나요?",
     "expect": "FAQ 밖 질문이므로 확인할 수 없다고 답한다", "must_know": False},
]

if client.has_dataset(dataset_name=DATASET):
    print(f"데이터셋 '{DATASET}'이 이미 있어 재사용합니다.")
else:
    ds = client.create_dataset(dataset_name=DATASET, description="구름월드 안내 서비스 골든 질문 4개")
    client.create_examples(
        dataset_id=ds.id,
        examples=[{"inputs": {"question": g["question"]},
                   "outputs": {"expect": g["expect"], "must_know": g["must_know"]}} for g in GOLDEN],
    )

def target(inputs: dict) -> dict:
    """평가 대상: 질문을 꺼내 안내 서비스를 부르고 답을 돌려준다."""
    return {"answer": answer(inputs["question"])}

print(target({"question": "안녕하세요!"}))

def rule_content(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    """규칙 채점자: FAQ 밖 질문은 '확인할 수 없' 표현이 있어야 1점, FAQ 안 질문은 답이 비어 있지 않으면 1점."""
    ans = outputs.get("answer", "") or ""
    if reference_outputs["must_know"]:
        ok = len(ans.strip()) > 0
    else:
        ok = "확인할 수 없" in ans
    return {"key": "rule_content", "score": int(ok)}


class Judge(BaseModel):
    faithful: bool = Field(description="답이 기대 조건에 부합하고 지어낸 내용이 없으면 true")
    reason: str = Field(description="판정 근거를 한 문장으로 적는다")


judge_llm = llm.with_structured_output(Judge)

JUDGE_GUIDE = (
    "너는 엄격한 채점자다. 질문·기대 조건·답변을 보고, "
    "답변이 기대 조건에 부합하며 지어낸 내용이 없는지 판정하라."
)


def judge_faithful(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    """모델 채점자: 구조화 출력을 강제한 모델이 부합 여부를 판정한다."""
    j = judge_llm.invoke(
        JUDGE_GUIDE
        + f"\n질문: {inputs['question']}"
        + f"\n기대 조건: {reference_outputs['expect']}"
        + f"\n답변: {outputs.get('answer', '')}"
    )
    return {"key": "judge_faithful", "score": int(j.faithful), "comment": j.reason}


sample_out = target({"question": GOLDEN[3]["question"]})
sample_ref = {"expect": GOLDEN[3]["expect"], "must_know": GOLDEN[3]["must_know"]}
print(rule_content({"question": GOLDEN[3]["question"]}, sample_out, sample_ref))
print(judge_faithful({"question": GOLDEN[3]["question"]}, sample_out, sample_ref))



captured = io.StringIO()
with redirect_stdout(captured):
    res = client.evaluate(
        target,
        data=DATASET,
        evaluators=[rule_content, judge_faithful],
        experiment_prefix="sesac-v1",
        max_concurrency=1,
        metadata={"model": MODEL},
    )
print("실험 이름:", res.experiment_name)
print("실험 URL: (LangSmith 화면에서 확인)")
print()

judge_scores = []
for r in res:
    question = r["example"].inputs["question"]
    scores = {f.key: f.score for f in r["evaluation_results"]["results"]}
    judge_scores.append(scores.get("judge_faithful") or 0)
    print(f"{question:<24} rule_content={scores.get('rule_content')} judge_faithful={scores.get('judge_faithful')}")

THRESHOLD = 0.5
mean = sum(judge_scores) / len(judge_scores)
print()
print(f"게이트: judge_faithful 평균 {mean:.2f} / 기준 {THRESHOLD} -> {'통과' if mean >= THRESHOLD else '차단'}")
