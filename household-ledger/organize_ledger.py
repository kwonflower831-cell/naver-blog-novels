#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""가계부 CSV 자동 분류 및 월별/항목별 요약 스크립트 (외부 패키지 불필요)."""

import argparse
import csv
import os
import re
import sys
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_RULES = [
    ("주유", "유류·차량비"),
    ("SK에너지", "유류·차량비"),
    ("GS칼텍스", "유류·차량비"),
    ("S-OIL", "유류·차량비"),
    ("정비", "유류·차량비"),
    ("하이패스", "유류·차량비"),
    ("마트", "식비·생활"),
    ("편의점", "식비·생활"),
    ("CU", "식비·생활"),
    ("GS25", "식비·생활"),
    ("식당", "식비·생활"),
    ("김밥", "식비·생활"),
    ("스타벅스", "식비·카페"),
    ("커피", "식비·카페"),
    ("통신", "고정비·공과금"),
    ("SKT", "고정비·공과금"),
    ("KT", "고정비·공과금"),
    ("관리비", "고정비·공과금"),
    ("보험", "고정비·공과금"),
    ("월세", "고정비·공과금"),
    ("병원", "의료·건강"),
    ("약국", "의료·건강"),
    ("정산", "수입·정산"),
    ("급여", "수입·정산"),
    ("입금", "수입·정산"),
]


def read_csv_auto(path: str):
    """UTF-8 또는 EUC-KR(CP949) 인코딩을 자동 판별해 CSV 행을 읽는다."""
    for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        try:
            with open(path, "r", encoding=enc, newline="") as f:
                return list(csv.reader(f))
        except UnicodeDecodeError:
            continue
    raise ValueError(f"지원하지 않는 파일 인코딩입니다: {path}")


def parse_amount(raw: str) -> int:
    """숫자 문자열에서 정수 금액을 추출한다."""
    cleaned = re.sub(r"[^0-9.-]", "", raw or "")
    return int(float(cleaned)) if cleaned else 0


def classify(desc: str, tx_type: str) -> str:
    """내용의 키워드를 기준으로 카테고리를 자동 분류한다."""
    lower = desc.lower()
    for kw, cat in DEFAULT_RULES:
        if kw.lower() in lower:
            return cat
    return "기타 수입" if tx_type == "수입" else "기타 지출"


def organize(input_path: str, output_path: str) -> None:
    """입력 CSV를 읽어 자동 분류한 뒤 정리본 CSV와 요약을 출력한다."""
    rows = read_csv_auto(input_path)
    if len(rows) < 2:
        print("처리할 거래 내역이 없습니다.")
        return

    headers = [h.strip().lower() for h in rows[0]]

    def find_col(candidates, default=None):
        for idx, h in enumerate(headers):
            if any(c in h for c in candidates):
                return idx
        return default

    date_i = find_col(["날짜", "일자", "일시", "date"], 0)
    desc_i = find_col(["내용", "적요", "가맹점", "항목", "desc"], 1)
    type_i = find_col(["구분", "유형", "type"])
    amt_i = find_col(["금액", "결제금액", "amount"], 2)
    in_i = find_col(["입금", "수입"])
    out_i = find_col(["출금", "지출"])

    organized = []
    monthly = defaultdict(lambda: {"수입": 0, "지출": 0})
    by_cat = defaultdict(int)

    for row in rows[1:]:
        if len(row) < 2:
            continue
        date_str = row[date_i].strip().replace(".", "-").replace("/", "-")[:10]
        desc = row[desc_i].strip() or "내역 없음"

        if in_i is not None or out_i is not None:
            in_amt = abs(parse_amount(row[in_i])) if in_i is not None else 0
            out_amt = abs(parse_amount(row[out_i])) if out_i is not None else 0
            if in_amt > 0:
                tx_type, amount = "수입", in_amt
            else:
                tx_type, amount = "지출", out_amt
        else:
            raw_amt = parse_amount(row[amt_i])
            if type_i is not None and "수입" in row[type_i]:
                tx_type = "수입"
            elif type_i is None and raw_amt > 0 and any(k in desc for k in ("입금", "정산", "급여")):
                tx_type = "수입"
            else:
                tx_type = "지출"
            amount = abs(raw_amt)

        if amount == 0:
            continue

        cat = classify(desc, tx_type)
        organized.append([date_str, tx_type, desc, cat, amount])
        month = date_str[:7]
        monthly[month][tx_type] += amount
        if tx_type == "지출":
            by_cat[cat] += amount

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["날짜", "구분", "내용", "카테고리", "금액"])
        writer.writerows(organized)

    print(f"[완료] 총 {len(organized)}건 정리 -> {os.path.abspath(output_path)}")
    print("\n[월별 요약]")
    for m in sorted(monthly):
        inc = monthly[m]["수입"]
        exp = monthly[m]["지출"]
        print(f"  {m}: 수입 {inc:,}원 | 지출 {exp:,}원 | 순수익 {inc - exp:+,}원")

    print("\n[카테고리별 지출]")
    for cat, amt in sorted(by_cat.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {amt:,}원")


def main():
    parser = argparse.ArgumentParser(description="가계부 CSV 자동 정리 스크립트")
    parser.add_argument("input", help="원본 거래내역 CSV 경로")
    parser.add_argument("-o", "--output", default="organized_ledger.csv", help="출력 CSV 경로")
    args = parser.parse_args()
    organize(args.input, args.output)


if __name__ == "__main__":
    main()
