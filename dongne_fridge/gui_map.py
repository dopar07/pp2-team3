# ============================================================
# [AI 사용 표기]
# - AI 종류    : Claude Opus 5.5 (Anthropic, Claude Code)
# - 사용 목적  : Canvas로 동네별 상품 분포 지도를 그리는 탭 작성
# - 프롬프트   : "ppt보고 만들어줘 파이썬으로 만드는것이 목표야"
#                (팀프로젝트 요구서 PDF + 동네냉장고 아이디어 제공)
# - 사용한 사람: 이찬민
# - 날짜       : 2026-11-07
# - 범위       : 이 파일 전체 (AI 생성 후 팀원 검토/수정 필요)
# ============================================================
"""동네 지도 탭: 내 동네를 중심으로 동별 판매중 상품 수를 원으로 표시.

동네 원을 클릭하면 오른쪽에 그 동네의 상품 목록이 나온다.
"""

import tkinter as tk
from collections import Counter
from tkinter import ttk

from gui_app import GRAY, GREEN, ORANGE
from gui_market import ItemDetailDialog
from location import NEIGHBORHOODS, distance_km, offset_km
from models import won


class MapTab(ttk.Frame):
    RINGS_KM = (1, 2, 3)

    def __init__(self, master, main):
        super().__init__(master, padding=10)
        self.main = main
        self.list_ids: list[str] = []

        self.canvas = tk.Canvas(self, bg="#f5faf3", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.refresh())

        side = ttk.Frame(self, padding=(12, 0, 0, 0), width=300)
        side.pack(side="right", fill="y")
        side.pack_propagate(False)
        self.side_title = ttk.Label(side, text="동네를 클릭하세요", style="H2.TLabel")
        self.side_title.pack(anchor="w", pady=(0, 6))
        self.listbox = tk.Listbox(side, activestyle="none", selectbackground=GREEN)
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<Double-1>", lambda e: self.open_selected())
        ttk.Button(side, text="상세보기 / 주문", style="Accent.TButton",
                   command=self.open_selected).pack(fill="x", pady=(8, 0))
        ttk.Label(side, text="● 주황: 내 동네  ● 초록: 상품 있음\n원이 클수록 상품이 많아요. 점선: 1·2·3km",
                  style="Sub.TLabel").pack(anchor="w", pady=(8, 0))

    def _available_items(self):
        user = self.main.user
        return [i for i in self.main.store.items.values()
                if i.is_available() and i.seller_id != user.user_id]

    def refresh(self) -> None:
        c = self.canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 50 or h < 50:          # 아직 화면에 그려지기 전
            return
        center = self.main.user.dong
        cx, cy = w / 2, h / 2

        # 가장 먼 동이 화면 안에 들어오도록 축척(px/km) 계산
        max_km = max(max(abs(dx), abs(dy)) for dx, dy in
                     (offset_km(center, d) for d in NEIGHBORHOODS)) or 1
        scale = min(w, h) / 2 * 0.82 / max_km

        for km in self.RINGS_KM:
            r = km * scale
            c.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#b7d3b0", dash=(4, 4))
            c.create_text(cx + r - 4, cy - 8, text=f"{km}km", fill="#7a9c72", anchor="e",
                          font=("맑은 고딕", 9))

        counts = Counter(i.dong for i in self._available_items())
        for dong in NEIGHBORHOODS:
            dx, dy = offset_km(center, dong)
            x, y = cx + dx * scale, cy - dy * scale
            n = counts.get(dong, 0)
            r = 10 + min(n, 8) * 3
            color = ORANGE if dong == center else (GREEN if n else GRAY)
            tag = f"dong:{dong}"
            c.create_oval(x - r, y - r, x + r, y + r, fill=color, outline="white", width=2,
                          tags=("dong", tag))
            c.create_text(x, y, text=str(n), fill="white", font=("맑은 고딕", 10, "bold"),
                          tags=("dong", tag))
            c.create_text(x, y + r + 10, text=dong, font=("맑은 고딕", 9, "bold"), tags=("dong", tag))
        c.tag_bind("dong", "<Button-1>", self.on_click)
        c.tag_bind("dong", "<Enter>", lambda e: c.config(cursor="hand2"))
        c.tag_bind("dong", "<Leave>", lambda e: c.config(cursor=""))
        c.create_text(12, 12, anchor="nw", text=f"{center} 중심 · 판매중 상품 분포",
                      font=("맑은 고딕", 11, "bold"), fill="#33691e")

    def on_click(self, event) -> None:
        current = self.canvas.find_withtag("current")
        if not current:
            return
        for tag in self.canvas.gettags(current[0]):
            if tag.startswith("dong:"):
                self.show_dong(tag[5:])
                return

    def show_dong(self, dong: str) -> None:
        items = sorted((i for i in self._available_items() if i.dong == dong),
                       key=lambda i: i.days_left())
        dist = distance_km(self.main.user.dong, dong)
        self.side_title.config(text=f"{dong} ({dist:.1f}km) · {len(items)}개")
        self.listbox.delete(0, "end")
        self.list_ids = [i.item_id for i in items]
        for i in items:
            self.listbox.insert("end", f"[{i.d_day_text()}] {i.title} {won(i.current_price())}")

    def open_selected(self) -> None:
        sel = self.listbox.curselection()
        if sel:
            ItemDetailDialog(self, self.main, self.list_ids[sel[0]])
