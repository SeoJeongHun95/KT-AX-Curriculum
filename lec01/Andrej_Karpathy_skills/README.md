# Karpathy 가이드라인 스킬

AI 코딩 에이전트가 흔히 저지르는 실수(과한 설계, 요청 밖 수정, 확인 없는 가정, 검증 없는 완료 선언)를 줄이는 행동 지침입니다. 수강생이 Claude Code에서 바로 쓸 수 있도록 스킬 형태로 넣어 두었습니다.

- 원본: forrestchang의 GitHub 저장소 `andrej-karpathy-skills` (MIT 라이선스). Andrej Karpathy가 LLM 코딩의 함정을 정리한 글에서 출발한 자료입니다.
- 이 폴더의 파일
  - `.claude\skills\karpathy-guidelines\SKILL.md`: 스킬 본문입니다. 네 원칙(생각한 뒤 코딩·단순함 우선·수정은 필요한 곳만·검증 가능한 목표)이 들어 있습니다.
  - `EXAMPLES.md`: 네 원칙마다 「에이전트가 흔히 하는 잘못」과 「고친 모습」을 코드로 보인 예시입니다. 읽기 자료입니다.
  - `CLAUDE.md`: 원본 저장소의 지침 파일입니다. 내용은 `SKILL.md`와 같으므로 **복사하지 않습니다.** 여러분의 `CLAUDE.md`를 덮어쓰지 않도록 이 폴더에만 둡니다.

## 어디에 두는가

`.claude\skills\karpathy-guidelines\` 폴더를 통째로 자기 프로젝트의 `.claude\skills\` 아래에 복사합니다. 학습 폴더(`study\`)와 포트폴리오 프로젝트 폴더 어느 쪽에 두어도 됩니다. 폴더 이름이 곧 스킬 이름이라 `/karpathy-guidelines`로 부를 수 있고, 코드를 쓰거나 고칠 때 에이전트가 스스로 참고하기도 합니다.

## 언제 쓰는가

- 에이전트에게 코드 작성이나 수정을 맡기기 전에 `/karpathy-guidelines`를 한 번 부릅니다.
- 에이전트가 요청보다 크게 고치거나, 묻지 않고 가정하거나, 검증 없이 「완료」라고 할 때 이 스킬의 네 원칙을 근거로 되돌립니다.
