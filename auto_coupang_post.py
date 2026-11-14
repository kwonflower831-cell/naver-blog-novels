import re
import sys
import time
import subprocess
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def get_clipboard_text():
    try:
        res = subprocess.run(['powershell', '-command', 'Get-Clipboard'], capture_output=True, text=True, encoding='utf-8')
        return res.stdout.strip()
    except Exception:
        return ""

def set_clipboard_text(text):
    ps = subprocess.Popen(['powershell', '-command', '$input | Set-Clipboard'], stdin=subprocess.PIPE, text=True, encoding='utf-8')
    ps.communicate(input=text)

def main():
    print("=" * 60, flush=True)
    print("🔍 [쿠팡 파트너스 링크 원클릭 자동 감지기 가동 중]", flush=True)
    print("화면의 파트너스 창에서 [URL 복사] 버튼을 딱 한 번만 클릭해 주세요!", flush=True)
    print("=" * 60, flush=True)

    detected_url = ""
    for sec in range(120):
        clip = get_clipboard_text()
        if "link.coupang.com" in clip or "coupang.com" in clip:
            detected_url = clip
            print(f"\n🎉 쿠팡 링크 자동 감지 성공! -> {detected_url}", flush=True)
            break
        time.sleep(1)

    if not detected_url:
        detected_url = "https://link.coupang.com/ (쿠팡 추천 링크)"
        print("\n시간 초과로 기본 템플릿으로 생성합니다.", flush=True)

    post_title = "자취생 & 주부 필수! 쿠팡에서 무조건 쟁여두는 가성비 생필품 BEST 3 (솔직 가격비교)"
    
    post_body = f"""안녕하세요! 

매달 나가는 고정 생활비, 물가가 너무 올라서 장보기가 무서울 정도입니다.
하지만 쿠팡 로켓배송과 정기배송을 똑똑하게 활용하면 오프라인 대형마트보다 **매달 최소 5~10만 원 이상의 생활비**를 아낄 수 있다는 사실, 알고 계셨나요?

오늘은 수많은 후기와 판매량으로 검증된, **장바구니에 무조건 쟁여두는 가성비 생필품 꿀템 3선**을 꼼꼼하게 비교해 드립니다!

---

### 💧 1. 생수 부동의 1위: 탐사수 2L x 6병 / 500ml
* **추천 이유**: 마트에서 무겁게 들고 올 필요 없이 현관 앞까지 무료 로켓배송!
* **가성비 비교**: 편의점 대비 병당 1/3 가격 수준으로 자취생과 1인 가구 필수템입니다.

👉 **[추천 상품 바로가기]**: {detected_url}
*(※ 실시간 특가 및 로켓와우 혜택 적용 가능)*

---

### 🧻 2. 도톰한 3겹 롤화장지 (30롤 대용량)
* **추천 이유**: 먼지 날림이 적고 3겹 데코 엠보싱으로 흡수력이 뛰어납니다.
* **꿀팁**: 10m당 단가를 비교했을 때 브랜드 제품 중 가장 경제적입니다.

---

### 🔒 3. 자취방 & 원룸 필수: 무타공 현관문 이중 안전고리
* **추천 이유**: 못이나 나사 없이 문틀에 10초 만에 설치 가능한 철벽 보안템!
* 혼자 사는 원룸이나 여성 자취생들의 불안을 덜어주는 최고의 안전 지킴이입니다.

---

💡 **현명한 소비 팁**
생필품은 다 떨어졌을 때 급하게 편의점에서 사면 비용이 2~3배 듭니다. 자주 쓰는 소모품은 특가 쟁여템으로 미리 구비해 두시는 것을 추천합니다!

---

*이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.*
"""

    set_clipboard_text(post_body)
    print("✔ 포스팅 본문이 클립보드에 자동으로 생성·복사되었습니다!", flush=True)

    # 글쓰기 페이지 열기
    subprocess.run(['powershell', '-command', 'Start-Process "https://blog.naver.com/kwonflower58?Redirect=Write&"'])
    print("✔ 네이버 블로그 글쓰기 창이 열렸습니다. 에디터에서 Ctrl+V만 누르시면 완성됩니다!", flush=True)

if __name__ == "__main__":
    main()
