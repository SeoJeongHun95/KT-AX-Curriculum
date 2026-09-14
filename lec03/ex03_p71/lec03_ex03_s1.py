import csv
import os

from dotenv import load_dotenv, find_dotenv

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

load_dotenv(find_dotenv(usecwd=True))
if not os.environ.get("OPENAI_API_KEY"):
    raise SystemExit("agentic-ai 폴더의 .env 파일에 OPENAI_API_KEY 한 줄을 넣습니다.")

CSV_PATH = "day05_faq_구름월드.csv"

docs = []
with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
    for i, row in enumerate(csv.DictReader(f), start=1):
        if not (row.get("Question") or "").strip():
            continue
        text = f"[{row['Category']}] Q: {row['Question']}\nA: {row['Answer']}"
        docs.append(Document(page_content=text, metadata={"row": i, "category": row["Category"]}))

emb = OpenAIEmbeddings(model="text-embedding-3-small")

vec = emb.embed_query("자유이용권 환불이 되나요?")
 
db = Chroma.from_documents(
    docs, emb,
    persist_directory="chroma_db",
    ids=[f"row-{d.metadata['row']}" for d in docs],
)

q = "자유이용권 환불이 되나요?"
for d, s in db.similarity_search_with_score(q, k=3):
    print(f"  score={s:.4f} | {d.page_content[:60].replace(chr(10), ' / ')}")

THRESHOLD = 1.5
NO_EVIDENCE = "문서에서 근거를 찾지 못했습니다. 안내 창구로 문의해 주세요."

def answer_or_cut(question: str) -> str:
    d, s = db.similarity_search_with_score(question, k=1)[0]
    verdict = "통과" if s <= THRESHOLD else "컷"
    return d.page_content if s <= THRESHOLD else NO_EVIDENCE

for q in ["자유이용권 환불이 되나요?", "파이썬 리스트 정렬은 어떻게 하나요?"]:
    print("  결과:", answer_or_cut(q).replace(chr(10), " / "))
    print()
