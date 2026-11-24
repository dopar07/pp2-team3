# ============================================================
# [AI 사용 표기]
# - AI 종류    : Claude Opus 5.5 (Anthropic, Claude Code)
# - 사용 목적  : 로그인 화면 / 회원가입 창 GUI 작성
# - 프롬프트   : "ppt보고 만들어줘 파이썬으로 만드는것이 목표야"
#                (팀프로젝트 요구서 PDF + 동네냉장고 아이디어 제공)
# - 사용한 사람: 이찬민
# - 날짜       : 2026-11-07
# - 범위       : 이 파일 전체 (AI 생성 후 팀원 검토/수정 필요)
# ============================================================
"""로그인 화면과 회원가입 창."""

import tkinter as tk
from tkinter import messagebox, ttk

from location import DONG_NAMES
from models import USER_TYPES


class LoginFrame(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.id_var = tk.StringVar(value="demo")
        self.pw_var = tk.StringVar()

        card = ttk.Frame(self, padding=40)
        card.place(relx=0.5, rely=0.45, anchor="center")

        ttk.Label(card, text="🧊 동네냉장고", style="Title.TLabel").grid(row=0, column=0, columnspan=2)
        ttk.Label(card, text="버려질 식재료를 이웃과 저렴하게 나눠요",
                  style="Sub.TLabel").grid(row=1, column=0, columnspan=2, pady=(4, 24))

        ttk.Label(card, text="아이디").grid(row=2, column=0, sticky="w", pady=4)
        id_entry = ttk.Entry(card, textvariable=self.id_var, width=26)
        id_entry.grid(row=2, column=1, pady=4)
        ttk.Label(card, text="비밀번호").grid(row=3, column=0, sticky="w", pady=4)
        pw_entry = ttk.Entry(card, textvariable=self.pw_var, show="●", width=26)
        pw_entry.grid(row=3, column=1, pady=4)
        pw_entry.bind("<Return>", lambda e: self.login())

        ttk.Button(card, text="로그인", style="Accent.TButton",
                   command=self.login).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(16, 4))
        ttk.Button(card, text="회원가입",
                   command=lambda: SignupDialog(self, app)).grid(row=5, column=0, columnspan=2, sticky="ew")
        ttk.Label(card, text="시연용 계정: demo / 1234  (판매자: mart01 / 1234)",
                  style="Sub.TLabel").grid(row=6, column=0, columnspan=2, pady=(18, 0))
        pw_entry.focus_set()

    def login(self) -> None:
        user = self.app.store.login(self.id_var.get(), self.pw_var.get())
        if user is None:
            messagebox.showerror("로그인 실패", "아이디 또는 비밀번호가 올바르지 않습니다.", parent=self)
            return
        self.app.on_login(user)


class SignupDialog(tk.Toplevel):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.title("회원가입")
        self.resizable(False, False)
        self.transient(master)

        self.vars = {
            "user_id": tk.StringVar(),
            "password": tk.StringVar(),
            "password2": tk.StringVar(),
            "name": tk.StringVar(),
            "user_type": tk.StringVar(value=USER_TYPES[0]),
            "dong": tk.StringVar(value=DONG_NAMES[0]),
        }
        body = ttk.Frame(self, padding=24)
        body.pack()
        rows = [
            ("아이디 (영문/숫자)", ttk.Entry(body, textvariable=self.vars["user_id"], width=24)),
            ("비밀번호 (4자 이상)", ttk.Entry(body, textvariable=self.vars["password"], show="●", width=24)),
            ("비밀번호 확인", ttk.Entry(body, textvariable=self.vars["password2"], show="●", width=24)),
            ("이름 / 상호명", ttk.Entry(body, textvariable=self.vars["name"], width=24)),
            ("회원 유형", ttk.Combobox(body, textvariable=self.vars["user_type"],
                                     values=USER_TYPES, state="readonly", width=22)),
            ("우리 동네", ttk.Combobox(body, textvariable=self.vars["dong"],
                                     values=DONG_NAMES, state="readonly", width=22)),
        ]
        for r, (label, widget) in enumerate(rows):
            ttk.Label(body, text=label).grid(row=r, column=0, sticky="w", pady=4, padx=(0, 12))
            widget.grid(row=r, column=1, pady=4)
        ttk.Label(body, text="※ 마트·식당·농가는 사업자 회원으로 상품을 등록할 수 있어요.\n"
                             "   개인 회원도 미개봉 식재료를 올릴 수 있어요.",
                  style="Sub.TLabel").grid(row=len(rows), column=0, columnspan=2, pady=(8, 8), sticky="w")
        ttk.Button(body, text="가입하기", style="Accent.TButton",
                   command=self.submit).grid(row=len(rows) + 1, column=0, columnspan=2, sticky="ew")
        self.grab_set()

    def submit(self) -> None:
        v = {k: var.get() for k, var in self.vars.items()}
        if v["password"] != v["password2"]:
            messagebox.showerror("회원가입", "비밀번호가 서로 다릅니다.", parent=self)
            return
        try:
            self.app.store.register_user(v["user_id"], v["password"], v["name"],
                                         v["user_type"], v["dong"])
        except ValueError as e:
            messagebox.showerror("회원가입", str(e), parent=self)
            return
        messagebox.showinfo("회원가입", "가입이 완료되었습니다. 로그인해 주세요.", parent=self)
        self.destroy()
