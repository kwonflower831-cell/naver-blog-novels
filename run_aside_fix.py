import base64
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ch13_path = Path(r"C:\Users\kwonf\.gemini\antigravity\scratch\novels\novel-yupum-text\ch13-published.txt")
raw_bytes = ch13_path.read_bytes()
b64_str = base64.b64encode(raw_bytes).decode("ascii")

js_code = f"""
await attachActiveBrowserTab();
const mf = page.frames()[1];
const raw = Buffer.from('{b64_str}', 'base64').toString('utf8').replace(/\\r\\n/g, '\\n').trim();
const lines = raw.split('\\n');

// Focus first paragraph via synthetic mouse events
await mf.evaluate(() => {{
  const p = document.querySelector('.se-component.se-text .se-text-paragraph');
  const r = p.getBoundingClientRect();
  const opts = {{ bubbles: true, cancelable: true, view: window, clientX: r.left + 20, clientY: r.top + 10 }};
  p.dispatchEvent(new MouseEvent('mousedown', opts));
  p.dispatchEvent(new MouseEvent('mouseup', opts));
  p.dispatchEvent(new MouseEvent('click', opts));
}});
await sleep(200);
await page.keyboard.press('Control+a');
await sleep(200);
await page.keyboard.press('Backspace');
await sleep(300);

for (let i = 0; i < lines.length; i++) {{
  let ln = lines[i].trim();
  if (ln.length > 0) {{
    if (ln.startsWith('1. ')) ln = '1.\\u200b ' + ln.slice(3);
    await page.keyboard.insertText(ln);
  }}
  if (i < lines.length - 1) {{
    await page.keyboard.press('Enter');
  }}
}}
await sleep(500);

// Select all and set font to 나눔명조
await page.keyboard.press('Control+a');
await sleep(300);
await mf.evaluate(() => {{
  const fb = document.querySelector('button[data-name="font-family"], .se-toolbar-item-font-family button');
  fb?.click();
}});
await sleep(500);
await mf.evaluate(() => {{
  const item = [...document.querySelectorAll('button, span, li')].find(e => e.textContent.trim() === '나눔명조');
  item?.click();
}});
await sleep(500);

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

// Select 연재소설 유품
const catSelected = await mf.evaluate(() => {{
  const items = [...document.querySelectorAll('label, button, span, li, a')].filter(e => e.textContent.trim().includes('유품'));
  for (const it of items) {{
    it.click();
  }}
  return items.map(e => e.textContent.trim());
}});
console.log('Category selected:', JSON.stringify(catSelected));
await sleep(600);

// Ensure 전체공개
await mf.evaluate(() => {{
  const pub = document.querySelector('label[for="open_public"], input#open_public');
  pub?.click();
}});
await sleep(500);

// Click final publish button
const confirmed = await mf.evaluate(() => {{
  const cbtn = document.querySelector('button[class*="confirm_btn"]');
  cbtn?.click();
  return !!cbtn;
}});
console.log('Clicked confirm publish:', confirmed);
await sleep(4000);
console.log('Final URL:', page.url());
"""

import shutil
cmd = [
    shutil.which("aside") or "aside",
    "repl",
    "--profile",
    "58101a3d-4173-46fe-a8e0-2cd595eeaabb",
    js_code
]
res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
print("EXIT:", res.returncode)
