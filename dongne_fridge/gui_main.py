# ============================================================
# [AI 사용 표기]
# - AI 종류    : Claude Opus 5.5 (Anthropic, Claude Code)
# - 사용 목적  : 로그인 후 메인 화면(상단 바 + 탭 구성) 작성
# - 프롬프트   : "ppt보고 만들어줘 파이썬으로 만드는것이 목표야"
#                (팀프로젝트 요구서 PDF + 동네냉장고 아이디어 제공)
# - 사용한 사람: 이찬민
# - 날짜       : 2026-11-07
# - 범위       : 이 파일 전체 (AI 생성 후 팀원 검토/수정 필요)
# ============================================================
"""메인 화면: 상단 사용자 정보 바 + 탭(장터/지도/판매등록/판매관리/마이페이지)."""

import tkinter as tk
from tkinter import ttk

from gui_map import MapTab
from gui_market import MarketTab
from gui_mypage import MyPageTab
from gui_sell import MySalesTab, SellTab
from location import DONG_NAMES


class MainFrame(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        user = app.current_user

        # ---- 상단 바 ----
        header = ttk.Frame(self, style="Header.TFrame", padding=(16, 10))
        header.pack(fill="x")
        ttk.Label(header, text="🧊 동네냉장고", style="Header.TLabel",
                  font=("맑은 고딕", 14, "bold")).pack(side="left")
        ttk.Button(header, text="로그아웃", command=app.show_login).pack(side="right")
        self.dong_var = tk.StringVar(value=user.dong)
        dong_box = ttk.Combobox(header, textvariable=self.dong_var, values=DONG_NAMES,
                                state="readonly", width=8)
        dong_box.pack(side="right", padx=(4, 16))
        dong_box.bind("<<ComboboxSelected>>", self.on_dong_change)
        ttk.Label(header, text=f"{user.display_name}님 · 내 동네",
                  style="Header.TLabel").pack(side="right")

        # ---- 탭 ----
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)
        self.tabs = [
            (MarketTab(self.notebook, self), "🛒 동네 장터"),
            (MapTab(self.notebook, self), "🗺 동네 지도"),
            (SellTab(self.notebook, self), "➕ 상품 등록"),
            (MySalesTab(self.notebook, self), "📦 내 판매 관리"),
            (MyPageTab(self.notebook, self), "🌱 마이페이지"),
        ]
        for tab, title in self.tabs:
            self.notebook.add(tab, text=title)
        self.market = self.tabs[0][0]
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self.refresh_current())

    @property
    def store(self):
        return self.app.store

    @property
    def user(self):
        return self.app.current_user

    def refresh_current(self) -> None:
        """선택된 탭만 새로고침 (탭을 열 때마다 최신 데이터로)."""
        index = self.notebook.index("current")
        self.tabs[index][0].refresh()

    def refresh_all(self) -> None:
        for tab, _ in self.tabs:
            tab.refresh()

    def go_to_market(self) -> None:
        self.notebook.select(0)

    def on_dong_change(self, event=None) -> None:
        self.store.change_dong(self.user, self.dong_var.get())
        self.refresh_all()
