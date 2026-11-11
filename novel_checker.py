#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
소설 집필 및 연재 자체 검증 자동화 도구 (Novel Draft Quality & Continuity Checker)
- 규칙 기준: novel-writing-guidelines.md (서식, 문장, 오류 유형 10절, 기술 점검 12절)
- 사실 장부 기준: novel-yupum-ledger.md (5대 질문, 시간표, 인물 지식, 물건 위치)
"""

import sys
import os
import re
import argparse
from typing import List, Dict, Tuple, Any

# Windows 콘솔 utf-8 출력 설정
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# ANSI 색상 코드 (터미널 출력용)
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

# 허구 안내 필수 문구
DISCLAIMER_TEXT = "※ 이 소설은 허구입니다. 등장하는 인물, 단체, 사건은 실제와 관련이 없습니다."

# 한글 시각 표현 패턴
KOREAN_TIME_WORDS = [
    (r"(오전|오후|새벽|저녁|밤)?\s*(한\s*시)", "1시"),
    (r"(오전|오후|새벽|저녁|밤)?\s*(두\s*시)", "2시"),
    (r"(오전|오후|새벽|저녁|밤)?\s*(세\s*시)", "3시"),
    (r"(오전|오후|새벽|저녁|밤)?\s*(네\s*시)", "4시"),
    (r"(오전|오후|새벽|저녁|밤)?\s*(다섯\s*시)", "5시"),
    (r"(오전|오후|새벽|저녁|밤)?\s*(여섯\s*시)", "6시"),
    (r"(오전|오후|새벽|저녁|밤)?\s*(일곱\s*시)", "7시"),
    (r"(오전|오후|새벽|저녁|밤)?\s*(여덟\s*시)", "8시"),
    (r"(오전|오후|새벽|저녁|밤)?\s*(아홉\s*시)", "9시"),
    (r"(오전|오후|새벽|저녁|밤)?\s*(열\s*시)", "10시"),
    (r"(오전|오후|새벽|저녁|밤)?\s*(열한\s*시)", "11시"),
    (r"(오전|오후|새벽|저녁|밤)?\s*(열두\s*시)", "12시"),
]

# 감정 직접 설명 표현 (Rule 12 #8)
EMOTION_EXPOSITION_PATTERNS = [
    r"이상했다",
    r"설명할\s*수\s*없었다",
    r"기분이\s*들었다",
    r"생각이\s*들었다",
    r"느낌이\s*들었다",
    r"불길한\s*예감이",
]

# 시간 기준어 (Rule 10-2 #1)
TIME_WORDS = [
    "어제", "어젯밤", "오늘", "사흘", "나흘", "이틀 전", "내일", "새벽", "방금", "지난주", "그저께"
]

class NovelChecker:
    def __init__(self, filepath: str, ledger_path: str = None):
        self.filepath = os.path.abspath(filepath)
        self.ledger_path = os.path.abspath(ledger_path) if ledger_path else None
        
        with open(self.filepath, "r", encoding="utf-8") as f:
            self.raw_text = f.read()
            
        self.lines = self.raw_text.splitlines()
        self.non_empty_lines = [(idx + 1, line) for idx, line in enumerate(self.lines) if line.strip()]
        
        self.passes = []
        self.warnings = []
        self.errors = []
        
    def check_header_and_footer(self):
        """1. 머리말 허구 문구 및 끝 줄 형식 검사"""
        if not self.non_empty_lines:
            self.errors.append("원고가 비어 있습니다.")
            return

        # 1장 첫 줄 머리글 링크 예외 허용 확인
        first_line_num, first_line = self.non_empty_lines[0]
        if DISCLAIMER_TEXT in first_line or "▶ 연재 안내와 목차 보기" in first_line:
            self.passes.append(f"머리말 허구 안내 확인 (줄 {first_line_num})")
        else:
            self.errors.append(f"첫 줄에 허구 안내 문구가 없습니다: '{first_line[:30]}...'")

        last_line_num, last_line = self.non_empty_lines[-1]
        footer_pattern = r"^\((\d+장에\s*계속|끝)\)$"
        if re.search(footer_pattern, last_line.strip()):
            self.passes.append(f"끝 줄 형식 확인: '{last_line.strip()}' (줄 {last_line_num})")
        else:
            self.errors.append(f"마지막 줄이 '(N장에 계속)' 또는 '(끝)' 형식이 아닙니다: '{last_line}' (줄 {last_line_num})")

    def check_length(self):
        """2. 글자 수 검사 (권장: 2,200 ~ 3,500자)"""
        char_count_with_spaces = len(self.raw_text)
        char_count_no_spaces = len(re.sub(r"\s+", "", self.raw_text))
        
        status = f"글자 수: 공백 포함 {char_count_with_spaces:,}자 / 공백 제외 {char_count_no_spaces:,}자"
        if 2000 <= char_count_with_spaces <= 4500:
            self.passes.append(f"{status} (권장 분량 충족)")
        elif char_count_with_spaces < 2000:
            self.warnings.append(f"{status} (권장 2,200자보다 다소 짧음)")
        else:
            self.warnings.append(f"{status} (권장 3,500자보다 다소 김)")

    def check_quote_pairs(self):
        """3. 따옴표 및 괄호 짝 닫힘 검사 (" ", ' ', [ ])"""
        double_quotes = self.raw_text.count('"')
        single_monologue = len(re.findall(r"'(.*?)'", self.raw_text))
        single_quotes_total = self.raw_text.count("'")
        
        open_brackets = self.raw_text.count('[')
        close_brackets = self.raw_text.count(']')

        if double_quotes % 2 == 0:
            self.passes.append(f"큰따옴표(\"\") 짝 일치 (대사 쌍: {double_quotes // 2}개)")
        else:
            self.errors.append(f"큰따옴표(\"\") 개수가 홀수입니다 ({double_quotes}개). 닫히지 않은 대사가 있습니다.")

        if single_quotes_total % 2 == 0:
            self.passes.append(f"작은따옴표('') 짝 일치 (속말/생각: {single_quotes_total // 2}개)")
        else:
            self.warnings.append(f"작은따옴표('') 개수가 홀수입니다 ({single_quotes_total}개). 줄임말/속말 확인 필요.")

        if open_brackets == close_brackets:
            self.passes.append(f"대괄호([]) 짝 일치 (문자/메모/서류: {open_brackets}개)")
        else:
            self.errors.append(f"대괄호([]) 짝 불일치: 열린 괄호 {open_brackets}개 != 닫힌 괄호 {close_brackets}개")

    def check_spacing_and_paragraphs(self):
        """4. 띄어쓰기 및 빈 줄 규칙 검사"""
        double_spaces = []
        for idx, line in enumerate(self.lines, 1):
            if "  " in line:
                double_spaces.append(idx)
        
        if double_spaces:
            self.warnings.append(f"연속 공백(스페이스 2개 이상) 발견: {len(double_spaces)}개 줄 (예: 줄 {double_spaces[:5]})")
        else:
            self.passes.append("연속 공백 없음")

        # 빈 줄 2개 이상 연속 여부
        consecutive_blanks = re.findall(r"\n\s*\n\s*\n", self.raw_text)
        if consecutive_blanks:
            self.warnings.append(f"문단 사이에 빈 줄이 2개 이상 연속된 구간이 {len(consecutive_blanks)}곳 있습니다.")
        else:
            self.passes.append("문단 간 빈 줄 규칙 적합 (빈 줄 1개 유지)")

    def check_time_expressions(self):
        """5. 시각 및 숫자 표기 통일 검사 (Rule 3, 10-1 #12)"""
        korean_times_found = []
        for pattern, replacement in KOREAN_TIME_WORDS:
            for idx, line in enumerate(self.lines, 1):
                # 대사 내 구어체 제외하고 지문에서 검출
                clean_line = re.sub(r'"[^"]*"', '', line)
                matches = re.finditer(pattern, clean_line)
                for m in matches:
                    korean_times_found.append((idx, m.group(0), replacement))
        
        if korean_times_found:
            details = [f"줄 {idx}: '{orig}' -> '{repl}' 권장" for idx, orig, repl in korean_times_found[:5]]
            self.warnings.append(f"한글 시각 표기 발견 ({len(korean_times_found)}건, 숫자 표기 권장): {', '.join(details)}")
        else:
            self.passes.append("시각 표기 숫자 통일 준수 (예: 오후 7시 8분)")

    def check_subject_repetitions(self):
        """6. 인물 이름+'은/는/이/가' 과다 반복 및 연속 문장 검사 (Rule 10-1 #14)"""
        characters = ["해진", "재식", "도훈", "유라", "세창", "만복", "정숙", "순자", "해린"]
        
        for name in characters:
            # 지문에서의 사용 빈도
            pattern = rf"{name}(은|는|이|가)"
            matches = list(re.finditer(pattern, self.raw_text))
            count = len(matches)
            
            if count > 20:
                self.warnings.append(f"주어 과다 사용 경고: '{name}(은/는/이/가)' 총 {count}회 등장 (지문 내 15~20회 이하 권장)")
            elif count > 0:
                self.passes.append(f"주어 빈도 적정: '{name}' {count}회")

        # 3연속 동일 주어 시작 검사
        prev_name = None
        consecutive_count = 0
        consecutive_alerts = []
        
        for idx, line in self.non_empty_lines:
            stripped = line.strip()
            # 대사, 장면전환, 특수문구 제외
            if stripped.startswith('"') or stripped.startswith("'") or stripped.startswith("[") or stripped.startswith("※") or stripped == "◇":
                prev_name = None
                consecutive_count = 0
                continue
                
            matched_name = None
            for name in characters:
                if stripped.startswith(name):
                    matched_name = name
                    break
                    
            if matched_name and matched_name == prev_name:
                consecutive_count += 1
                if consecutive_count >= 3:
                    consecutive_alerts.append((idx, matched_name))
            else:
                prev_name = matched_name
                consecutive_count = 1 if matched_name else 0

        if consecutive_alerts:
            self.warnings.append(f"동일 주어로 연속 3문단 이상 시작: {consecutive_alerts}")
        else:
            self.passes.append("동일 주어 연속 3회 이상 시작 없음")

    def check_emotion_exposition(self):
        """7. 감정 직접 설명 서술어 검사 (Rule 12 #8: 3회 초과 시 행동으로 전환 권장)"""
        found_emotions = []
        for pattern in EMOTION_EXPOSITION_PATTERNS:
            for idx, line in enumerate(self.lines, 1):
                clean_line = re.sub(r'"[^"]*"', '', line) # 대사 제외
                if re.search(pattern, clean_line):
                    found_emotions.append((idx, pattern))
        
        if len(found_emotions) > 3:
            self.warnings.append(f"감정 직접 설명 서술어 {len(found_emotions)}회 발견 (행동/신체 반응 묘사 권장): {found_emotions[:4]}")
        else:
            self.passes.append(f"감정 직접 설명 절제 (발견 {len(found_emotions)}건, 3회 이하 적정)")

    def extract_time_anchors(self):
        """8. 시간 기준어 추출 (날짜/시간 정합성 점검용)"""
        found_times = []
        for word in TIME_WORDS:
            for idx, line in self.non_empty_lines:
                clean_line = re.sub(r'"[^"]*"', '', line)
                if word in clean_line:
                    found_times.append((idx, word, line.strip()[:40]))
        return found_times

    def load_ledger_info(self) -> Dict[str, Any]:
        """사실 장부 로드 및 파싱"""
        if not self.ledger_path or not os.path.exists(self.ledger_path):
            return {}
            
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            ledger_text = f.read()

        info = {
            "characters_knowledge": [],
            "item_locations": [],
            "open_questions": [],
            "timeline": []
        }
        
        current_section = None
        for line in ledger_text.splitlines():
            line_str = line.strip()
            if line_str.startswith("## 시간표"):
                current_section = "timeline"
            elif line_str.startswith("## 인물이 아는 것"):
                current_section = "characters_knowledge"
            elif line_str.startswith("## 물건 위치"):
                current_section = "item_locations"
            elif line_str.startswith("## 열린 질문"):
                current_section = "open_questions"
            elif line_str.startswith("##"):
                current_section = None
            elif current_section and line_str.startswith("-"):
                info[current_section].append(line_str.lstrip("- ").strip())
                
        return info

    def generate_five_questions_worksheet(self) -> List[str]:
        """사실 장부 5대 질문 점검 워크시트 생성"""
        worksheet = [
            "============================================================",
            f"{BOLD}《유품》 사실 장부 5대 질문 점검표 (Continuity Checklist){RESET}",
            "============================================================",
            "1. [행동 원인] 인물이 지금 이 순간 그렇게 행동하는 명확한 이유가 본문에 있는가?",
            "   -> 점검: 각 인물(해진, 석만복, 오세창, 마재식, 강도훈)의 선택과 행동 동기",
            "2. [정보 출처] 인물이 알고 있는 정보를 어떻게 알았는지 경로가 확실한가?",
            "   -> 점검: 본 것, 들은 곳, 전달받은 서류/가계부의 출처와 정황",
            "3. [상식적 대응] 상식적인 사람이라면 취했을 필수 조치가 누락되지 않았는가?",
            "   -> 점검: 112 긴급 신고, 119 구급 이송, 현장 보존, 촬영 및 녹취",
            "4. [시간/이동] 시간 순서와 장소 간 이동 시간이 분 단위로 모순 없이 맞아떨어지는가?",
            "   -> 점검: 사건 발생 시각, 출동 시간, 차량 이동 시각의 연속성",
            "5. [장부 정합성] 앞 장에서 확정된 사실 장부의 물건 위치 및 인물 지식과 모순이 없는가?",
            "   -> 점검: 사물함 소지품, 지문 채취 시점, 쪽지와 가계부의 이동 경로"
        ]
        return worksheet

    def run_all(self):
        """전체 검사 실행"""
        self.check_header_and_footer()
        self.check_length()
        self.check_quote_pairs()
        self.check_spacing_and_paragraphs()
        self.check_time_expressions()
        self.check_subject_repetitions()
        self.check_emotion_exposition()

    def print_report(self):
        """검사 결과 리포트 출력"""
        print("\n" + "="*60)
        print(f"{BOLD}{CYAN}[점검] 소설 원고 자체 검증 리포트 (Novel Checker){RESET}")
        print(f"파일: {self.filepath}")
        print("="*60)

        # 1. 성공 항목 (PASS)
        print(f"\n{GREEN}{BOLD}[통과 항목 (PASS: {len(self.passes)})]{RESET}")
        for p in self.passes:
            print(f"  {GREEN}[O]{RESET} {p}")

        # 2. 주의/권장 항목 (WARN)
        if self.warnings:
            print(f"\n{YELLOW}{BOLD}[주의 및 권장 사항 (WARNING: {len(self.warnings)})]{RESET}")
            for w in self.warnings:
                print(f"  {YELLOW}[!]{RESET} {w}")
        else:
            print(f"\n{GREEN}주의 및 권장 사항 없음 (완벽){RESET}")

        # 3. 오류 항목 (ERROR)
        if self.errors:
            print(f"\n{RED}{BOLD}[필수 수정 항목 (ERROR: {len(self.errors)})]{RESET}")
            for e in self.errors:
                print(f"  {RED}[X]{RESET} {e}")
        else:
            print(f"\n{GREEN}{BOLD}[필수 오류 0건 - 기본 서식 검사 통과]{RESET}")

        # 4. 시간 기준어 추출 현황
        time_anchors = self.extract_time_anchors()
        if time_anchors:
            print(f"\n{BLUE}{BOLD}[본문 내 시간 기준어 (타임라인 대조용: {len(time_anchors)}건)]{RESET}")
            for idx, word, snippet in time_anchors[:8]:
                print(f"  - 줄 {idx:3d} [{word}]: {snippet}...")
            if len(time_anchors) > 8:
                print(f"    ... 외 {len(time_anchors) - 8}건")

        # 5. 장부 5대 질문 점검 워크시트
        print("\n" + "\n".join(self.generate_five_questions_worksheet()))
        print("="*60 + "\n")

    def auto_fix(self, output_path: str = None) -> str:
        """연속 공백 정리, 줄 끝 공백 제거 등 안전한 자동 교정"""
        fixed_lines = []
        for line in self.lines:
            # 줄 끝 공백 제거
            stripped_end = line.rstrip()
            # 2개 이상 연속 공백 단일 공백으로 치환 (단, 빈 줄은 유지)
            if stripped_end:
                normalized = re.sub(r" {2,}", " ", stripped_end)
                fixed_lines.append(normalized)
            else:
                fixed_lines.append("")
                
        fixed_content = "\n".join(fixed_lines)
        if not fixed_content.endswith("\n"):
            fixed_content += "\n"

        target_path = output_path or self.filepath
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(fixed_content)

        return target_path


def resolve_paths(target_arg: str, novel_name: str = "yupum") -> Tuple[str, str]:
    """장 번호(숫자) 또는 파일 경로를 전달받아 draft 파일과 ledger 파일 경로를 자동 해석"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 만약 숫자만 들어온 경우 (예: "9")
    if target_arg.isdigit():
        ch_num = int(target_arg)
        draft_file = os.path.join(base_dir, f"novel-{novel_name}-text", f"ch{ch_num}-draft.txt")
        ledger_file = os.path.join(base_dir, f"novel-{novel_name}-ledger.md")
        return draft_file, ledger_file

    # 파일 경로인 경우
    draft_file = os.path.abspath(target_arg)
    ledger_file = os.path.join(base_dir, f"novel-{novel_name}-ledger.md")
    return draft_file, ledger_file

def main():
    parser = argparse.ArgumentParser(description="소설 연재 원고 자동 검증 및 교정 도구")
    parser.add_argument("target", help="검증할 원고 파일 (.txt) 또는 장 번호 (예: 9)")
    parser.add_argument("--novel", "-n", default="yupum", help="소설 이름 (기본값: yupum)")
    parser.add_argument("--ledger", "-l", help="사실 장부 마크다운 파일 경로 (.md)", default=None)
    parser.add_argument("--fix", action="store_true", help="연속 공백 등 안전한 교정 사항 자동 적용")
    parser.add_argument("--promote", "-p", action="store_true", help="검증 통과 시 chN-published.txt로 저장/승급")
    parser.add_argument("--out", help="교정 결과 저장 파일 경로")
    
    args = parser.parse_args()

    draft_file, default_ledger = resolve_paths(args.target, args.novel)
    ledger_file = args.ledger or default_ledger

    if not os.path.exists(draft_file):
        print(f"{RED}오류: 원고 파일을 찾을 수 없습니다: {draft_file}{RESET}")
        sys.exit(1)

    checker = NovelChecker(draft_file, ledger_file)
    checker.run_all()
    checker.print_report()

    if args.fix:
        backup_file = draft_file + ".bak"
        with open(backup_file, "w", encoding="utf-8") as f:
            f.write(checker.raw_text)
        fixed_file = checker.auto_fix(args.out)
        print(f"{GREEN}[O] 자동 교정 완료: {fixed_file} (원본 백업: {backup_file}){RESET}")

    if args.promote:
        if checker.errors:
            print(f"{RED}[X] 필수 오류가 있어 published.txt로 승급할 수 없습니다.{RESET}")
        else:
            published_file = draft_file.replace("-draft.txt", "-published.txt")
            with open(published_file, "w", encoding="utf-8") as f:
                f.write(checker.raw_text)
            print(f"{GREEN}[O] 검증 통과 - 게시본 확정 생성: {published_file}{RESET}")

if __name__ == "__main__":
    main()
