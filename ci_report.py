#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""전체 소설 원고 일괄 검증 및 GitHub Actions 요약 리포트 생성기."""

import glob
import os
import re
import sys
from pathlib import Path

from novel_checker import NovelChecker

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def natural_key(path: str):
    name = Path(path).name
    m = re.search(r"ch(\d+)-", name)
    ch = int(m.group(1)) if m else 999
    kind = 0 if name.endswith("-published.txt") else 1
    return (ch, kind, name)


def main() -> int:
    base_dir = Path(__file__).resolve().parent
    groups = [
        ("《유품》", "yupum", "novel-yupum-text"),
        ("《마지막 통화》", "lasttalk", "novel-lasttalk-text"),
    ]

    lines = [
        "# 📚 소설 원고 일괄 점검 리포트",
        "",
        "| 작품 | 파일 | 글자 수(공백 포함) | 오류 | 주의 | 상태 |",
        "|---|---|---:|---:|---:|---|",
    ]

    total = 0
    failed = []

    for title, slug, folder in groups:
        drafts = glob.glob(str(base_dir / folder / "ch*-draft.txt"))
        published = glob.glob(str(base_dir / folder / "ch*-published.txt"))
        files = sorted(drafts + published, key=natural_key)
        ledger = str(base_dir / f"novel-{slug}-ledger.md")

        for path in files:
            total += 1
            checker = NovelChecker(path, ledger if os.path.exists(ledger) else None)
            checker.run_all()
            chars = len(checker.raw_text)
            err_n = len(checker.errors)
            warn_n = len(checker.warnings)
            status = "✅ 통과" if err_n == 0 else "❌ 오류"
            rel = Path(path).relative_to(base_dir).as_posix()
            lines.append(f"| {title} | `{rel}` | {chars:,}자 | {err_n} | {warn_n} | {status} |")
            if err_n > 0:
                failed.append((rel, checker.errors))

    lines.extend(["", f"**총 {total}개 원고 검증 완료** · 실패 **{len(failed)}건**"])

    if failed:
        lines.append("")
        lines.append("## ❌ 필수 오류 상세")
        for rel, errs in failed:
            lines.append(f"- `{rel}`")
            for e in errs:
                lines.append(f"  - {e}")

    report = "\n".join(lines) + "\n"
    print(report)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(report)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
