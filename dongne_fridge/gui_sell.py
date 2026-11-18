# ============================================================
# [AI 사용 표기]
# - AI 종류    : Claude Opus 5.5 (Anthropic, Claude Code)
# - 사용 목적  : 상품 등록 폼 탭, 내 판매 관리(상품 상태 변경·받은 주문 처리) 탭 작성
# - 프롬프트   : "ppt보고 만들어줘 파이썬으로 만드는것이 목표야"
#                (팀프로젝트 요구서 PDF + 동네냉장고 아이디어 제공)
# - 사용한 사람: 이찬민
# - 날짜       : 2026-11-07
# - 범위       : 이 파일 전체 (AI 생성 후 팀원 검토/수정 필요)
# ============================================================
"""판매자 기능: 상품 등록 탭 + 내 판매 관리 탭."""

import tkinter as tk
from datetime import date, timedelta
from tkinter import messagebox, ttk

from gui_market import build_tree
from models import CATEGORIES, ITEM_TYPES, won


class SellTab(ttk.Frame):
    def __init__(self, master, main):
        super().__init__(master, padding=20)
        self.main = main
        self.vars = {
            "title": tk.StringVar(),
            "category": tk.StringVar(value=CATEGORIES[0]),
            "item_type": tk.StringVar(value=ITEM_TYPES[0]),
            "original_price": tk.StringVar(),
            "price": tk.StringVar(),
            "quantity": tk.StringVar(value="1"),
            "weight_g": tk.StringVar(value="500"),
            "expire_date": tk.StringVar(),
        }
        form = ttk.Frame(self)
        form.pack(anchor="nw")
        ttk.Label(form, text="소비기한 임박 / 못난이 손질 상품 등록", style="H2.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 14))

        fields = [
            ("상품명", ttk.Entry(form, textvariable=self.vars["title"], width=36), "예) 우유 1L, 못난이 감자 깍둑썰기"),
            ("분류", ttk.Combobox(form, textvariable=self.vars["category"], values=CATEGORIES,
                                state="readonly", width=34), ""),
            ("종류", ttk.Combobox(form, textvariable=self.vars["item_type"], values=ITEM_TYPES,
                                state="readonly", width=34), "못난이손질: 외관이 못난 농산물을 손질·소분한 상품"),
            ("정가 (원)", ttk.Entry(form, textvariable=self.vars["original_price"], width=36), ""),
            ("판매가 (원)", ttk.Entry(form, textvariable=self.vars["price"], width=36), ""),
            ("수량 (개)", ttk.Entry(form, textvariable=self.vars["quantity"], width=36), ""),
            ("1개당 무게 (g)", ttk.Entry(form, textvariable=self.vars["weight_g"], width=36),
             "음식물쓰레기 감축량 계산에 사용"),
            ("소비기한", ttk.Entry(form, textvariable=self.vars["expire_date"], width=36),
             "YYYY-MM-DD, 오늘부터 30일 이내"),
        ]
        for r, (label, widget, hint) in enumerate(fields, start=1):
            ttk.Label(form, text=label).grid(row=r, column=0, sticky="w", pady=5, padx=(0, 14))
            widget.grid(row=r, column=1, sticky="w", pady=5)
            ttk.Label(form, text=hint, style="Sub.TLabel").grid(row=r, column=2, sticky="w", padx=10)

        r = len(fields) + 1
        ttk.Label(form, text="설명").grid(row=r, column=0, sticky="nw", pady=5)
        self.desc = tk.Text(form, width=50, height=4, relief="solid", borderwidth=1)
        self.desc.grid(row=r, column=1, columnspan=2, sticky="w", pady=5)

        self.preview = ttk.Label(form, text="", foreground="#ef6c00", font=("맑은 고딕", 11, "bold"))
        self.preview.grid(row=r + 1, column=1, columnspan=2, sticky="w", pady=(6, 4))
        for key in ("original_price", "price"):
            self.vars[key].trace_add("write", lambda *a: self.update_preview())

        btns = ttk.Frame(form)
        btns.grid(row=r + 2, column=1, sticky="w", pady=10)
        ttk.Button(btns, text="등록하기", style="Accent.TButton", command=self.submit).pack(side="left")
        ttk.Button(btns, text="초기화", command=self.reset).pack(side="left", padx=8)

        ttk.Label(self, text="※ 판매 금지: 개봉한 음식, 소비기한 지난 식품, 주류·건강기능식품, 직접 만든 음식(개인)\n"
                             "※ 소비기한 하루 전 10%, 당일 20%가 자동으로 추가 할인됩니다.",
                  style="Sub.TLabel", justify="left").pack(anchor="w", pady=(16, 0))
        self.reset()

    def update_preview(self) -> None:
        try:
            orig = int(self.vars["original_price"].get())
            price = int(self.vars["price"].get())
            self.preview.config(text=f"할인율 {round((1 - price / orig) * 100)}%" if orig > 0 else "")
        except ValueError:
            self.preview.config(text="")

    def reset(self) -> None:
        for key in ("title", "original_price", "price"):
            self.vars[key].set("")
        self.vars["quantity"].set("1")
        self.vars["weight_g"].set("500")
        self.vars["expire_date"].set((date.today() + timedelta(days=2)).isoformat())
        self.desc.delete("1.0", "end")

    def refresh(self) -> None:
        pass     # 등록 폼은 새로고침할 내용이 없음

    def submit(self) -> None:
        v = {k: var.get() for k, var in self.vars.items()}
        try:
            numbers = {k: int(v[k].replace(",", "")) for k in ("original_price", "price", "quantity", "weight_g")}
        except ValueError:
            messagebox.showerror("상품 등록", "가격·수량·무게는 숫자로 입력하세요.", parent=self)
            return
        try:
            item = self.main.store.add_item(
                self.main.user, v["title"], v["category"], v["item_type"],
                numbers["original_price"], numbers["price"], numbers["quantity"],
                numbers["weight_g"], v["expire_date"], self.desc.get("1.0", "end"))
        except ValueError as e:
            messagebox.showerror("상품 등록", str(e), parent=self)
            return
        messagebox.showinfo("상품 등록", f"'{item.title}' 등록 완료!\n{item.dong} 주변 이웃에게 노출됩니다.", parent=self)
        self.reset()
        self.main.refresh_all()


class MySalesTab(ttk.Frame):
    ITEM_COLUMNS = (("title", "상품명", 240), ("type", "종류", 85), ("price", "현재가", 85),
                    ("dday", "소비기한", 80), ("qty", "남은수량", 70), ("status", "상태", 80),
                    ("reports", "신고", 50))
    ORDER_COLUMNS = (("order_id", "주문번호", 80), ("title", "상품명", 230), ("buyer", "구매자", 120),
                     ("qty", "수량", 55), ("total", "결제금액", 90), ("method", "수령", 60),
                     ("created", "주문일시", 130), ("status", "상태", 80))

    def __init__(self, master, main):
        super().__init__(master, padding=10)
        self.main = main

        ttk.Label(self, text="내가 등록한 상품", style="H2.TLabel").pack(anchor="w")
        top = ttk.Frame(self)
        top.pack(fill="both", expand=True, pady=(4, 0))
        self.item_tree = build_tree(top, self.ITEM_COLUMNS, height=8)
        b1 = ttk.Frame(self)
        b1.pack(fill="x", pady=6)
        ttk.Button(b1, text="판매 중지 / 재개", command=self.toggle_status).pack(side="left")
        ttk.Button(b1, text="삭제", command=self.delete_item).pack(side="left", padx=6)
        self.summary = ttk.Label(b1, text="", style="Sub.TLabel")
        self.summary.pack(side="right")

        # 하단 버튼을 먼저 bottom에 배치해야 목록이 늘어나도 버튼이 가려지지 않는다
        b2 = ttk.Frame(self)
        b2.pack(side="bottom", fill="x", pady=6)
        ttk.Button(b2, text="거래 완료 처리 (픽업·배달 완료)", style="Accent.TButton",
                   command=self.complete_order).pack(side="left")
        ttk.Label(self, text="받은 주문", style="H2.TLabel").pack(anchor="w", pady=(10, 0))
        bottom = ttk.Frame(self)
        bottom.pack(fill="both", expand=True, pady=(4, 0))
        self.order_tree = build_tree(bottom, self.ORDER_COLUMNS, height=8)
        self.refresh()

    def refresh(self) -> None:
        store, user = self.main.store, self.main.user
        self.item_tree.delete(*self.item_tree.get_children())
        for i in store.items_of_seller(user.user_id):
            self.item_tree.insert("", "end", iid=i.item_id, values=(
                i.title, i.item_type, won(i.current_price()), i.d_day_text(),
                i.quantity, i.status, len(i.reporters)))
        self.order_tree.delete(*self.order_tree.get_children())
        for o in store.orders_of_seller(user.user_id):
            buyer = store.users.get(o.buyer_id)
            self.order_tree.insert("", "end", iid=o.order_id, values=(
                o.order_id, o.item_title, buyer.name if buyer else "-", o.quantity,
                won(o.total), o.method, o.created_at, o.status))
        s = store.stats(user.user_id)
        self.summary.config(text=f"누적 판매 {s['sold_count']}건 · 매출 {won(s['sales_amount'])} · "
                                 f"폐기 막은 식재료 {s['sold_kg']:.1f}kg")

    def _selected(self, tree, what):
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("내 판매 관리", f"{what}을(를) 선택하세요.", parent=self)
            return None
        return sel[0]

    def toggle_status(self) -> None:
        item_id = self._selected(self.item_tree, "상품")
        if not item_id:
            return
        item = self.main.store.items[item_id]
        if item.status == "판매중":
            self.main.store.set_item_status(item_id, "판매중지")
        elif item.status == "판매중지" and item.quantity > 0:
            self.main.store.set_item_status(item_id, "판매중")
        else:
            messagebox.showinfo("내 판매 관리", f"'{item.status}' 상태에서는 변경할 수 없습니다.", parent=self)
            return
        self.main.refresh_all()

    def delete_item(self) -> None:
        item_id = self._selected(self.item_tree, "상품")
        if item_id and messagebox.askyesno("삭제", "이 상품을 삭제할까요?", parent=self):
            self.main.store.delete_item(item_id)
            self.main.refresh_all()

    def complete_order(self) -> None:
        order_id = self._selected(self.order_tree, "주문")
        if not order_id:
            return
        try:
            self.main.store.complete_order(self.main.user, order_id)
        except ValueError as e:
            messagebox.showerror("내 판매 관리", str(e), parent=self)
            return
        self.refresh()
