import base64
import shutil
import subprocess
import sys
import time
import urllib.request
import re
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def fix_post_in_aside(log_no: str, txt_path: Path, target_category: str):
    raw_bytes = txt_path.read_bytes()
    b64_str = base64.b64encode(raw_bytes).decode("ascii")

    js_code = f"""
await attachActiveBrowserTab();
const mf0 = page.frames()[1] || page.mainFrame();
await mf0.evaluate(() => {{
  location.href = 'https://blog.naver.com/kwonflower58/postupdate?logNo={log_no}';
}});
await sleep(6000);

let mf = null;
for (let retry = 0; retry < 20; retry++) {{
  for (const f of page.frames()) {{
    if (await f.locator('.se-component.se-text .se-text-paragraph').count() > 0) {{
      mf = f;
      break;
    }}
  }}
  if (mf) break;
  await sleep(1000);
}}
if (!mf) throw new Error('Editor frame not found for ' + '{log_no}');

// Dismiss any popups
await mf.evaluate(() => {{
  for (const sel of ['.se-popup-button-cancel', '.se-help-panel-close-button']) {{
    const b = document.querySelector(sel);
    if (b) b.click();
  }}
}});
await sleep(400);

const raw = Buffer.from('{b64_str}', 'base64').toString('utf8').replace(/\\r\\n/g, '\\n').trim();
const blocks = raw.split('\\n\\n').map(b => b.trim()).filter(Boolean);
const flatParas = [];
for (const b of blocks) {{
  for (const sub of b.split('\\n')) {{
    let s = sub.trim();
    if (s) {{
      if (s.startsWith('1. ')) s = '1.\\u200b ' + s.slice(3);
      flatParas.push(s);
    }}
  }}
}}
console.log('Target paragraphs count:', flatParas.length);

// Focus first paragraph via synthetic mouse events
await mf.evaluate(() => {{
  const p = document.querySelector('.se-component.se-text .se-text-paragraph');
  if (p) {{
    const r = p.getBoundingClientRect();
    const opts = {{ bubbles: true, cancelable: true, view: window, clientX: r.left + 20, clientY: r.top + 10 }};
    p.dispatchEvent(new MouseEvent('mousedown', opts));
    p.dispatchEvent(new MouseEvent('mouseup', opts));
    p.dispatchEvent(new MouseEvent('click', opts));
  }}
}});
await sleep(300);
await page.keyboard.press('Control+a');
await sleep(300);
await page.keyboard.press('Backspace');
await sleep(500);

for (let i = 0; i < flatParas.length; i++) {{
  await page.keyboard.insertText(flatParas[i]);
  await sleep(110);
  if (i < flatParas.length - 1) {{
    await page.keyboard.press('Enter');
    await sleep(90);
    await page.keyboard.press('Enter');
    await sleep(90);
  }}
}}
await sleep(800);

// Verify DOM paragraph count
const domParas = await mf.evaluate(() => {{
  return [...document.querySelectorAll('.se-component.se-text .se-text-paragraph')]
    .map(e => e.textContent.replace(/\\u200b/g, '').trim())
    .filter(Boolean);
}});
console.log('DOM non-empty paragraphs:', domParas.length, 'Expected:', flatParas.length);

// Select all and set font to 나눔명조
await page.keyboard.press('Control+a');
await sleep(300);
await mf.evaluate(() => {{
  const fb = document.querySelector('button[data-name="font-family"], .se-toolbar-item-font-family button');
  fb?.click();
}});
await sleep(600);
await mf.evaluate(() => {{
  const item = [...document.querySelectorAll('button, span, li')].find(e => e.textContent.trim() === '나눔명조');
  item?.click();
}});
await sleep(600);

// Open publish panel
await mf.evaluate(() => {{
  const pb = document.querySelector('button[class*="publish_btn"]');
  pb?.click();
}});
await sleep(1000);

// Open category dropdown
await mf.evaluate(() => {{
  const cb = document.querySelector('button[class*="selectbox_button"]');
  cb?.click();
}});
await sleep(800);

// Select target category
const catRes = await mf.evaluate((targetCat) => {{
  const sp = [...document.querySelectorAll('span[class*="option__"]')].find(e => e.textContent.trim() === targetCat);
  sp?.click();
  return sp ? sp.textContent.trim() : null;
}}, '{target_category}');
console.log('Selected category:', catRes);
await sleep(600);

// Ensure 전체공개
await mf.evaluate(() => {{
  document.querySelector('label[for="open_public"]')?.click();
}});
await sleep(400);

// Click final publish button
const confirmed = await mf.evaluate(() => {{
  const cbtn = document.querySelector('button[class*="confirm_btn"]');
  cbtn?.click();
  return !!cbtn;
}});
console.log('Clicked confirm_btn:', confirmed);
await sleep(5000);
"""

    cmd = [
        shutil.which("aside") or "aside",
        "repl",
        "--profile",
        "58101a3d-4173-46fe-a8e0-2cd595eeaabb",
        js_code
    ]
    print(f"=== Running Aside fix for {log_no} ({target_category}) ===", flush=True)
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    print("STDOUT:", res.stdout, flush=True)
    if res.stderr:
        print("STDERR:", res.stderr, flush=True)
    return res.returncode == 0

if __name__ == "__main__":
    p13 = Path(r"C:\Users\kwonf\.gemini\antigravity\scratch\novels\novel-yupum-text\ch13-published.txt")
    fix_post_in_aside("224481551902", p13, "연재소설 유품")
