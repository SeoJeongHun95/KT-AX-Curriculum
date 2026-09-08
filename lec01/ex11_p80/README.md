# 학습 도우미 워크플로우 — 배치와 사용법 (직접 채우는 판)

## 어디에 두는가

실습 10에서 만든 학습 폴더(`agentic-ai\study\`) 안에 둡니다. 새 폴더를 만들지 않습니다.

| 이 묶음의 것 | 두는 위치 |
|---|---|
| `.claude\agents\` · `.claude\skills\study-workflow\` · `.claude\hooks\` · `.claude\settings.json` | `study\.claude\` 아래에 그대로 복사합니다. 실습 10의 `CLAUDE.md`와 스킬 두 개(`eli5`·`grilling`)는 그대로 남습니다 |
| `wiki\` | `study\wiki\`로 복사합니다 |

```powershell
Copy-Item -Path "<묶음 폴더 경로>\.claude\*" -Destination study\.claude\ -Recurse -Force
Copy-Item -Path "<묶음 폴더 경로>\wiki" -Destination study\wiki -Recurse
```

## 무엇을 채우는가

- 채우는 파일: `.claude\agents\` 세 파일의 `description`과 본문 · `.claude\skills\study-workflow\SKILL.md`의 `description`·`argument-hint`와 본문 · 이 README의 「어떻게 쓰는가」.
- 이미 완성되어 있는 파일: `.claude\settings.json` · `.claude\hooks\update_index.py` · 에이전트와 스킬 머리말의 `tools`·`allowed-tools`. 이들은 고치지 않습니다. 파이썬 코드는 이 실습에서 쓰지 않습니다.
- 각 파일의 「여기에 …을 씁니다」 문장을 지우고 그 위치에 내용을 씁니다. 학습 도우미의 원칙은 실습 10의 `CLAUDE.md`에 이미 있으므로 여기서는 워크플로우만 씁니다.

## 어떻게 쓰는가

1. 여기에 어느 폴더에서 무엇을 실행해 시작하는지 씁니다.
2. 여기에 학습 질문을 어떻게 입력하는지 씁니다.
3. 여기에 입력한 뒤 무엇이 일어나는지 씁니다.
4. 여기에 최종 답변이 어디로 나오는지 씁니다.
5. 여기에 학습 노트가 어느 폴더에 어떤 이름으로 저장되고, 저장 뒤 훅이 무엇을 하는지 씁니다.
