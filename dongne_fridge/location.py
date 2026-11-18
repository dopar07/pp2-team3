# ============================================================
# [AI 사용 표기]
# - AI 종류    : Claude Opus 5.5 (Anthropic, Claude Code)
# - 사용 목적  : 동네 좌표 테이블, 거리 계산(하버사인 공식), 배달비 계산 함수 작성
# - 프롬프트   : "ppt보고 만들어줘 파이썬으로 만드는것이 목표야"
#                (팀프로젝트 요구서 PDF + 동네냉장고 아이디어 제공)
# - 사용한 사람: 이찬민
# - 날짜       : 2026-11-07
# - 범위       : 이 파일 전체 (AI 생성 후 팀원 검토/수정 필요)
# ============================================================
"""동네 위치와 거리 계산.

지도 API 없이도 동작하도록 청주시 주요 동의 '대략적인' 중심 좌표를 사용한다.
(선택 과제로 카카오/네이버 지도 API를 붙이면 이 파일만 바꾸면 된다.)
"""

import math

# dict[동 이름] = (위도, 경도) tuple
NEIGHBORHOODS = {
    "모충동": (36.6250, 127.4710),
    "사창동": (36.6335, 127.4590),
    "개신동": (36.6245, 127.4560),
    "복대동": (36.6410, 127.4430),
    "가경동": (36.6280, 127.4310),
    "봉명동": (36.6430, 127.4600),
    "성안동": (36.6360, 127.4880),
    "율량동": (36.6640, 127.4930),
    "용암동": (36.6050, 127.5070),
    "분평동": (36.6090, 127.4800),
    "수곡동": (36.6160, 127.4760),
    "산남동": (36.6080, 127.4630),
}
DONG_NAMES = tuple(NEIGHBORHOODS)

# 배달 정책
MAX_DELIVERY_KM = 3.0        # 배달 가능 최대 거리
DELIVERY_BASE_FEE = 1000     # 기본 배달비
DELIVERY_FEE_PER_KM = 500    # 1km당 추가
FREE_DELIVERY_MIN = 20000    # 이 금액 이상 주문 시 무료 배달

EARTH_RADIUS_KM = 6371.0


def distance_km(dong_a: str, dong_b: str) -> float:
    """두 동 사이의 직선거리(km) - 하버사인 공식."""
    lat1, lon1 = NEIGHBORHOODS[dong_a]
    lat2, lon2 = NEIGHBORHOODS[dong_b]
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def offset_km(center: str, target: str) -> tuple[float, float]:
    """center 동을 원점으로 한 target 동의 (동쪽 km, 북쪽 km). 지도 그리기용."""
    lat0, lon0 = NEIGHBORHOODS[center]
    lat1, lon1 = NEIGHBORHOODS[target]
    dx = (lon1 - lon0) * 111.0 * math.cos(math.radians(lat0))
    dy = (lat1 - lat0) * 111.0
    return dx, dy


def delivery_fee(dist_km: float, subtotal: int) -> int:
    """배달비: 기본 1,000원 + km당 500원(올림). 2만원 이상이면 무료."""
    if subtotal >= FREE_DELIVERY_MIN:
        return 0
    return DELIVERY_BASE_FEE + math.ceil(dist_km) * DELIVERY_FEE_PER_KM
