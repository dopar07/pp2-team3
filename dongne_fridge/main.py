# ============================================================
# [AI 사용 표기]
# - AI 종류    : Claude Opus 5.5 (Anthropic, Claude Code)
# - 사용 목적  : 프로그램 시작 파일 작성
# - 프롬프트   : "ppt보고 만들어줘 파이썬으로 만드는것이 목표야"
#                (팀프로젝트 요구서 PDF + 동네냉장고 아이디어 제공)
# - 사용한 사람: 이찬민
# - 날짜       : 2026-11-07
# - 범위       : 이 파일 전체 (AI 생성 후 팀원 검토/수정 필요)
# ============================================================
"""동네냉장고 실행 파일.   실행:  python main.py"""

from pathlib import Path

from gui_app import App
from storage import DataStore

DATA_DIR = Path(__file__).resolve().parent / "data"


def main() -> None:
    store = DataStore(DATA_DIR)
    App(store).mainloop()


if __name__ == "__main__":
    main()
