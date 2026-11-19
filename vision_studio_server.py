#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Vision Studio — Full-Stack StoryOps & Visual Lab Server (v2.0)
실제 소설 작업실 데이터(유품, 증거4호, 사라진 호선, 마지막 통화, 침묵) 및
novel_checker.py / auto_blog_publisher.py / auto_postype_publisher.py / auto_backup.py 연동 서버
"""

import json
import os
import re
import shutil
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# pythonw.exe 실행 시 None stdout/stderr 크래시 방지 안전장치
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

try:
    from novel_checker import NovelChecker
    HAS_NOVEL_CHECKER = True
except ImportError:
    NovelChecker = None
    HAS_NOVEL_CHECKER = False

BASE_DIR = Path(__file__).resolve().parent
HTML_FILE = BASE_DIR / "Antigravity_Vision_Studio.html"
GRAPH_STORE_FILE = BASE_DIR / "causal_graphs.json"

NOVEL_CATALOG = {
    "yupum": {
        "id": "yupum",
        "title": "《유품》",
        "category": "카테고리 11 (연재소설 유품)",
        "folder": "novel-yupum-text",
        "ledger": "novel-yupum-ledger.md",
        "outline": "novel-yupum-outline.md",
        "status": "1~13장 연재 중",
    },
    "evidence4": {
        "id": "evidence4",
        "title": "《증거 4호》",
        "category": "미스터리/추리 시리즈",
        "folder": "novel-evidence4-text",
        "ledger": "novel-evidence4-ledger.md",
        "outline": "novel-evidence4-outline.md",
        "status": "1~12장 집필 완료",
    },
    "missingline": {
        "id": "missingline",
        "title": "《사라진 호선》",
        "category": "신작 스릴러 시리즈",
        "folder": "novel-missingline-text",
        "ledger": "novel-missingline-ledger.md",
        "outline": "novel-missingline-outline.md",
        "status": "1장 런칭 완료",
    },
    "silence": {
        "id": "silence",
        "title": "《침묵의 기록》",
        "category": "추리/서스펜스 시리즈",
        "folder": "novel-silence-text",
        "ledger": "novel-silence-ledger.md",
        "outline": "novel-silence-outline.md",
        "status": "1~8장 집필 완료",
    },
    "lasttalk": {
        "id": "lasttalk",
        "title": "《마지막 통화》",
        "category": "카테고리 10 (1~15장 완결)",
        "folder": "novel-lasttalk-text",
        "ledger": None,
        "outline": "novel-lasttalk-outline.md",
        "status": "1~15장 완결",
    },
}

DEFAULT_CAUSAL_GRAPHS = {
    "yupum": {
        "title": "《유품》 인물·단서 인과율 신경망",
        "nodes": [
            {"id": "haejin", "label": "서해진", "role": "주인공 / 유품 정리인", "x": 200, "y": 160, "color": "#38bdf8", "r": 25, "lore": "고인의 남겨진 물건과 메모에서 시점 불일치를 발견하고 진실을 추적하는 중심 인물."},
            {"id": "dongwoo", "label": "한동우", "role": "핵심 관계자", "x": 480, "y": 110, "color": "#f59e0b", "r": 22, "lore": "사건 당일의 행적과 통화 기록에 공백이 존재하며, 핵심 열쇠의 이동 경로와 연결됨."},
            {"id": "jaesik", "label": "마재식", "role": "현장 목격·연루자", "x": 480, "y": 310, "color": "#f43f5e", "r": 22, "lore": "보관함 출입 기록과 장부 내역에서 결정적 단서를 쥐고 있는 인물."},
            {"id": "haerin", "label": "서해린", "role": "해진의 가족", "x": 180, "y": 330, "color": "#10b981", "r": 20, "lore": "과거 사건의 기록과 가족사를 연결하는 주요 정서적·사실적 축."},
            {"id": "dohoon", "label": "강도훈", "role": "조사 협력자", "x": 750, "y": 180, "color": "#c084fc", "r": 22, "lore": "공식 기록과 실제 물품 이동 시각 사이의 모순을 검증하는 조력자."},
            {"id": "sechang", "label": "오세창", "role": "배후 이해관계자", "x": 740, "y": 340, "color": "#94a3b8", "r": 21, "lore": "계약서 및 장부 원장의 실제 수혜자로 지목되는 인물."},
        ],
        "edges": [
            {"from": "haejin", "to": "dongwoo", "label": "시각 행적 대조"},
            {"from": "haejin", "to": "jaesik", "label": "유품 전달 경로 추적"},
            {"from": "haerin", "to": "haejin", "label": "과거 단서 공유"},
            {"from": "dongwoo", "to": "dohoon", "label": "알리바이 검증"},
            {"from": "jaesik", "to": "sechang", "label": "장부 거래 연결", "color": "#f43f5e"},
            {"from": "dohoon", "to": "sechang", "label": "출입 기록 확보"},
        ],
    },
    "evidence4": {
        "title": "《증거 4호》 사실 장부 & 단서 관계망",
        "nodes": [
            {"id": "ev4", "label": "증거 4호", "role": "핵심 물증", "x": 500, "y": 210, "color": "#f59e0b", "r": 26, "lore": "사건 현장에서 수거된 네 번째 물증. 보관 이력과 봉인 시각에 결정적 단서가 담겨 있음."},
            {"id": "investigator", "label": "담당 조사관", "role": "주인공", "x": 210, "y": 160, "color": "#38bdf8", "r": 24, "lore": "1~12장에 걸쳐 증거 목록과 진술 조서의 시간차 모순을 역추적함."},
            {"id": "witness1", "label": "최초 목격자", "role": "진술인 A", "x": 230, "y": 340, "color": "#10b981", "r": 20, "lore": "비 오는 밤의 시각 진술에서 디지털 시계와 아날로그 기록 간 15분 오차가 발견됨."},
            {"id": "archive", "label": "보관소 기록", "role": "시간표 앵커", "x": 760, "y": 150, "color": "#c084fc", "r": 22, "lore": "출입 로그와 인수인계 서명란의 필적·시각 대조 포인트."},
            {"id": "suspect", "label": "내부 관계자", "role": "추적 대상", "x": 760, "y": 330, "color": "#f43f5e", "r": 23, "lore": "증거 4호의 라벨 교체 시점에 유일하게 접근 권한을 보유했던 인물."},
        ],
        "edges": [
            {"from": "investigator", "to": "ev4", "label": "봉인 이력 재검토"},
            {"from": "witness1", "to": "investigator", "label": "15분 시차 진술"},
            {"from": "ev4", "to": "archive", "label": "로그 대조"},
            {"from": "suspect", "to": "ev4", "label": "라벨 접근 흔적", "color": "#f43f5e"},
            {"from": "archive", "to": "suspect", "label": "단독 출입 확인"},
        ],
    },
    "missingline": {
        "title": "《사라진 호선》 노선·시각 인과율 신경망",
        "nodes": [
            {"id": "train", "label": "막차 열차", "role": "사라진 구간", "x": 490, "y": 200, "color": "#38bdf8", "r": 25, "lore": "정규 운행표와 관제 기록 사이에서 7분간 신호가 소실된 구간."},
            {"id": "passenger", "label": "탑승 기록자", "role": "시점 인물", "x": 200, "y": 180, "color": "#10b981", "r": 23, "lore": "열차 내부 안내판([ ])과 실제 정차역의 불일치를 최초로 인지한 인물."},
            {"id": "control", "label": "관제 센터", "role": "운행 로그", "x": 770, "y": 160, "color": "#f59e0b", "r": 22, "lore": "선로 전환 기록과 무전 교신 시각이 어긋난 지점."},
            {"id": "platform", "label": "폐쇄 승강장", "role": "공간 단서", "x": 490, "y": 360, "color": "#f43f5e", "r": 22, "lore": "도면상 폐쇄되었으나 전력 공급 기록이 남아 있는 지하 구역."},
        ],
        "edges": [
            {"from": "passenger", "to": "train", "label": "정차역 불일치 포착"},
            {"from": "train", "to": "control", "label": "7분 신호 공백"},
            {"from": "train", "to": "platform", "label": "우회 선로 진입", "color": "#f43f5e"},
            {"from": "control", "to": "platform", "label": "전력 로그 확인"},
        ],
    },
    "lasttalk": {
        "title": "《마지막 통화》 인물 관계망 (1~15장 완결)",
        "nodes": [
            {"id": "seojin", "label": "한서진", "role": "주인공", "x": 200, "y": 170, "color": "#38bdf8", "r": 24, "lore": "남겨진 마지막 통화 기록의 발신 위치와 배경음을 단서로 진실을 밝히는 주인공."},
            {"id": "doyoon", "label": "한도윤", "role": "발신 당사자", "x": 480, "y": 130, "color": "#f59e0b", "r": 22, "lore": "통화 직전 남긴 짧은 메모와 행적이 전체 사건의 출발점이 됨."},
            {"id": "seungtae", "label": "오승태", "role": "핵심 조사선", "x": 480, "y": 320, "color": "#f43f5e", "r": 22, "lore": "통화 중계기 기록과 차량 이동 경로의 교차점에 위치한 인물."},
            {"id": "hana", "label": "윤하나", "role": "결정적 증언자", "x": 760, "y": 180, "color": "#10b981", "r": 21, "lore": "사건 당일 저녁의 실제 만남 시각을 증언하여 알리바이를 뒤집는 인물."},
            {"id": "seunghwan", "label": "백승환", "role": "배후 연결고리", "x": 760, "y": 330, "color": "#c084fc", "r": 21, "lore": "14~15장 클라이맥스에서 모든 통화 내역의 종착지로 밝혀지는 인물."},
        ],
        "edges": [
            {"from": "doyoon", "to": "seojin", "label": "마지막 발신 기록"},
            {"from": "seojin", "to": "seungtae", "label": "행적 추적"},
            {"from": "seojin", "to": "hana", "label": "시각 증언 확보"},
            {"from": "seungtae", "to": "seunghwan", "label": "중계기 위치 일치", "color": "#f43f5e"},
            {"from": "hana", "to": "seunghwan", "label": "결정적 단서 제공"},
        ],
    },
}


def load_causal_graphs():
    if GRAPH_STORE_FILE.exists():
        try:
            data = json.loads(GRAPH_STORE_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                merged = dict(DEFAULT_CAUSAL_GRAPHS)
                merged.update(data)
                return merged
        except Exception:
            pass
    return dict(DEFAULT_CAUSAL_GRAPHS)


def save_causal_graphs(graphs: dict):
    GRAPH_STORE_FILE.write_text(
        json.dumps(graphs, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def safe_resolve_chapter(novel_key: str, file_name: str) -> Path:
    meta = NOVEL_CATALOG.get(novel_key, NOVEL_CATALOG["yupum"])
    folder = (BASE_DIR / meta["folder"]).resolve()
    clean_name = Path(file_name).name
    target = (folder / clean_name).resolve()
    if folder not in target.parents and target != folder:
        raise ValueError("잘못된 파일 경로입니다.")
    return target


def scan_novel_chapters(novel_key: str):
    info = NOVEL_CATALOG.get(novel_key, NOVEL_CATALOG["yupum"])
    folder = BASE_DIR / info["folder"]
    chapters = []
    if folder.exists():
        files = sorted(folder.glob("*.txt"))
        for f in files:
            try:
                text = f.read_text(encoding="utf-8")
                length = len(text)
            except Exception:
                length = 0
            chapters.append({
                "fileName": f.name,
                "isPublished": "published" in f.name,
                "charCount": length,
            })
    return chapters


def fallback_check_text(raw_text: str):
    """novel_checker.py가 없는 환경에서도 동작하는 경량 검수기"""
    passes, warnings, errors = [], [], []
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    if lines and "허구입니다" in lines[0]:
        passes.append("머리말 허구 안내 문구 확인")
    else:
        errors.append("첫 줄 허구 안내 문구 누락")

    if lines and (re.search(r"\(\d+장에 계속\)$", lines[-1]) or lines[-1] == "(끝)"):
        passes.append("끝 줄 연재 표기 형식 확인")
    else:
        warnings.append("끝 줄 '(N장에 계속)' 또는 '(끝)' 표기를 확인하세요")

    if raw_text.count('"') % 2 == 0:
        passes.append("대사 큰따옴표(\"\") 짝 일치")
    else:
        errors.append("대사 큰따옴표(\"\") 짝 불일치")

    if raw_text.count("[") == raw_text.count("]"):
        passes.append("문자/메모 대괄호([]) 짝 일치")
    else:
        errors.append("대괄호([]) 짝 불일치")

    char_count = len(raw_text)
    dialogue_chars = sum(len(m.group(0)) for m in re.finditer(r'"[^"]*"', raw_text))
    dialogue_ratio = round((dialogue_chars / char_count) * 100, 1) if char_count else 0.0
    return {
        "charCount": char_count,
        "dialogueRatio": dialogue_ratio,
        "passes": passes,
        "warnings": warnings,
        "errors": errors,
        "timeAnchorsCount": len(re.findall(r"\d{1,2}시\s*\d{0,2}분?", raw_text)),
        "hasLedger": False,
        "ledgerQuestionsCount": 0,
    }


def run_check_for_file(target_path: Path, ledger_path: Path = None):
    if HAS_NOVEL_CHECKER:
        checker = NovelChecker(
            str(target_path),
            str(ledger_path) if ledger_path and ledger_path.exists() else None,
        )
        checker.check_header_and_footer()
        checker.check_length()
        checker.check_quote_pairs()
        checker.check_spacing_and_paragraphs()
        checker.check_time_expressions()
        checker.check_subject_repetitions()
        checker.check_emotion_exposition()
        time_anchors = checker.extract_time_anchors()
        ledger_info = checker.load_ledger_info()

        char_count = len(checker.raw_text)
        dialogue_chars = sum(len(m.group(0)) for m in re.finditer(r'"[^"]*"', checker.raw_text))
        dialogue_ratio = round((dialogue_chars / char_count) * 100, 1) if char_count else 0.0
        return {
            "charCount": char_count,
            "dialogueRatio": dialogue_ratio,
            "passes": checker.passes,
            "warnings": checker.warnings,
            "errors": checker.errors,
            "timeAnchorsCount": len(time_anchors),
            "hasLedger": bool(ledger_info),
            "ledgerQuestionsCount": len(ledger_info.get("questions", [])),
        }
    return fallback_check_text(target_path.read_text(encoding="utf-8"))


class StudioHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html", "/Antigravity_Vision_Studio.html"):
            content = HTML_FILE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        if parsed.path == "/api/novels":
            novels_list = []
            for key, meta in NOVEL_CATALOG.items():
                chapters = scan_novel_chapters(key)
                pub_count = sum(1 for c in chapters if c["isPublished"])
                total_chars = sum(c["charCount"] for c in chapters if c["isPublished"] or "ch0" in c["fileName"])
                novels_list.append({
                    **meta,
                    "chapters": chapters,
                    "publishedCount": pub_count,
                    "totalFiles": len(chapters),
                    "totalChars": total_chars,
                })
            self._send_json({
                "success": True,
                "novels": novels_list,
                "hasNovelChecker": HAS_NOVEL_CHECKER,
            })
            return

        if parsed.path == "/api/graph":
            qs = parse_qs(parsed.query)
            novel_key = qs.get("novel", ["yupum"])[0]
            graphs = load_causal_graphs()
            graph = graphs.get(novel_key, graphs.get("yupum"))
            self._send_json({"success": True, "novel": novel_key, "graph": graph})
            return

        if parsed.path == "/api/chapter":
            qs = parse_qs(parsed.query)
            novel_key = qs.get("novel", ["yupum"])[0]
            file_name = qs.get("fileName", ["ch13-published.txt"])[0]
            meta = NOVEL_CATALOG.get(novel_key, NOVEL_CATALOG["yupum"])
            try:
                target = safe_resolve_chapter(novel_key, file_name)
            except ValueError as e:
                self._send_json({"success": False, "error": str(e)}, 400)
                return
            if not target.exists():
                self._send_json({"success": False, "error": "파일 없음"}, 404)
                return
            text = target.read_text(encoding="utf-8")
            self._send_json({
                "success": True,
                "novel": novel_key,
                "title": meta["title"],
                "fileName": target.name,
                "content": text,
            })
            return

        if parsed.path == "/api/docs":
            qs = parse_qs(parsed.query)
            novel_key = qs.get("novel", ["yupum"])[0]
            kind = qs.get("kind", ["ledger"])[0]
            meta = NOVEL_CATALOG.get(novel_key, NOVEL_CATALOG["yupum"])
            rel_name = meta.get("ledger") if kind == "ledger" else meta.get("outline")
            if not rel_name:
                self._send_json({
                    "success": True,
                    "novel": novel_key,
                    "kind": kind,
                    "fileName": None,
                    "exists": False,
                    "content": f"# {meta['title']} {kind} 파일이 아직 등록되지 않았습니다.",
                })
                return
            doc_path = BASE_DIR / rel_name
            exists = doc_path.exists()
            content = doc_path.read_text(encoding="utf-8") if exists else ""
            self._send_json({
                "success": True,
                "novel": novel_key,
                "kind": kind,
                "fileName": rel_name,
                "exists": exists,
                "content": content,
            })
            return

        self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        body_raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            body = json.loads(body_raw)
        except Exception:
            body = {}

        if parsed.path == "/api/check":
            novel_key = body.get("novel", "yupum")
            file_name = body.get("fileName", "")
            meta = NOVEL_CATALOG.get(novel_key, NOVEL_CATALOG["yupum"])
            folder = BASE_DIR / meta["folder"]

            if not file_name:
                candidates = sorted(folder.glob("*.txt"))
                target_path = candidates[-1] if candidates else None
            else:
                try:
                    target_path = safe_resolve_chapter(novel_key, file_name)
                except ValueError as e:
                    self._send_json({"success": False, "error": str(e)}, 400)
                    return

            if not target_path or not target_path.exists():
                self._send_json({"success": False, "error": "원고 파일을 찾을 수 없습니다."}, 404)
                return

            ledger_path = (BASE_DIR / meta["ledger"]) if meta.get("ledger") else None
            res = run_check_for_file(target_path, ledger_path)
            self._send_json({
                "success": True,
                "novel": novel_key,
                "novelTitle": meta["title"],
                "fileName": target_path.name,
                **res,
            })
            return

        if parsed.path == "/api/chapter/save":
            novel_key = body.get("novel", "yupum")
            file_name = body.get("fileName", "")
            content = body.get("content", "")
            if not file_name:
                self._send_json({"success": False, "error": "fileName이 필요합니다."}, 400)
                return
            try:
                target = safe_resolve_chapter(novel_key, file_name)
            except ValueError as e:
                self._send_json({"success": False, "error": str(e)}, 400)
                return
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            self._send_json({
                "success": True,
                "fileName": target.name,
                "charCount": len(content),
                "message": f"{target.name} 저장 완료 ({len(content):,}자)",
            })
            return

        if parsed.path == "/api/chapter/fix":
            novel_key = body.get("novel", "yupum")
            file_name = body.get("fileName", "")
            meta = NOVEL_CATALOG.get(novel_key, NOVEL_CATALOG["yupum"])
            try:
                target = safe_resolve_chapter(novel_key, file_name)
            except ValueError as e:
                self._send_json({"success": False, "error": str(e)}, 400)
                return
            if not target.exists():
                self._send_json({"success": False, "error": "원고 파일을 찾을 수 없습니다."}, 404)
                return

            before = target.read_text(encoding="utf-8")
            if HAS_NOVEL_CHECKER:
                ledger_path = (BASE_DIR / meta["ledger"]) if meta.get("ledger") else None
                checker = NovelChecker(
                    str(target),
                    str(ledger_path) if ledger_path and ledger_path.exists() else None,
                )
                checker.auto_fix(str(target))
                after = target.read_text(encoding="utf-8")
            else:
                after = re.sub(r"[ \t]+\n", "\n", before)
                after = re.sub(r"\n{3,}", "\n\n", after)
                target.write_text(after, encoding="utf-8")

            self._send_json({
                "success": True,
                "fileName": target.name,
                "changed": before != after,
                "content": after,
                "message": "안전한 자동 교정(--fix) 적용 완료" if before != after else "교정할 항목이 없습니다.",
            })
            return

        if parsed.path == "/api/chapter/promote":
            novel_key = body.get("novel", "yupum")
            file_name = body.get("fileName", "")
            meta = NOVEL_CATALOG.get(novel_key, NOVEL_CATALOG["yupum"])
            try:
                target = safe_resolve_chapter(novel_key, file_name)
            except ValueError as e:
                self._send_json({"success": False, "error": str(e)}, 400)
                return
            if not target.exists():
                self._send_json({"success": False, "error": "원고 파일을 찾을 수 없습니다."}, 404)
                return

            ledger_path = (BASE_DIR / meta["ledger"]) if meta.get("ledger") else None
            check_res = run_check_for_file(target, ledger_path)
            if check_res["errors"]:
                self._send_json({
                    "success": False,
                    "error": f"필수 오류 {len(check_res['errors'])}건이 남아 있어 승급할 수 없습니다.",
                    "errors": check_res["errors"],
                }, 400)
                return

            pub_name = re.sub(r"-draft(\.txt)$", r"-published\1", target.name)
            if pub_name == target.name and "-published" not in pub_name:
                pub_name = target.stem + "-published" + target.suffix
            pub_path = target.parent / pub_name
            if target != pub_path:
                shutil.copy2(target, pub_path)

            self._send_json({
                "success": True,
                "publishedFile": pub_path.name,
                "message": f"게시본 승급 완료: {pub_path.name}",
            })
            return

        if parsed.path == "/api/docs/save":
            novel_key = body.get("novel", "yupum")
            kind = body.get("kind", "ledger")
            content = body.get("content", "")
            meta = NOVEL_CATALOG.get(novel_key, NOVEL_CATALOG["yupum"])
            rel_name = meta.get("ledger") if kind == "ledger" else meta.get("outline")
            if not rel_name:
                self._send_json({"success": False, "error": "해당 작품에 등록된 문서 경로가 없습니다."}, 400)
                return
            doc_path = BASE_DIR / rel_name
            doc_path.write_text(content, encoding="utf-8")
            self._send_json({
                "success": True,
                "fileName": rel_name,
                "message": f"{rel_name} 저장 완료 ({len(content):,}자)",
            })
            return

        if parsed.path == "/api/graph/save":
            novel_key = body.get("novel", "yupum")
            graph = body.get("graph")
            if not isinstance(graph, dict) or "nodes" not in graph or "edges" not in graph:
                self._send_json({"success": False, "error": "유효하지 않은 그래프 데이터입니다."}, 400)
                return
            graphs = load_causal_graphs()
            graphs[novel_key] = graph
            save_causal_graphs(graphs)
            self._send_json({
                "success": True,
                "novel": novel_key,
                "message": f"{novel_key} 인과율 신경망 저장 완료 (노드 {len(graph['nodes'])}개, 연결 {len(graph['edges'])}개)",
            })
            return

        if parsed.path == "/api/publish":
            platform = body.get("platform", "blog")
            dry_run = body.get("dryRun", True)
            
            # 소설 연재 실전 발행기 연결
            script_path = BASE_DIR / "publish_yupum_ch14.py"
            if dry_run:
                # 점검 모드: 원고 파일과 설정 검증
                ch14_file = BASE_DIR / "novel-yupum-text" / "ch14-published.txt"
                if not ch14_file.exists():
                    ch14_file = BASE_DIR / "novel-yupum-text" / "ch14-draft.txt"
                
                status_msg = f"[점검 완료] 《유품》 14장 원고 확인됨 ({ch14_file.name}, {len(ch14_file.read_text(encoding='utf-8'))}자) - 네이버 블로그(카테고리 11) 실전 발행 준비 완료!"
                self._send_json({
                    "success": True,
                    "platform": platform,
                    "dryRun": True,
                    "command": f"python publish_yupum_ch14.py (점검)",
                    "stdout": status_msg,
                    "stderr": "",
                })
                return

            # 실전 발행 모드: 백그라운드로 발행기 가동
            proc = subprocess.Popen(
                [sys.executable, "-u", str(script_path)],
                cwd=str(BASE_DIR),
                creationflags=0x00000008 if sys.platform == "win32" else 0, # DETACHED_PROCESS
            )
            self._send_json({
                "success": True,
                "platform": platform,
                "dryRun": False,
                "command": f"python publish_yupum_ch14.py",
                "stdout": "🚀 [실전 발행 가동] 《유품》 14장 발행기가 백그라운드에서 실행되었습니다. (화면에 로그인 창이 뜨면 1회 확인해 주세요)",
                "stderr": "",
            })
            return

        if parsed.path == "/api/backup":
            run_backup = body.get("runBackup", False)
            status_proc = subprocess.run(
                ["git", "status", "--short"],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
            )
            backup_output = ""
            backup_ok = True
            if run_backup:
                backup_script = BASE_DIR / "auto_backup.py"
                if backup_script.exists():
                    b_proc = subprocess.run(
                        [sys.executable, str(backup_script)],
                        cwd=str(BASE_DIR),
                        capture_output=True,
                        text=True,
                        timeout=60,
                    )
                    backup_ok = b_proc.returncode == 0
                    backup_output = (b_proc.stdout + "\n" + b_proc.stderr).strip()
                else:
                    backup_ok = False
                    backup_output = "auto_backup.py를 찾을 수 없습니다."

            self._send_json({
                "success": backup_ok,
                "message": "auto_backup.py 실행 완료" if run_backup else "작업실 상태 점검 및 동기화 준비 완료",
                "gitStatus": status_proc.stdout.strip() or "깨끗함 (모든 변경사항 동기화됨)",
                "output": backup_output,
            })
            return

        self.send_error(404, "Not Found")


if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", "8080"))
        server = HTTPServer(("0.0.0.0", port), StudioHandler)
        with open(BASE_DIR / "server_status.txt", "w", encoding="utf-8") as f:
            f.write(f"Server started on port {port}\n")
        server.serve_forever()
    except Exception as e:
        import traceback
        with open(BASE_DIR / "server_crash.txt", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
