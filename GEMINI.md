# 소설 연재 워크스페이스 규칙

- 소설을 쓰거나 수정하기 전에 반드시 이 폴더의 [novel-writing-guidelines.md](./novel-writing-guidelines.md)를 읽고 서식, 문장, 육하원칙, 오감, 수위, 10절 점검표, 12절 기술 점검을 따른다.
- **《유품》** 작업 시: [novel-yupum-outline.md](./novel-yupum-outline.md)와 [novel-yupum-ledger.md](./novel-yupum-ledger.md)(사실 장부 및 쓴 뒤 질문 5개)를 먼저 읽고, 원고는 `novel-yupum-text/` 폴더에 저장한다.
- **《마지막 통화》** 작업 시: [novel-lasttalk-outline.md](./novel-lasttalk-outline.md)를 먼저 읽고, 원고는 `novel-lasttalk-text/` 폴더에 저장한다.
- **《투명》** (1~15장 완결): [novel-tumyeong-outline.md](./novel-tumyeong-outline.md) 참고.
- 서식 요약:
  - 대사: `" "`
  - 주인공 속말/생각: `' '`
  - 문자/메모/표지판/화면 글자: `[ ]`
  - 장면 전환: `◇`
  - 첫 줄 허구 안내: `※ 이 소설은 허구입니다. 등장하는 인물, 단체, 사건은 실제와 관련이 없습니다.`
  - 끝 줄: `(N장에 계속)` 또는 `(끝)`
- 자체 점검 원칙: 초안을 사용자에게 보여 주기 전에 코드 점검 + 사실 장부 5개 질문 + 1·2차 문장 검토를 에이전트가 먼저 끝내고, 사용자에게 일상적인 교정을 다시 시키지 않는다.
- 자동 검증 도구 (`novel_checker.py`):
  - 실행: `python novel_checker.py <장번호 또는 파일경로> [--novel yupum|lasttalk] [--fix] [--promote]`
  - 예시: `python novel_checker.py 9` (ch9-draft.txt 및 사실 장부 자동 점검)
  - 검증 완료 후 게시본 확정 승급: `python novel_checker.py 9 --promote` (ch9-published.txt 자동 생성)
