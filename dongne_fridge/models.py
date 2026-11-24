# ============================================================
# [AI 사용 표기]
# - AI 종류    : Claude Opus 5.5 (Anthropic, Claude Code)
# - 사용 목적  : 데이터 모델 클래스(User, Item, Order) 초안 작성
# - 프롬프트   : "ppt보고 만들어줘 파이썬으로 만드는것이 목표야"
#                (팀프로젝트 요구서 PDF + 동네냉장고 아이디어 제공)
# - 사용한 사람: 이찬민
# - 날짜       : 2026-11-07
# - 범위       : 이 파일 전체 (AI 생성 후 팀원 검토/수정 필요)
# ============================================================
"""동네냉장고 데이터 모델: 회원(User), 상품(Item), 주문(Order)."""

import hashlib
from dataclasses import dataclass, field
from datetime import date, datetime

# ---- 상수 (tuple: 바뀌지 않는 선택지 목록) ----
CATEGORIES = ("채소", "과일", "정육", "수산", "유제품", "베이커리", "반찬/도시락", "가공식품", "기타")
USER_TYPES = ("개인", "마트", "식당", "농가")
ITEM_TYPES = ("임박상품", "못난이손질")
ITEM_STATUSES = ("판매중", "판매완료", "판매중지", "신고숨김")

REPORT_LIMIT = 3      # 신고가 이 횟수 이상이면 자동 숨김
CO2_PER_KG = 2.5      # 음식물 1kg 폐기 시 온실가스(kg CO2e) - 발표용 추정치


def hash_password(password: str) -> str:
    """비밀번호를 그대로 저장하지 않고 SHA-256 해시로 저장한다."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def won(amount: int) -> str:
    """12000 -> '12,000원'"""
    return f"{amount:,}원"


@dataclass
class User:
    user_id: str
    password_hash: str
    name: str
    user_type: str          # 개인 / 마트 / 식당 / 농가
    dong: str               # 거주(영업) 동네
    favorites: set = field(default_factory=set)   # 찜한 상품 ID (set: 중복 없음)

    def check_password(self, password: str) -> bool:
        return self.password_hash == hash_password(password)

    @property
    def display_name(self) -> str:
        return f"{self.name}({self.user_type})"

    def toggle_favorite(self, item_id: str) -> bool:
        """찜 추가/해제. 추가되면 True."""
        if item_id in self.favorites:
            self.favorites.remove(item_id)
            return False
        self.favorites.add(item_id)
        return True

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "password_hash": self.password_hash,
            "name": self.name,
            "user_type": self.user_type,
            "dong": self.dong,
            "favorites": sorted(self.favorites),   # JSON은 set을 저장 못 해서 list로 변환
        }

    @classmethod
    def from_dict(cls, d: dict) -> "User":
        return cls(d["user_id"], d["password_hash"], d["name"], d["user_type"],
                   d["dong"], set(d.get("favorites", [])))


@dataclass
class Item:
    item_id: str
    seller_id: str
    title: str
    category: str
    item_type: str          # 임박상품 / 못난이손질
    original_price: int     # 정가
    price: int              # 판매자가 정한 판매가
    quantity: int
    weight_g: int           # 1개당 무게(g) - 음식물쓰레기 감축량 계산용
    expire_date: str        # 소비기한 "YYYY-MM-DD"
    dong: str
    description: str = ""
    status: str = "판매중"
    created_at: str = field(default_factory=now_text)
    reporters: set = field(default_factory=set)   # 신고한 사용자 ID

    def days_left(self, today: date | None = None) -> int:
        today = today or date.today()
        return (date.fromisoformat(self.expire_date) - today).days

    def d_day_text(self) -> str:
        d = self.days_left()
        if d < 0:
            return "기한지남"
        return "D-day" if d == 0 else f"D-{d}"

    def extra_discount_rate(self) -> float:
        """마감 임박 자동 추가 할인: 당일 20%, 하루 전 10%."""
        d = self.days_left()
        if d <= 0:
            return 0.2
        if d == 1:
            return 0.1
        return 0.0

    def current_price(self) -> int:
        """자동 할인을 반영한 현재 판매가 (10원 단위 내림)."""
        return int(self.price * (1 - self.extra_discount_rate())) // 10 * 10

    def discount_rate(self) -> int:
        """정가 대비 할인율(%)."""
        if self.original_price <= 0:
            return 0
        return round((1 - self.current_price() / self.original_price) * 100)

    def is_available(self) -> bool:
        return self.status == "판매중" and self.quantity > 0 and self.days_left() >= 0

    def add_report(self, user_id: str) -> bool:
        """신고 추가. 같은 사람이 여러 번 신고해도 1번으로 센다(set). 숨김 처리되면 True."""
        self.reporters.add(user_id)
        if len(self.reporters) >= REPORT_LIMIT:
            self.status = "신고숨김"
            return True
        return False

    def to_dict(self) -> dict:
        d = dict(self.__dict__)
        d["reporters"] = sorted(self.reporters)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Item":
        d = dict(d)
        d["reporters"] = set(d.get("reporters", []))
        return cls(**d)


@dataclass
class Order:
    order_id: str
    item_id: str
    item_title: str
    category: str
    buyer_id: str
    seller_id: str
    quantity: int
    unit_price: int             # 실제 결제 단가
    original_unit_price: int    # 정가 단가 (절약 금액 계산용)
    weight_g: int               # 총 무게
    method: str                 # 픽업 / 배달
    delivery_fee: int
    created_at: str = field(default_factory=now_text)
    status: str = "주문완료"     # 주문완료 / 거래완료 / 주문취소

    @property
    def subtotal(self) -> int:
        return self.unit_price * self.quantity

    @property
    def total(self) -> int:
        return self.subtotal + self.delivery_fee

    @property
    def saved_money(self) -> int:
        return (self.original_unit_price - self.unit_price) * self.quantity

    def to_dict(self) -> dict:
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, d: dict) -> "Order":
        return cls(**d)
