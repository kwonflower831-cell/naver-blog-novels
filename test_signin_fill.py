import time
from playwright.sync_api import sync_playwright

PROFILE_DIR = r"C:\Users\kwonf\.gemini\antigravity\scratch\chrome-naver-profile"

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(user_data_dir=PROFILE_DIR, channel="chrome", headless=True)
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://nid.naver.com/nidlogin.login?url=https%3A%2F%2Fblog.naver.com%2Fkwonflower58%3FRedirect%3DWrite%26", wait_until="domcontentloaded")
    time.sleep(1)

    page.locator("#id").fill("kwonflower58")
    time.sleep(0.3)
    page.locator("#pw").fill("kwon7604@@")
    time.sleep(0.3)

    # Click Sign in button
    btn = page.locator("#loginBtn_column, #loginBtn_row, button.btn_done").last
    btn.click()
    print("Clicked Sign in!")
    time.sleep(4)
    print("URL after Sign in:", page.url)
    page.screenshot(path="after_signin_fill.png")
    cookies = ctx.cookies()
    has_auth = any(c.get("name") in ("NID_AUT", "NID_SES") for c in cookies)
    print("Has auth cookies:", has_auth)
    ctx.close()
