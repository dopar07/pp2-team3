# ============================================================
# [AI 사용 표기]
# - AI 종류    : Claude Opus 5.5 (Anthropic, Claude Code)
# - 사용 목적  : tkinter 메인 윈도우(App) 및 공통 스타일 작성
# - 프롬프트   : "ppt보고 만들어줘 파이썬으로 만드는것이 목표야"
#                (팀프로젝트 요구서 PDF + 동네냉장고 아이디어 제공)
# - 사용한 사람: 이찬민
# - 날짜       : 2026-11-07
# - 범위       : 이 파일 전체 (AI 생성 후 팀원 검토/수정 필요)
# ============================================================
"""App: 로그인 화면과 메인 화면을 전환하는 최상위 윈도우."""

import tkinter as tk
from tkinter import ttk

GREEN = "#2e7d32"
DARK_GREEN = "#1b5e20"
LIGHT_GREEN = "#e8f5e9"
ORANGE = "#ef6c00"
RED = "#c62828"
GRAY = "#9e9e9e"
FONT = "맑은 고딕"


def setup_style(root: tk.Tk) -> None:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    base = (FONT, 10)
    # 일반 tk 위젯(Listbox, Text)만 옵션DB로 폰트 지정. "*Font"로 전체 지정하면 ttk 스타일 폰트가 무시된다.
    for pattern in ("*Listbox.font", "*Text.font", "*TCombobox*Listbox.font"):
        root.option_add(pattern, base)
    style.configure(".", font=base)
    style.configure("Treeview", rowheight=26)
    style.configure("Treeview.Heading", font=(FONT, 10, "bold"))
    style.configure("Title.TLabel", font=(FONT, 20, "bold"), foreground=GREEN)
    style.configure("Sub.TLabel", foreground="#555555")
    style.configure("H2.TLabel", font=(FONT, 12, "bold"))
    style.configure("Header.TFrame", background=GREEN)
    style.configure("Header.TLabel", background=GREEN, foreground="white", font=(FONT, 11, "bold"))
    style.configure("Accent.TButton", background=GREEN, foreground="white", font=(FONT, 10, "bold"))
    style.map("Accent.TButton", background=[("active", DARK_GREEN), ("disabled", GRAY)])
    style.configure("Big.TLabel", font=(FONT, 18, "bold"), foreground=GREEN)
    style.configure("TNotebook.Tab", padding=(14, 6), font=(FONT, 10, "bold"))


class App(tk.Tk):
    def __init__(self, store):
        super().__init__()
        self.title("동네냉장고 - 우리 동네 소비기한 임박 식재료 매칭")
        self.geometry("1180x720")
        self.minsize(980, 620)
        setup_style(self)
        self.store = store
        self.current_user = None
        self.frame = None
        self.show_login()

    def _switch(self, frame: ttk.Frame) -> None:
        if self.frame is not None:
            self.frame.destroy()
        self.frame = frame
        self.frame.pack(fill="both", expand=True)

    def show_login(self) -> None:
        from gui_login import LoginFrame        # 순환 import 방지를 위해 함수 안에서 import
        self.current_user = None
        self._switch(LoginFrame(self, self))

    def on_login(self, user) -> None:
        from gui_main import MainFrame
        self.current_user = user
        self._switch(MainFrame(self, self))
