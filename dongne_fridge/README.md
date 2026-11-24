# 🧊 동네냉장고

> 우리 동네 소비기한 임박 식재료 매칭 프로그램 (2026-2 프로그래밍 II 팀프로젝트, 3조)

동네 마트·식당·농가·개인이 소비기한이 임박한 식재료나 손질한 못난이 농산물을 올리면,
가까운 이웃이 싸게 사서 **픽업하거나 근거리 배달**로 받는 Python tkinter 데스크톱 프로그램입니다.

## 실행 방법

```bash
cd dongne_fridge
python main.py
```

- Python 3.10 이상이면 됩니다. 표준 라이브러리만 쓰기 때문에 따로 설치할 것이 없습니다.
- 처음 실행하면 `data/` 폴더에 시연용 샘플 데이터가 생깁니다. 데이터를 초기화하려면 `data/` 폴더를 지우세요.
- 시연용 계정 (비밀번호는 모두 `1234`)
  - `demo`: 개인 구매자 (모충동)
  - `mart01`: 마트, `food01`: 식당, `bread01`: 빵집, `farm01`: 농가 (못난이 손질 상품)
  - `user02`, `user03`: 개인 판매자

## 주요 기능 (기능표)

| 구분 | 기능 | 설명 | 파일 |
|---|---|---|---|
| 회원 | 회원가입 / 로그인 | 개인·마트·식당·농가 유형, 동네 선택, 비밀번호 SHA-256 해시 저장 | `gui_login.py`, `storage.py` |
| 장터 | 동네 상품 검색 | 키워드·분류·종류(임박/못난이) 필터, **반경(1/2/3/5km)** 필터 | `gui_market.py` |
| 장터 | 정렬 | 소비기한 임박순, 할인율순, 가까운순, 낮은 가격순 | `storage.py` (`SORT_OPTIONS`) |
| 장터 | 자동 추가 할인 | 소비기한 하루 전 10%, 당일 20% 자동 할인 | `models.py` (`Item.current_price`) |
| 주문 | 픽업 / 배달 주문 | 배달은 3km 이내, 기본 1,000원 + km당 500원, 2만원 이상 무료 | `location.py`, `storage.py` |
| 주문 | 찜 / 신고 | 찜 목록 필터, 신고 3회 누적 시 자동 숨김 | `gui_market.py`, `models.py` |
| 지도 | 동네 지도 | Canvas에 내 동네 중심 1·2·3km 원과 동네별 상품 수 표시, 클릭 시 목록 | `gui_map.py` |
| 판매 | 상품 등록 | 임박상품 / **못난이 손질** 상품 등록, 입력값 검증 | `gui_sell.py` |
| 판매 | 판매 관리 | 판매 중지·재개, 삭제, 받은 주문 거래완료 처리, 매출 요약 | `gui_sell.py` |
| 마이 | 환경 기여도 | 아낀 생활비, 구한 식재료 kg, 줄인 온실가스(추정), 분류별 막대그래프 | `gui_mypage.py` |
| 마이 | 주문 내역 | 주문 취소(재고 복구), **CSV 내보내기** | `gui_mypage.py`, `storage.py` |

## 요구사항 반영

| 요구 기술 | 사용한 곳 |
|---|---|
| GUI (tkinter) | 모든 `gui_*.py`: ttk Notebook, Treeview, Canvas, Toplevel 대화상자 |
| 파일 구조 | `data/*.json` (JSON 저장/불러오기), 주문 내역 CSV 내보내기 |
| 객체지향 (Class) | `User`, `Item`, `Order`, `DataStore`, `App`, 각 탭 클래스 |
| 자료구조 | **list**: 주문 목록 / **dict**: 회원·상품 저장소, 동네 좌표, 정렬 기준 / **set**: 찜 목록, 신고자(중복 방지) / **tuple**: 분류·유형 상수, 좌표 |
| (선택) 전문 모듈 | `hashlib`, `math` (하버사인 거리), `datetime`, `collections.Counter`, `csv` |

## 파일 구조

```
dongne_fridge/
├── main.py          # 실행 파일
├── models.py        # 데이터 클래스: User, Item, Order
├── location.py      # 동네 좌표, 거리 계산, 배달비 계산
├── storage.py       # DataStore: JSON 저장, 회원/상품/주문 처리, 통계, CSV
├── gui_app.py       # App (최상위 창), 공통 스타일
├── gui_login.py     # 로그인, 회원가입
├── gui_main.py      # 메인 화면 (상단 바 + 탭)
├── gui_market.py    # 동네 장터 탭, 상품 상세/주문 창
├── gui_map.py       # 동네 지도 탭
├── gui_sell.py      # 상품 등록 탭, 내 판매 관리 탭
├── gui_mypage.py    # 마이페이지 탭
└── data/            # 실행 시 자동 생성 (users.json, items.json, orders.json)
```

## 역할 분담 예시 (4명 기준)

| 담당 | 파일 | 내용 |
|---|---|---|
| 팀원 A (팀장) | `models.py`, `storage.py`, `main.py` | 데이터 구조, 파일 저장, GitHub 관리 |
| 팀원 B | `gui_login.py`, `gui_main.py`, `gui_app.py` | 로그인·회원가입, 메인 화면, 스타일 |
| 팀원 C | `gui_market.py`, `location.py` | 장터 검색·주문, 거리·배달비 |
| 팀원 D | `gui_sell.py`, `gui_map.py`, `gui_mypage.py` | 판매자 기능, 지도, 통계 |

## 개발 일정 예시

| 주차 | 내용 |
|---|---|
| 11주차 | 주제 제안 발표, GitHub 저장소 생성 |
| 12주차 | 데이터 모델·파일 저장 완성, 로그인/장터 화면 |
| 13주차 | 판매 등록·관리, 주문·배달, 지도, 중간 발표 |
| 14주차 | 통계·CSV, 테스트·버그 수정, 최종 발표·시연 |

## 형상관리 (GitHub)

1. 팀장이 GitHub 저장소를 만들고 팀원을 Collaborator로 초대합니다.
2. 팀원은 `git checkout -b feature/기능이름`으로 브랜치를 만들어 작업합니다.
3. 작업이 끝나면 push하고 Pull Request를 올립니다. 팀장이 리뷰한 뒤 `main`에 병합합니다.

## 앞으로 확장할 수 있는 기능 (선택 과제)

- **Open API**: 카카오/네이버 지도 API로 실제 주소와 거리를 쓰도록 `location.py`를 교체
- **네트워크(socket)**: 서버 하나에 `DataStore`를 두고 여러 PC에서 접속해 실시간 매칭
- 상품 사진 첨부 (`PhotoImage`, Pillow)

## AI 사용 표기

과제 규정에 따라 AI가 생성한 모든 파일 맨 위에 AI 종류, 사용 목적, 프롬프트, 사용한 사람, 날짜를 주석으로 적었습니다.
팀원이 코드를 고치면 그 주석 아래에 `수정: 이름, 날짜, 내용`을 덧붙여 주세요.
