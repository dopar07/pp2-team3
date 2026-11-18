# ============================================================
# [AI 사용 표기]
# - AI 종류    : Claude Opus 5.5 (Anthropic, Claude Code)
# - 사용 목적  : JSON 파일 저장/불러오기, 회원·상품·주문 처리 로직, CSV 내보내기, 샘플 데이터 작성
# - 프롬프트   : "ppt보고 만들어줘 파이썬으로 만드는것이 목표야"
#                (팀프로젝트 요구서 PDF + 동네냉장고 아이디어 제공)
# - 사용한 사람: 이찬민
# - 날짜       : 2026-11-07
# - 범위       : 이 파일 전체 (AI 생성 후 팀원 검토/수정 필요)
# ============================================================
"""DataStore: 프로그램의 모든 데이터를 관리하고 JSON 파일로 저장한다.

data/users.json  : 회원 목록
data/items.json  : 상품 목록
data/orders.json : 주문 목록
"""

import csv
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from location import DONG_NAMES, MAX_DELIVERY_KM, delivery_fee, distance_km
from models import (CATEGORIES, CO2_PER_KG, ITEM_TYPES, USER_TYPES, Item, Order,
                    User, hash_password)

# 정렬 기준: dict[이름] = 정렬 키 함수.  (item, 거리) tuple을 받는다.
SORT_OPTIONS = {
    "소비기한 임박순": lambda pair: (pair[0].days_left(), pair[1]),
    "할인율 높은순": lambda pair: -pair[0].discount_rate(),
    "가까운순": lambda pair: pair[1],
    "낮은 가격순": lambda pair: pair[0].current_price(),
}


class DataStore:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.users: dict[str, User] = {}
        self.items: dict[str, Item] = {}
        self.orders: list[Order] = []
        self.load()
        if not self.users:          # 첫 실행이면 시연용 샘플 데이터 생성
            self._seed()
            self.save_all()

    # ------------------------------------------------------------------
    # 파일 입출력
    # ------------------------------------------------------------------
    def _path(self, name: str) -> Path:
        return self.data_dir / f"{name}.json"

    def _read(self, name: str) -> list:
        path = self._path(name)
        if not path.exists():
            return []
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            # 파일이 깨졌으면 지우지 않고 백업해 둔다
            path.replace(path.with_suffix(".broken.json"))
            return []

    def _write(self, name: str, rows: list) -> None:
        path = self._path(name)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)       # 쓰는 도중 꺼져도 원본이 깨지지 않도록

    def load(self) -> None:
        self.users = {d["user_id"]: User.from_dict(d) for d in self._read("users")}
        self.items = {d["item_id"]: Item.from_dict(d) for d in self._read("items")}
        self.orders = [Order.from_dict(d) for d in self._read("orders")]

    def save_users(self) -> None:
        self._write("users", [u.to_dict() for u in self.users.values()])

    def save_items(self) -> None:
        self._write("items", [i.to_dict() for i in self.items.values()])

    def save_orders(self) -> None:
        self._write("orders", [o.to_dict() for o in self.orders])

    def save_all(self) -> None:
        self.save_users()
        self.save_items()
        self.save_orders()

    @staticmethod
    def _next_id(prefix: str, existing) -> str:
        nums = [int(k[len(prefix):]) for k in existing if k[len(prefix):].isdigit()]
        return f"{prefix}{max(nums, default=0) + 1:04d}"

    # ------------------------------------------------------------------
    # 회원
    # ------------------------------------------------------------------
    def register_user(self, user_id, password, name, user_type, dong) -> User:
        user_id = user_id.strip()
        name = name.strip()
        if len(user_id) < 3 or not user_id.isalnum():
            raise ValueError("아이디는 영문/숫자 3자 이상이어야 합니다.")
        if user_id in self.users:
            raise ValueError("이미 사용 중인 아이디입니다.")
        if len(password) < 4:
            raise ValueError("비밀번호는 4자 이상이어야 합니다.")
        if not name:
            raise ValueError("이름(상호명)을 입력하세요.")
        if user_type not in USER_TYPES:
            raise ValueError("회원 유형을 선택하세요.")
        if dong not in DONG_NAMES:
            raise ValueError("동네를 선택하세요.")
        user = User(user_id, hash_password(password), name, user_type, dong)
        self.users[user_id] = user
        self.save_users()
        return user

    def login(self, user_id, password) -> User | None:
        user = self.users.get(user_id.strip())
        if user and user.check_password(password):
            return user
        return None

    def change_dong(self, user: User, dong: str) -> None:
        if dong in DONG_NAMES:
            user.dong = dong
            self.save_users()

    def toggle_favorite(self, user: User, item_id: str) -> bool:
        added = user.toggle_favorite(item_id)
        self.save_users()
        return added

    # ------------------------------------------------------------------
    # 상품
    # ------------------------------------------------------------------
    def add_item(self, seller: User, title, category, item_type, original_price,
                 price, quantity, weight_g, expire_date, description="") -> Item:
        title = title.strip()
        if not title:
            raise ValueError("상품명을 입력하세요.")
        if category not in CATEGORIES or item_type not in ITEM_TYPES:
            raise ValueError("분류/종류를 선택하세요.")
        if original_price <= 0 or price <= 0:
            raise ValueError("가격은 0보다 커야 합니다.")
        if price > original_price:
            raise ValueError("판매가는 정가보다 클 수 없습니다.")
        if quantity <= 0 or weight_g <= 0:
            raise ValueError("수량과 무게는 1 이상이어야 합니다.")
        try:
            exp = date.fromisoformat(expire_date.strip())
        except ValueError:
            raise ValueError("소비기한은 2026-11-10 형식으로 입력하세요.") from None
        if exp < date.today():
            raise ValueError("이미 소비기한이 지난 상품은 등록할 수 없습니다.")
        if exp > date.today() + timedelta(days=30):
            raise ValueError("소비기한이 30일 이내인 임박 상품만 등록할 수 있습니다.")

        item = Item(self._next_id("I", self.items), seller.user_id, title, category,
                    item_type, original_price, price, quantity, weight_g,
                    exp.isoformat(), seller.dong, description.strip())
        self.items[item.item_id] = item
        self.save_items()
        return item

    def search_items(self, viewer: User, keyword="", category="전체", item_type="전체",
                     radius_km=None, sort_by="소비기한 임박순", only_favorites=False):
        """조건에 맞는 판매중 상품을 [(item, 거리km), ...] 형태로 돌려준다."""
        keyword = keyword.strip().lower()
        results = []
        for item in self.items.values():
            if not item.is_available() or item.seller_id == viewer.user_id:
                continue
            if category != "전체" and item.category != category:
                continue
            if item_type != "전체" and item.item_type != item_type:
                continue
            if only_favorites and item.item_id not in viewer.favorites:
                continue
            if keyword and keyword not in (item.title + " " + item.description).lower():
                continue
            dist = distance_km(viewer.dong, item.dong)
            if radius_km is not None and dist > radius_km:
                continue
            results.append((item, dist))
        results.sort(key=SORT_OPTIONS.get(sort_by, SORT_OPTIONS["소비기한 임박순"]))
        return results

    def items_of_seller(self, seller_id: str) -> list[Item]:
        mine = [i for i in self.items.values() if i.seller_id == seller_id]
        return sorted(mine, key=lambda i: i.created_at, reverse=True)

    def set_item_status(self, item_id: str, status: str) -> None:
        self.items[item_id].status = status
        self.save_items()

    def delete_item(self, item_id: str) -> None:
        self.items.pop(item_id, None)
        for user in self.users.values():
            user.favorites.discard(item_id)
        self.save_items()
        self.save_users()

    def report_item(self, reporter: User, item_id: str) -> bool:
        hidden = self.items[item_id].add_report(reporter.user_id)
        self.save_items()
        return hidden

    # ------------------------------------------------------------------
    # 주문
    # ------------------------------------------------------------------
    def quote(self, buyer: User, item: Item, qty: int, method: str) -> tuple[int, int, int]:
        """(상품금액, 배달비, 총액) 계산. 배달 불가면 ValueError."""
        subtotal = item.current_price() * qty
        fee = 0
        if method == "배달":
            dist = distance_km(buyer.dong, item.dong)
            if dist > MAX_DELIVERY_KM:
                raise ValueError(f"배달은 {MAX_DELIVERY_KM:g}km 이내만 가능합니다. (현재 {dist:.1f}km)")
            fee = delivery_fee(dist, subtotal)
        return subtotal, fee, subtotal + fee

    def place_order(self, buyer: User, item_id: str, qty: int, method: str) -> Order:
        item = self.items.get(item_id)
        if item is None or not item.is_available():
            raise ValueError("이미 판매가 끝난 상품입니다.")
        if item.seller_id == buyer.user_id:
            raise ValueError("본인 상품은 구매할 수 없습니다.")
        if not 1 <= qty <= item.quantity:
            raise ValueError(f"구매 수량은 1~{item.quantity}개 사이여야 합니다.")
        _, fee, _ = self.quote(buyer, item, qty, method)

        order = Order(self._next_id("O", [o.order_id for o in self.orders]),
                      item.item_id, item.title, item.category, buyer.user_id,
                      item.seller_id, qty, item.current_price(), item.original_price,
                      item.weight_g * qty, method, fee)
        item.quantity -= qty
        if item.quantity == 0:
            item.status = "판매완료"
        self.orders.append(order)
        self.save_items()
        self.save_orders()
        return order

    def _find_order(self, order_id: str) -> Order:
        for order in self.orders:
            if order.order_id == order_id:
                return order
        raise ValueError("주문을 찾을 수 없습니다.")

    def cancel_order(self, user: User, order_id: str) -> None:
        order = self._find_order(order_id)
        if order.buyer_id != user.user_id:
            raise ValueError("본인 주문만 취소할 수 있습니다.")
        if order.status != "주문완료":
            raise ValueError("이미 거래가 끝났거나 취소된 주문입니다.")
        order.status = "주문취소"
        item = self.items.get(order.item_id)
        if item:                             # 재고 복구
            item.quantity += order.quantity
            if item.status == "판매완료":
                item.status = "판매중"
        self.save_items()
        self.save_orders()

    def complete_order(self, seller: User, order_id: str) -> None:
        order = self._find_order(order_id)
        if order.seller_id != seller.user_id:
            raise ValueError("본인이 판매한 주문만 처리할 수 있습니다.")
        if order.status != "주문완료":
            raise ValueError("이미 처리된 주문입니다.")
        order.status = "거래완료"
        self.save_orders()

    def orders_of_buyer(self, user_id: str) -> list[Order]:
        return [o for o in reversed(self.orders) if o.buyer_id == user_id]

    def orders_of_seller(self, user_id: str) -> list[Order]:
        return [o for o in reversed(self.orders) if o.seller_id == user_id]

    # ------------------------------------------------------------------
    # 통계 / 내보내기
    # ------------------------------------------------------------------
    def stats(self, user_id: str) -> dict:
        """구매자 기준 절약 금액, 구한 식재료 무게, 카테고리별 무게."""
        valid = [o for o in self.orders_of_buyer(user_id) if o.status != "주문취소"]
        by_category = defaultdict(int)
        for o in valid:
            by_category[o.category] += o.weight_g
        kg = sum(o.weight_g for o in valid) / 1000
        sold = [o for o in self.orders_of_seller(user_id) if o.status != "주문취소"]
        return {
            "order_count": len(valid),
            "saved_money": sum(o.saved_money for o in valid),
            "saved_kg": kg,
            "co2_kg": kg * CO2_PER_KG,
            "by_category": dict(by_category),
            "sold_count": len(sold),
            "sold_kg": sum(o.weight_g for o in sold) / 1000,
            "sales_amount": sum(o.subtotal for o in sold),
        }

    def export_orders_csv(self, user_id: str, path) -> int:
        orders = self.orders_of_buyer(user_id)
        with open(path, "w", newline="", encoding="utf-8-sig") as f:   # 엑셀 한글 깨짐 방지
            writer = csv.writer(f)
            writer.writerow(["주문번호", "주문일시", "상품명", "분류", "수량", "단가",
                             "배달비", "총액", "절약금액", "수령방법", "상태"])
            for o in orders:
                writer.writerow([o.order_id, o.created_at, o.item_title, o.category,
                                 o.quantity, o.unit_price, o.delivery_fee, o.total,
                                 o.saved_money, o.method, o.status])
        return len(orders)

    # ------------------------------------------------------------------
    # 시연용 샘플 데이터
    # ------------------------------------------------------------------
    def _seed(self) -> None:
        users = [
            ("demo", "1234", "김동네", "개인", "모충동"),
            ("mart01", "1234", "모충 동네마트", "마트", "모충동"),
            ("food01", "1234", "사창 한식뷔페", "식당", "사창동"),
            ("bread01", "1234", "개신 동네빵집", "식당", "개신동"),
            ("farm01", "1234", "율량 햇살농장", "농가", "율량동"),
            ("user02", "1234", "이서연", "개인", "수곡동"),
            ("user03", "1234", "박민수", "개인", "분평동"),
        ]
        for uid, pw, name, utype, dong in users:
            self.users[uid] = User(uid, hash_password(pw), name, utype, dong)

        today = date.today()
        # (판매자, 상품명, 분류, 종류, 정가, 판매가, 수량, 무게g, 남은일수, 설명)
        samples = [
            ("mart01", "우유 1L", "유제품", "임박상품", 2980, 1500, 6, 1000, 1, "냉장 보관, 미개봉"),
            ("mart01", "두부 2입", "가공식품", "임박상품", 3200, 1600, 4, 600, 0, "오늘까지 소비 권장"),
            ("mart01", "닭가슴살 500g", "정육", "임박상품", 7900, 4500, 3, 500, 2, "냉장 보관"),
            ("mart01", "그릭요거트 4개입", "유제품", "임박상품", 6400, 3500, 5, 400, 3, ""),
            ("food01", "오늘의 반찬 3종 세트", "반찬/도시락", "임박상품", 9000, 4000, 5, 600, 0,
             "점심 영업 후 남은 반찬, 저녁 8시까지 픽업"),
            ("food01", "제육볶음 도시락", "반찬/도시락", "임박상품", 7000, 3500, 4, 450, 0, ""),
            ("bread01", "식빵·모닝빵 랜덤 박스", "베이커리", "임박상품", 8000, 3000, 6, 700, 1,
             "당일 생산, 마감 후 남은 빵"),
            ("bread01", "크루아상 3개", "베이커리", "임박상품", 7500, 3500, 3, 300, 1, ""),
            ("farm01", "못난이 감자 손질 (깍둑썰기)", "채소", "못난이손질", 5000, 2500, 8, 800, 4,
             "모양이 못생긴 감자를 껍질 벗겨 깍둑썰기, 바로 조리 가능"),
            ("farm01", "못난이 사과 슬라이스", "과일", "못난이손질", 6000, 3000, 6, 500, 3,
             "흠집 부분 제거 후 슬라이스, 갈변 방지 처리"),
            ("farm01", "못난이 당근·양파 볶음용 채소", "채소", "못난이손질", 4500, 2200, 10, 600, 5,
             "카레·볶음밥용으로 손질"),
            ("user02", "양배추 반통", "채소", "임박상품", 3000, 1000, 1, 1200, 2,
             "1인 가구라 다 못 먹어요. 퇴근 후 픽업 가능"),
            ("user02", "계란 10구 중 6개", "기타", "임박상품", 4000, 1500, 1, 360, 4, ""),
            ("user03", "냉동 만두 1봉 (미개봉)", "가공식품", "임박상품", 8900, 4000, 1, 1000, 6,
             "대용량 사서 남았어요"),
        ]
        for i, (seller, title, cat, itype, orig, price, qty, w, days, desc) in enumerate(samples, 1):
            item = Item(f"I{i:04d}", seller, title, cat, itype, orig, price, qty, w,
                        (today + timedelta(days=days)).isoformat(),
                        self.users[seller].dong, desc)
            self.items[item.item_id] = item
