# ============================================================
# [AI 사용 표기]
# - AI 종류    : Claude Opus 5.5 (Anthropic, Claude Code)
# - 사용 목적  : 동네 장터(검색/필터/정렬 목록) 탭과 상품 상세·주문 창 GUI 작성
# - 프롬프트   : "ppt보고 만들어줘 파이썬으로 만드는것이 목표야"
#                (팀프로젝트 요구서 PDF + 동네냉장고 아이디어 제공)
# - 사용한 사람: 이찬민
# - 날짜       : 2026-11-07
# - 범위       : 이 파일 전체 (AI 생성 후 팀원 검토/수정 필요)
# ============================================================
"""동네 장터 탭: 반경 내 임박 상품 검색 + 상세보기/주문."""

import tkinter as tk
from tkinter import messagebox, ttk

from gui_app import GREEN, LIGHT_GREEN, ORANGE, RED
from location import MAX_DELIVERY_KM, distance_km
from models import CATEGORIES, ITEM_TYPES, won
from storage import SORT_OPTIONS

RADIUS_OPTIONS = {"1km": 1.0, "2km": 2.0, "3km": 3.0, "5km": 5.0, "전체": None}

# (컬럼ID, 제목, 너비) tuple 목록
COLUMNS = (
    ("title", "상품명", 230), ("type", "종류", 80), ("category", "분류", 85),
    ("price", "판매가", 80), ("rate", "할인율", 60), ("dday", "소비기한", 75),
    ("dist", "거리", 60), ("dong", "동네", 65), ("seller", "판매자", 140), ("qty", "남은수량", 65),
)


def build_tree(parent, columns, height=15) -> ttk.Treeview:
    """스크롤바가 달린 Treeview를 만든다 (다른 탭에서도 재사용)."""
    frame = ttk.Frame(parent)
    frame.pack(fill="both", expand=True)
    tree = ttk.Treeview(frame, columns=[c[0] for c in columns], show="headings", height=height)
    for col_id, title, width in columns:
        tree.heading(col_id, text=title)
        tree.column(col_id, width=width, anchor="w" if col_id == "title" else "center")
    bar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=bar.set)
    tree.pack(side="left", fill="both", expand=True)
    bar.pack(side="right", fill="y")
    return tree


class MarketTab(ttk.Frame):
    def __init__(self, master, main):
        super().__init__(master, padding=10)
        self.main = main

        # ---- 검색 / 필터 바 ----
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 8))
        self.keyword = tk.StringVar()
        self.category = tk.StringVar(value="전체")
        self.item_type = tk.StringVar(value="전체")
        self.radius = tk.StringVar(value="3km")
        self.sort_by = tk.StringVar(value="소비기한 임박순")
        self.only_fav = tk.BooleanVar(value=False)

        ttk.Label(bar, text="검색").pack(side="left")
        entry = ttk.Entry(bar, textvariable=self.keyword, width=18)
        entry.pack(side="left", padx=(4, 10))
        entry.bind("<Return>", lambda e: self.refresh())
        combos = [
            ("분류", self.category, ("전체",) + CATEGORIES, 10),
            ("종류", self.item_type, ("전체",) + ITEM_TYPES, 10),
            ("반경", self.radius, tuple(RADIUS_OPTIONS), 6),
            ("정렬", self.sort_by, tuple(SORT_OPTIONS), 15),
        ]
        for label, var, values, width in combos:
            ttk.Label(bar, text=label).pack(side="left")
            box = ttk.Combobox(bar, textvariable=var, values=values, state="readonly", width=width)
            box.pack(side="left", padx=(4, 10))
            box.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        ttk.Checkbutton(bar, text="♥ 찜만", variable=self.only_fav,
                        command=self.refresh).pack(side="left")
        ttk.Button(bar, text="검색", style="Accent.TButton", command=self.refresh).pack(side="right")

        # ---- 하단 (목록보다 먼저 bottom에 배치해야 창이 작아져도 가려지지 않음) ----
        bottom = ttk.Frame(self)
        bottom.pack(side="bottom", fill="x", pady=(8, 0))
        self.status = ttk.Label(bottom, text="", style="Sub.TLabel")
        self.status.pack(side="left")
        ttk.Button(bottom, text="상세보기 / 주문", style="Accent.TButton",
                   command=self.open_selected).pack(side="right")
        ttk.Label(bottom, text="빨간 글씨: 오늘·내일 마감(자동 추가할인)   초록 배경: 못난이 손질 상품",
                  style="Sub.TLabel").pack(side="right", padx=12)

        # ---- 목록 ----
        self.tree = build_tree(self, COLUMNS)
        self.tree.tag_configure("urgent", foreground=RED)
        self.tree.tag_configure("ugly", background=LIGHT_GREEN)
        self.tree.bind("<Double-1>", lambda e: self.open_selected())
        self.refresh()

    def refresh(self) -> None:
        store, user = self.main.store, self.main.user
        results = store.search_items(
            user, self.keyword.get(), self.category.get(), self.item_type.get(),
            RADIUS_OPTIONS[self.radius.get()], self.sort_by.get(), self.only_fav.get())
        self.tree.delete(*self.tree.get_children())
        for item, dist in results:
            seller = store.users.get(item.seller_id)
            tags = []
            if item.days_left() <= 1:
                tags.append("urgent")
            if item.item_type == "못난이손질":
                tags.append("ugly")
            fav = "♥ " if item.item_id in user.favorites else ""
            self.tree.insert("", "end", iid=item.item_id, tags=tags, values=(
                fav + item.title, item.item_type, item.category, won(item.current_price()),
                f"{item.discount_rate()}%", item.d_day_text(), f"{dist:.1f}km", item.dong,
                seller.display_name if seller else "-", item.quantity))
        self.status.config(text=f"내 동네 {user.dong} 기준 · 상품 {len(results)}개")

    def open_selected(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("동네 장터", "목록에서 상품을 선택하세요.", parent=self)
            return
        ItemDetailDialog(self, self.main, selected[0])


class ItemDetailDialog(tk.Toplevel):
    """상품 상세 + 수량/수령방법 선택 + 주문, 찜, 신고."""

    def __init__(self, master, main, item_id):
        super().__init__(master)
        self.main = main
        self.store = main.store
        self.user = main.user
        self.item = self.store.items[item_id]
        item = self.item
        seller = self.store.users.get(item.seller_id)
        self.dist = distance_km(self.user.dong, item.dong)

        self.title(f"상품 상세 - {item.title}")
        self.resizable(False, False)
        self.transient(master)
        body = ttk.Frame(self, padding=22)
        body.pack(fill="both")

        ttk.Label(body, text=item.title, style="H2.TLabel", wraplength=380).grid(
            row=0, column=0, columnspan=2, sticky="w")
        tag = "🥕 못난이 손질 상품" if item.item_type == "못난이손질" else "⏰ 소비기한 임박 상품"
        ttk.Label(body, text=tag, foreground=GREEN).grid(row=1, column=0, columnspan=2,
                                                          sticky="w", pady=(0, 10))
        extra = item.extra_discount_rate()
        price_text = f"{won(item.current_price())}  (정가 {won(item.original_price)}, {item.discount_rate()}% 할인)"
        if extra:
            price_text += f"\n  └ 마감 임박 자동 추가할인 {int(extra * 100)}% 적용"
        info = [
            ("가격", price_text),
            ("소비기한", f"{item.expire_date}  ({item.d_day_text()})"),
            ("분류", item.category),
            ("남은 수량", f"{item.quantity}개  (1개당 {item.weight_g}g)"),
            ("판매자", f"{seller.display_name if seller else '-'} · {item.dong} ({self.dist:.1f}km)"),
            ("설명", item.description or "-"),
        ]
        for r, (k, v) in enumerate(info, start=2):
            ttk.Label(body, text=k, style="Sub.TLabel").grid(row=r, column=0, sticky="nw", pady=3, padx=(0, 14))
            ttk.Label(body, text=v, wraplength=330, justify="left").grid(row=r, column=1, sticky="w", pady=3)

        ttk.Separator(body).grid(row=8, column=0, columnspan=2, sticky="ew", pady=12)

        # ---- 주문 옵션 ----
        self.qty = tk.IntVar(value=1)
        self.method = tk.StringVar(value="픽업")
        ttk.Label(body, text="수량").grid(row=9, column=0, sticky="w")
        ttk.Spinbox(body, from_=1, to=item.quantity, textvariable=self.qty, width=6,
                    command=self.update_total, state="readonly").grid(row=9, column=1, sticky="w")
        ttk.Label(body, text="수령 방법").grid(row=10, column=0, sticky="w", pady=6)
        methods = ttk.Frame(body)
        methods.grid(row=10, column=1, sticky="w")
        ttk.Radiobutton(methods, text="직접 픽업 (무료)", value="픽업", variable=self.method,
                        command=self.update_total).pack(side="left")
        can_deliver = self.dist <= MAX_DELIVERY_KM
        ttk.Radiobutton(methods, text="근거리 배달" if can_deliver else f"배달 불가({MAX_DELIVERY_KM:g}km 초과)",
                        value="배달", variable=self.method, command=self.update_total,
                        state="normal" if can_deliver else "disabled").pack(side="left", padx=10)
        self.total_label = ttk.Label(body, text="", font=("맑은 고딕", 12, "bold"), foreground=ORANGE)
        self.total_label.grid(row=11, column=0, columnspan=2, sticky="w", pady=(8, 12))

        # ---- 버튼 ----
        buttons = ttk.Frame(body)
        buttons.grid(row=12, column=0, columnspan=2, sticky="ew")
        self.fav_btn = ttk.Button(buttons, command=self.toggle_fav)
        self.fav_btn.pack(side="left")
        ttk.Button(buttons, text="🚨 신고", command=self.report).pack(side="left", padx=6)
        ttk.Button(buttons, text="주문하기", style="Accent.TButton", command=self.order).pack(side="right")
        ttk.Button(buttons, text="닫기", command=self.destroy).pack(side="right", padx=6)

        self._update_fav_text()
        self.update_total()
        self.grab_set()

    def update_total(self) -> None:
        try:
            subtotal, fee, total = self.store.quote(self.user, self.item, self.qty.get(), self.method.get())
        except (ValueError, tk.TclError) as e:
            self.total_label.config(text=str(e))
            return
        fee_text = "무료" if fee == 0 else won(fee)
        self.total_label.config(text=f"결제 예정: {won(total)}  (상품 {won(subtotal)} + 배달비 {fee_text})")

    def _update_fav_text(self) -> None:
        on = self.item.item_id in self.user.favorites
        self.fav_btn.config(text="♥ 찜 해제" if on else "♡ 찜하기")

    def toggle_fav(self) -> None:
        self.store.toggle_favorite(self.user, self.item.item_id)
        self._update_fav_text()
        self.main.market.refresh()

    def report(self) -> None:
        if not messagebox.askyesno("신고", "상태가 의심되거나 판매 금지 품목인가요?\n이 상품을 신고합니다.", parent=self):
            return
        hidden = self.store.report_item(self.user, self.item.item_id)
        msg = "신고가 누적되어 상품이 숨김 처리되었습니다." if hidden else "신고가 접수되었습니다."
        messagebox.showinfo("신고", msg, parent=self)
        self.main.market.refresh()
        if hidden:
            self.destroy()

    def order(self) -> None:
        qty, method = self.qty.get(), self.method.get()
        try:
            _, _, total = self.store.quote(self.user, self.item, qty, method)
            if not messagebox.askyesno("주문 확인", f"{self.item.title} {qty}개\n{method} · {won(total)}\n주문할까요?",
                                       parent=self):
                return
            order = self.store.place_order(self.user, self.item.item_id, qty, method)
        except ValueError as e:
            messagebox.showerror("주문 실패", str(e), parent=self)
            return
        guide = (f"판매자 위치({self.item.dong})에서 직접 받아가세요." if method == "픽업"
                 else "근거리 배달로 보내드릴게요.")
        messagebox.showinfo("주문 완료", f"주문번호 {order.order_id}\n{won(order.saved_money)} 절약했어요! 🌱\n{guide}",
                            parent=self)
        self.main.refresh_all()
        self.destroy()
