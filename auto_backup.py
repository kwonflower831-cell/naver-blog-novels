import subprocess
import sys
import datetime
from pathlib import Path

# Set output encoding to UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REPO_DIR = Path(__file__).resolve().parent
LOG_FILE = REPO_DIR / "backup.log"

def log(msg):
    print(msg)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass

def run_git(cmd):
    result = subprocess.run(
        ["git"] + cmd,
        cwd=REPO_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()

def main():
    log("=" * 55)
    log("📚 네이버 블로그 소설 원고 & 비전 스튜디오 GitHub 자동 백업 도구")
    log("=" * 55)
    log(f"📁 작업 경로: {REPO_DIR}")
    log(f"⏰ 실행 시각: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 0. Auto-sync Antigravity_Vision_Studio.html between D:\사용자\storyops\vision_studio and REPO_DIR
    ext_studio_dir = Path(r"D:\사용자\storyops\vision_studio")
    ext_studio_html = ext_studio_dir / "Antigravity_Vision_Studio.html"
    repo_studio_html = REPO_DIR / "Antigravity_Vision_Studio.html"
    try:
        if repo_studio_html.exists() and ext_studio_dir.exists():
            import shutil
            if not ext_studio_html.exists() or repo_studio_html.stat().st_mtime > ext_studio_html.stat().st_mtime:
                shutil.copy2(repo_studio_html, ext_studio_html)
                log(f"🔄 최신 비전 스튜디오 HTML을 {ext_studio_html} 경로로 동기화했습니다.")
            elif ext_studio_html.stat().st_mtime > repo_studio_html.stat().st_mtime:
                shutil.copy2(ext_studio_html, repo_studio_html)
                log(f"🔄 {ext_studio_html} 변경본을 Git 저장소 안으로 가져왔습니다.")
    except Exception:
        pass

    # 1. Check status
    code, out, err = run_git(["status", "--porcelain"])
    if code != 0:
        log(f"❌ Git 상태 확인 실패: {err}")
        return

    if not out:
        log("✨ 변경되거나 새로 작성된 파일이 없습니다.")
        log("🔒 모든 원고와 파일이 이미 최신 상태로 안전하게 백업되어 있습니다.")
        log("=" * 55)
        return

    # Analyze changes
    changed_lines = [line.strip() for line in out.splitlines() if line.strip()]
    log(f"🔍 감지된 변경/추가 파일: {len(changed_lines)}개")
    
    tags = []
    for line in changed_lines:
        status = line[:2].strip()
        fname = line[2:].strip().replace('"', '')
        log(f"   - [{status}] {fname}")
        
        if "Vision_Studio" in fname or "vision_studio" in fname:
            if "비전스튜디오" not in tags:
                tags.append("비전스튜디오")
        elif "novel-yupum" in fname:
            if "유품" not in tags:
                tags.append("유품")
        elif "novel-lasttalk" in fname:
            if "마지막 통화" not in tags:
                tags.append("마지막 통화")
        elif "novel-tumyeong" in fname:
            if "투명" not in tags:
                tags.append("투명")
        elif "content-templates" in fname:
            if "콘텐츠템플릿" not in tags:
                tags.append("콘텐츠템플릿")
        elif "outline" in fname or "ledger" in fname or "guidelines" in fname:
            if "설정·장부" not in tags:
                tags.append("설정·장부")
        elif fname.endswith(".py") or fname.endswith(".bat") or fname.endswith(".vbs"):
            if "스크립트" not in tags:
                tags.append("스크립트")

    tag_str = f" [{', '.join(tags)}]" if tags else ""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_msg = f"자동 백업: {now_str}{tag_str}"

    log(f"\n📦 백업 진행 중...")
    log(f"💬 커밋 메시지: \"{commit_msg}\"")

    # 2. git add .
    code, out, err = run_git(["add", "."])
    if code != 0:
        log(f"❌ 파일 추가(git add) 실패: {err}")
        return

    # 3. git commit
    code, out, err = run_git(["commit", "-m", commit_msg])
    if code != 0:
        log(f"❌ 커밋(git commit) 실패: {err}")
        return
    log("   ✓ 로컬 커밋 완료")

    # 4. git push
    log("   ⬆️ GitHub로 전송 중 (git push origin main)...")
    code, out, err = run_git(["push", "origin", "main"])
    if code != 0:
        log(f"❌ GitHub 전송(git push) 실패:\n{err or out}")
        return

    log("\n" + "=" * 55)
    log("🎉 GitHub 공개 저장소 백업 완료!")
    log(f"🔗 확인 링크: https://github.com/kwonflower831-cell/naver-blog-novels")
    log(f"⏰ 완료 시각: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 55)

if __name__ == "__main__":
    main()
