# 학습 노트 훅 스크립트 — wiki/ 폴더에 학습 노트(.md)가 저장되거나 고쳐진 직후에만 실행됩니다.
#
# 하는 일:
#   학습 노트의 규격(파일 이름 · 필수 절 4개)을 검사하고,
#   통과하면 wiki/INDEX.md 목록을 다시 만들고, 어기면 종료 코드 2로 이유를 돌려줍니다.
#   종료 코드 2의 메시지는 에이전트에게 전달되어, 에이전트가 노트를 고쳐 다시 저장합니다.
#
# 훅의 원리: 훅은 settings.json에서 「이벤트(PostToolUse) + 도구 이름(Write·Edit) + 조건(if: 어느 파일인가)」으로 걸립니다.
# 조건이 `Write(wiki/*.md)`·`Edit(wiki/*.md)` 이므로 wiki/ 바로 아래의 .md 파일을 쓸 때만 이 스크립트가 뜹니다.
# 다른 파일을 쓸 때는 스크립트가 아예 실행되지 않습니다. 아래의 경로 검사(is_note)는 이중 안전장치입니다.
# 규격에 맞는가의 판단은 이 스크립트가 합니다. 에이전트의 판단에 맡기지 않습니다.

import json
import os
import re
import sys

# 훅이 주고받는 JSON과 메시지는 UTF-8입니다. Windows 기본 인코딩(cp949)이면 한글 파일 이름이 깨지므로 고정합니다.
for stream in (sys.stdin, sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WIKI = os.path.join(BASE, "wiki")
NAME_RULE = re.compile(r"\d{4}-\d{2}-\d{2}_.+\.md")
REQUIRED_SECTIONS = ("질문", "자료", "요약", "답변")


def saved_path() -> str:
    """훅이 표준입력으로 주는 JSON에서 방금 저장된 파일 경로를 꺼냅니다."""
    try:
        data = json.load(sys.stdin)
    except Exception:
        return ""
    return str((data.get("tool_input") or {}).get("file_path") or "")


def is_note(path: str) -> bool:
    """wiki/ 폴더 안의 .md 파일(INDEX.md 제외)만 학습 노트로 봅니다."""
    if not path:
        return False
    full = os.path.normcase(os.path.abspath(path))
    wiki = os.path.normcase(WIKI) + os.sep
    return os.path.dirname(full) + os.sep == wiki and full.endswith(".md") and os.path.basename(full) != os.path.normcase("INDEX.md")  # wiki 바로 아래만 (settings의 if 조건과 같은 범위)


def problems_of(path: str) -> list[str]:
    """규격 위반 사항을 문장 목록으로 돌려줍니다. 비어 있으면 통과입니다."""
    found = []
    name = os.path.basename(path)
    if not NAME_RULE.fullmatch(name):
        found.append("파일 이름이 YYYY-MM-DD_주제.md 형식이 아닙니다")
    try:
        text = open(path, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError):
        return found + ["파일을 UTF-8로 읽을 수 없습니다(메모장은 「UTF-8」로 저장)"]
    for section in REQUIRED_SECTIONS:
        if not re.search(rf"^#+\s*{section}\b", text, re.M):
            found.append(f"「{section}」 절이 없습니다")
    return found


def first_line_after(text: str, section: str) -> str:
    """지정한 절 제목 다음의 첫 문장을 돌려줍니다. 목록에 한 줄 요약으로 씁니다."""
    match = re.search(rf"^#+\s*{section}\b[^\n]*\n+([^\n#]+)", text, re.M)
    return match.group(1).strip()[:80] if match else ""


def rebuild_index() -> int:
    """규격을 지킨 노트만 모아 INDEX.md를 다시 만듭니다. 최신 날짜가 위에 옵니다."""
    lines = []
    for name in sorted(os.listdir(WIKI), reverse=True):
        path = os.path.join(WIKI, name)
        if name == "INDEX.md" or not NAME_RULE.fullmatch(name) or problems_of(path):
            continue
        text = open(path, encoding="utf-8", errors="replace").read()
        date, title = name[:10], name[11:-3].replace("_", " ")
        question = first_line_after(text, "질문")
        lines.append(f"- {date} · [{title}]({name}) — {question}")
    body = ["# 학습 노트 목록", "", f"총 {len(lines)}개", ""] + lines
    with open(os.path.join(WIKI, "INDEX.md"), "w", encoding="utf-8") as fp:
        fp.write("\n".join(body) + "\n")
    return len(lines)


def main() -> int:
    path = saved_path()
    if not is_note(path) or not os.path.isdir(WIKI):
        return 0
    problems = problems_of(path)
    if problems:
        print(
            f"학습 노트 규격 위반 ({os.path.basename(path)}): " + " / ".join(problems)
            + ". 규격에 맞게 고쳐 같은 위치에 다시 저장하십시오.",
            file=sys.stderr,
        )
        return 2
    count = rebuild_index()
    print(f"wiki/INDEX.md 갱신: 학습 노트 {count}개")
    return 0


if __name__ == "__main__":
    sys.exit(main())
