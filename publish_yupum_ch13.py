import os
import re
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

novel_file = Path(r"C:\Users\kwonf\.gemini\antigravity\scratch\novels\novel-yupum-text\ch13-published.txt")
text = novel_file.read_text(encoding="utf-8").strip()
lines = text.splitlines()

# Extract title
title = "《유품》 13장. 다른 종이"
for line in lines[:5]:
    if line.strip().startswith("《유품》"):
        title = line.strip()
        break

# Extract body paragraphs
body_lines = []
skip_first = True
for line in lines:
    s = line.strip()
    if skip_first and (s.startswith("※") or s.startswith("《유품》") or not s):
        continue
    skip_first = False
    if s:
        body_lines.append(s)

tags = ["유품", "연재소설", "스릴러", "소설", "유품정리"]

PROFILE_DIR = r"C:\Users\kwonf\.gemini\antigravity\scratch\chrome-naver-profile"

print(f"Title: {title}")
print(f"Paragraphs count: {len(body_lines)}")
print(f"Tags: {tags}")

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=PROFILE_DIR,
        channel="chrome",
        headless=False,
        args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
        no_viewport=True,
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    
    # Go to blog write
    page.goto("https://blog.naver.com/kwonflower58?Redirect=Write&", wait_until="domcontentloaded")
    time.sleep(3)
    
    # Check if login redirect happened
    if "nidlogin" in page.url or "nid.naver.com" in page.url:
        print("LOGIN_REQUIRED: Please complete login in the opened Chrome window. Waiting up to 180s...")
        for sec in range(180):
            if "nidlogin" not in page.url and "nid.naver.com" not in page.url:
                print("LOGIN_DETECTED! Proceeding to editor...")
                time.sleep(3)
                break
            time.sleep(1)
        if "nidlogin" in page.url:
            print("Login timed out.")
            ctx.close()
            sys.exit(1)
            
    # Find editor frame
    print("Finding editor frame...")
    frame = None
    for _ in range(30):
        for f in page.frames:
            try:
                if f.locator(".se-documentTitle").count() > 0 or f.locator(".se-component.se-text .se-text-paragraph").count() > 0:
                    frame = f
                    break
            except Exception:
                pass
        if frame:
            break
        time.sleep(1)
        
    if not frame:
        print("Editor frame not found!")
        ctx.close()
        sys.exit(1)
        
    # Dismiss popups
    for sel in [".se-popup-button-cancel", ".se-help-panel-close-button"]:
        try:
            b = frame.locator(sel)
            if b.count() > 0 and b.first.is_visible():
                b.first.click()
                time.sleep(0.5)
        except Exception:
            pass
            
    # Input title
    print("Entering title...")
    title_box = frame.locator(".se-documentTitle [contenteditable='true'], .se-documentTitle input").first
    title_box.click()
    time.sleep(0.3)
    page.keyboard.insert_text(title)
    time.sleep(0.5)
    
    # Input body
    print("Entering body paragraphs...")
    body_box = frame.locator(".se-component.se-text .se-text-paragraph").first
    body_box.click()
    time.sleep(0.3)
    
    for i, para in enumerate(body_lines):
        page.keyboard.insert_text(para)
        time.sleep(0.02)
        if i < len(body_lines) - 1:
            page.keyboard.press("Enter")
            page.keyboard.press("Enter")
            time.sleep(0.02)
            
    time.sleep(1)
    
    # Click publish button to open modal
    print("Opening publish panel...")
    frame.get_by_role("button", name="발행").first.click()
    time.sleep(2)
    
    # Tags
    print("Entering tags...")
    try:
        tag_box = frame.get_by_role("combobox", name=re.compile(r"^태그"))
        if tag_box.count() > 0:
            tag_box.first.click()
        else:
            frame.locator('input[placeholder*="태그"], [aria-label*="태그"]').first.click()
        for tg in tags:
            page.keyboard.insert_text(tg)
            page.keyboard.press("Enter")
            time.sleep(0.1)
    except Exception as e:
        print("Tag error:", e)
        
    # Final publish
    print("Clicking final publish...")
    frame.get_by_role("button", name="발행").last.click()
    time.sleep(5)
    print("SUCCESSFULLY_PUBLISHED")
    ctx.close()
