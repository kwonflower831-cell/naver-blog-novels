import base64
import shutil
import subprocess
import sys
import urllib.request
import re
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 1. Verify 224481551902 (Yupum Ch13)
url13 = "https://blog.naver.com/PostView.naver?blogId=kwonflower58&logNo=224481551902"
req13 = urllib.request.Request(url13, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req13) as resp:
    html13 = resp.read().decode("utf-8")
paras13 = re.findall(r'<p class="se-text-paragraph[^>]*>([\s\S]*?)</p>', html13)
ne13 = [re.sub(r'<[^>]+>', '', p).strip() for p in paras13 if re.sub(r'<[^>]+>', '', p).strip()]
ff13 = len(re.findall(r'se-ff-nanummyeongjo', html13))
print(f"[Verify 224481551902] paragraphs={len(ne13)}, myeongjo={ff13}")
print("  First 3:", ne13[:3])
print("  Last 2:", ne13[-2:])

# 2. Now fix 224481516237 (Chronos Arcana Ch1) via Aside REPL
ch1_path = Path(r"D:\사용자\storyops\novels\chronos_arcana\chapters\ch1-draft.txt")
b64_str = base64.b64encode(ch1_path.read_bytes()).decode("ascii")

js_code = f"""
await attachActiveBrowserTab();
const mf0 = page.frames()[1];
await mf0.evaluate(() => {{
  location.href = 'https://blog.naver.com/kwonflower58/postupdate?logNo=224481516237';
}});
await sleep(6000);

const mf = page.frames()[1];
const raw = Buffer.from('{b64_str}', 'base64').toString('utf8').replace(/\\r\\n/g, '\\n').trim();
const lines = raw.split('\\n');

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

await mf.evaluate(() => {{
  const pb = document.querySelector('button[class*="publish_btn"]');
  pb?.click();
}});
await sleep(1000);

await mf.evaluate(() => {{
  document.querySelector('label[for="open_public"]')?.click();
}});
await sleep(400);

const confirmed = await mf.evaluate(() => {{
  const cbtn = document.querySelector('button[class*="confirm_btn"]');
  cbtn?.click();
  return !!cbtn;
}});
console.log('Chronos Ch1 clicked confirm_btn:', confirmed);
await sleep(4000);
"""

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
