# ============================================================
# [AI 사용 표기]
# - AI 종류    : Claude Opus 5.5 (Anthropic, Claude Code)
# - 사용 목적  : 마이페이지(절약 금액·환경 기여도 통계, 카테고리 막대그래프, 주문 내역·취소·CSV 내보내기) 탭 작성
# - 프롬프트   : "ppt보고 만들어줘 파이썬으로 만드는것이 목표야"
#                (팀프로젝트 요구서 PDF + 동네냉장고 아이디어 제공)
# - 사용한 사람: 이찬민
# - 날짜       : 2026-11-07
# - 범위       : 이 파일 전체 (AI 생성 후 팀원 검토/수정 필요)
# ============================================================
"""마이페이지 탭: 나의 절약·환경 기여도 + 주문 내역."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from gui_app import GREEN
from gui_market import build_tree
from models import won


class MyPageTab(ttk.Frame):
    ORDER_COLUMNS = (("order_id", "주문번호", 80), ("title", "상품명", 230), ("qty", "수량", 55),
                     ("total", "결제금액", 90), ("saved", "절약", 80), ("method", "수령", 60),
                     ("created", "주문일시", 130), ("status", "상태", 80))
    CARDS = (("saved_money", "💰 아낀 생활비"), ("saved_kg", "🥬 구한 식재료"),
             ("co2_kg", "🌍 줄인 온실가스(추정)"), ("order_count", "🧾 구매 횟수"))

    def __init__(self, master, main):
        super().__init__(master, padding=10)
        self.main = main

        # ---- 통계 카드 ----
        cards = ttk.Frame(self)
        cards.pack(fill="x")
        self.card_labels = {}
        for col, (key, title) in enumerate(self.CARDS):
            box = ttk.LabelFrame(cards, text=title, padding=(14, 6))
            box.grid(row=0, column=col, sticky="nsew", padx=4)
            cards.columnconfigure(col, weight=1)
            self.card_labels[key] = ttk.Label(box, text="-", style="Big.TLabel")
            self.card_labels[key].pack()

        # 하단 버튼을 먼저 bottom에 배치해야 목록이 늘어나도 버튼이 가려지지 않는다
        btns = ttk.Frame(self)
        btns.pack(side="bottom", fill="x", pady=6)
        ttk.Button(btns, text="주문 취소", command=self.cancel_order).pack(side="left")
        ttk.Button(btns, text="CSV로 내보내기", command=self.export_csv).pack(side="left", padx=6)

        chart_box = ttk.LabelFrame(self, text="분류별 구한 식재료 (g)", padding=6)
        chart_box.pack(fill="x", pady=10)
        self.chart = tk.Canvas(chart_box, height=170, bg="white", highlightthickness=0)
        self.chart.pack(fill="both", expand=True)
        self.chart.bind("<Configure>", lambda e: self.draw_chart())

        # ---- 주문 내역 ----
        ttk.Label(self, text="내 주문 내역", style="H2.TLabel").pack(anchor="w")
        orders = ttk.Frame(self)
        orders.pack(fill="both", expand=True, pady=(4, 0))
        self.order_tree = build_tree(orders, self.ORDER_COLUMNS, height=7)
        self.stats = {}
        self.refresh()

    def refresh(self) -> None:
        store, user = self.main.store, self.main.user
        self.stats = store.stats(user.user_id)
        s = self.stats
        self.card_labels["saved_money"].config(text=won(s["saved_money"]))
        self.card_labels["saved_kg"].config(text=f"{s['saved_kg']:.1f} kg")
        self.card_labels["co2_kg"].config(text=f"{s['co2_kg']:.1f} kg")
        self.card_labels["order_count"].config(text=f"{s['order_count']} 회")

        self.order_tree.delete(*self.order_tree.get_children())
        for o in store.orders_of_buyer(user.user_id):
            self.order_tree.insert("", "end", iid=o.order_id, values=(
                o.order_id, o.item_title, o.quantity, won(o.total), won(o.saved_money),
                o.method, o.created_at, o.status))
        self.draw_chart()

    def draw_chart(self) -> None:
        c = self.chart
        c.delete("all")
        data = sorted(self.stats.get("by_category", {}).items(), key=lambda kv: -kv[1])
        w, h = c.winfo_width(), c.winfo_height()
        if not data:
            c.create_text(w / 2, h / 2, text="아직 구매 내역이 없어요. 동네 장터에서 첫 구매를 해보세요!",
                          fill="#888888")
            return
        top = max(v for _, v in data)
        left, right, row_h = 100, 80, min(30, (h - 10) / len(data))
        for i, (cat, grams) in enumerate(data):
            y = 8 + i * row_h
            bar_w = (w - left - right) * grams / top
            c.create_text(left - 10, y + row_h / 2, text=cat, anchor="e")
            c.create_rectangle(left, y + 4, left + bar_w, y + row_h - 4, fill=GREEN, outline="")
            c.create_text(left + bar_w + 6, y + row_h / 2, text=f"{grams:,}g", anchor="w")

    def cancel_order(self) -> None:
        sel = self.order_tree.selection()
        if not sel:
            messagebox.showinfo("주문 취소", "취소할 주문을 선택하세요.", parent=self)
            return
        if not messagebox.askyesno("주문 취소", "이 주문을 취소할까요?", parent=self):
            return
        try:
            self.main.store.cancel_order(self.main.user, sel[0])
        except ValueError as e:
            messagebox.showerror("주문 취소", str(e), parent=self)
            return
        self.main.refresh_all()

    def export_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self, title="주문 내역 저장", defaultextension=".csv",
            initialfile=f"동네냉장고_주문내역_{self.main.user.user_id}.csv",
            filetypes=[("CSV 파일", "*.csv")])
        if not path:
            return
        count = self.main.store.export_orders_csv(self.main.user.user_id, path)
        messagebox.showinfo("CSV 내보내기", f"{count}건을 저장했습니다.\n{path}", parent=self)
