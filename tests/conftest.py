"""
================================================================
[프로그램명] 실습 3 테스트 공통 준비 (pytest fixture)
================================================================

■ 목적
    모든 테스트가 함께 쓰는 두 가지를 여기서 준비한다.
      1) 제출 파일(광주_1반_박기택.py)을 모듈로 불러오는 방법
      2) 실제 데이터 대신 쓸 작은 시험용 CSV

■ 왜 importlib 로 불러오는가
    제출 파일 이름이 `광주_1반_박기택.py` 라서 `import 광주_1반_박기택` 은
    사람이 읽기 어렵고 편집기·검사 도구에서도 잘 인식되지 않는다.
    파일 경로를 직접 지정해 불러오면 파일 이름이 어떻게 바뀌어도
    이 파일 한 곳만 고치면 되므로 테스트 전체가 영향을 받지 않는다.

■ 왜 원본 CSV(77MB, 100만 행)를 쓰지 않는가
    테스트는 자주, 빨리 돌아야 의미가 있다. 원본을 쓰면 한 번 돌리는 데
    수 초가 걸리고, 데이터가 바뀌면 기대값도 매번 흔들린다.
    손으로 계산해 검증할 수 있는 12행짜리 표본을 만들어, 결과를 정확한
    숫자로 단언한다. 결측·이상치·BOM 등 원본이 가진 함정은 모두 포함한다.

■ 작성자 : 박기택
■ 최초 작성일 : 2026-07-21
================================================================
"""

import importlib.util
import sys
from pathlib import Path

import pytest

# 제출 파일 경로. 파일 이름이 바뀌면 이 줄만 고치면 된다.
# 실습 3과 실습 4의 제출 파일명이 같아(캠퍼스명_반_이름.py 규칙) 폴더로 구분한다.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = PROJECT_ROOT / "광주_1반_박기택.py"
MODULE4_PATH = PROJECT_ROOT / "실습4" / "광주_1반_박기택.py"

# 시험용 CSV 내용.
# 원본과 같은 컬럼 구성을 유지하면서 아래 상황을 모두 담았다.
#   - region 결측 2건, category 결측 2건 (둘 다 결측인 행 1건 포함)
#   - amount 결측 1건            → 집계에서 제외되어야 한다
#   - amount 이상치 1건(100000)  → IQR 필터에서 걸러져야 한다
#
# amount 결측을 뺀 값은 100~1000(100단위 10개)과 100000 총 11개다.
# 손으로 계산하면 Q1=350, Q3=850, IQR=500, 정상 범위=[-400, 1600] 이 되어
# 100000 한 건만 이상치로 빠진다. 기대값을 코드가 아니라 손으로 검증할 수 있다.
SAMPLE_ROWS = [
    # (order_id, region, category, amount)
    (1, "서울", "전자", "100"),
    (2, "서울", "전자", "200"),
    (3, "서울", "의류", "300"),
    (4, "부산", "전자", "400"),
    (5, "부산", "의류", "500"),
    (6, "", "전자", "600"),  # region 결측
    (7, "서울", "", "700"),  # category 결측
    (8, "", "", "800"),  # region·category 모두 결측
    (9, "부산", "의류", "900"),
    (10, "서울", "전자", "1000"),
    (11, "서울", "전자", ""),  # amount 결측 → 집계 제외
    (12, "부산", "전자", "100000"),  # 이상치 → IQR 필터 제외
]

# 시험용 CSV 를 기준으로 손으로 계산한 IQR 값. 테스트가 이 값을 그대로 검증한다.
EXPECTED_Q1 = 350.0
EXPECTED_Q3 = 850.0
EXPECTED_IQR = 500.0
EXPECTED_LOWER = -400.0  # 350 - 1.5 × 500
EXPECTED_UPPER = 1600.0  # 850 + 1.5 × 500

# IQR 필터를 통과해야 하는 행 수 (전체 12행 - amount 결측 1행 - 이상치 1행)
EXPECTED_KEPT_ROWS = 10

# 결측을 '미상'/'미분류'로 채운 뒤 만들어져야 하는 그룹별 기대값
# {(region, category): (total, count)}
EXPECTED_GROUPS = {
    ("부산", "의류"): (1400.0, 2),  # 500 + 900
    ("서울", "전자"): (1300.0, 3),  # 100 + 200 + 1000 (이상치·결측 제외)
    ("미상", "미분류"): (800.0, 1),
    ("서울", "미분류"): (700.0, 1),
    ("미상", "전자"): (600.0, 1),
    ("부산", "전자"): (400.0, 1),  # 100000 은 이상치로 제외
    ("서울", "의류"): (300.0, 1),
}


def write_sample_csv(path, rows=SAMPLE_ROWS, with_bom=True):
    """
    [기능] 시험용 매출 CSV 파일을 만든다.
    [설명] 원본 파일은 맨 앞에 BOM(눈에 보이지 않는 표식)이 붙어 있다.
           테스트에서도 같은 조건을 만들어야 "BOM 때문에 첫 컬럼 이름이 깨지는" 문제를
           실제로 잡아낼 수 있으므로, 기본값으로 BOM 을 붙여 저장한다.

    Args:
        path (Path): 만들 CSV 파일 경로.
        rows (list[tuple]): (order_id, region, category, amount) 목록.
        with_bom (bool): BOM 을 붙일지 여부.

    Returns:
        Path: 만들어진 파일 경로.
    """
    header = (
        "order_id,order_date,region,category,product_name,"
        "quantity,unit_price,payment_method,customer_age,customer_gender,amount"
    )
    lines = [header]
    for order_id, region, category, amount in rows:
        lines.append(
            f"{order_id},2024-01-01,{region},{category},상품_{order_id},"
            f"1,1000,카드,30,M,{amount}"
        )

    # utf-8-sig 로 저장하면 BOM 이 자동으로 붙는다
    path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig" if with_bom else "utf-8")
    return path


def load_module(path, name):
    """
    [기능] 파일 경로를 지정해 파이썬 모듈로 불러온다.
    [설명] 제출 파일이 한글 이름이라 `import 광주_1반_박기택` 은 읽기 어렵고
           편집기·검사 도구에서도 잘 인식되지 않는다. 경로로 직접 불러오면
           파일 이름이 어떻게 바뀌어도 이 함수 하나만 고치면 된다.

    Args:
        path (Path): 불러올 .py 파일 경로.
        name (str): 모듈에 붙일 이름.

    Returns:
        module: 불러온 모듈.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    # 모듈 안에서 자기 자신을 참조하는 경우를 대비해 등록한 뒤 실행한다
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def practice():
    """
    [기능] 실습 3 제출 파일을 파이썬 모듈로 불러와 테스트에 넘긴다.
    [설명] 모듈을 매번 다시 불러오면 시간이 낭비되므로 세션 전체에서 한 번만 만든다.

    Returns:
        module: 광주_1반_박기택.py (실습 3) 모듈.
    """
    return load_module(MODULE_PATH, "practice3")


@pytest.fixture(scope="session")
def practice4():
    """
    [기능] 실습 4 제출 파일을 파이썬 모듈로 불러와 테스트에 넘긴다.
    [설명] 실습 3과 파일 이름이 같아 폴더로 구분한다. 모듈 이름도 다르게 등록해야
           sys.modules 에서 서로 덮어쓰지 않는다.

    Returns:
        module: 실습4/광주_1반_박기택.py 모듈.
    """
    return load_module(MODULE4_PATH, "practice4_module")


# 실습 4 시험용 데이터 생성에 쓸 값들.
# 무작위 대신 순번으로 돌려 쓰면 몇 번을 실행해도 같은 데이터가 나와,
# 테스트가 어느 날 갑자기 실패하는 일이 없다.
P4_REGIONS = ("서울", "부산", "대구", "")          # 빈 값 → '미상' 으로 채워지는지 확인용
P4_CATEGORIES = ("전자", "의류", "식품", "")        # 빈 값 → '미분류' 확인용
P4_PAYMENTS = ("카드", "현금", "계좌이체", "포인트")
P4_GENDERS = ("M", "F")


def write_practice4_sample_csv(path, rows=300, outliers=6):
    """
    [기능] 실습 4 테스트용 매출 CSV 를 만든다.
    [설명] 실습 3 표본(12행)은 실습 4에 쓸 수 없다. 모델을 훈련·검증으로 나누려면
           최소 100행이 필요하고, 월별 추이를 보려면 날짜가 여러 달에 걸쳐야 하며,
           회귀가 성립하려면 수량·단가에 변화가 있어야 하기 때문이다.

           원본 데이터의 성격을 그대로 재현한다.
             - amount = quantity × unit_price (정상 행)
             - 일부 행은 amount 를 10배로 부풀림 → IQR 이 걸러낼 이상치
             - region·category 에 빈 값 섞임    → '미상'/'미분류' 로 채워지는지 확인
             - 날짜가 여러 달에 걸침            → 월별 추이 계산 가능

    Args:
        path (Path): 만들 CSV 파일 경로.
        rows (int): 만들 행 수.
        outliers (int): amount 를 부풀릴 이상치 행 수.

    Returns:
        Path: 만들어진 파일 경로.
    """
    header = (
        "order_id,order_date,region,category,product_name,"
        "quantity,unit_price,payment_method,customer_age,customer_gender,amount"
    )
    lines = [header]
    for i in range(rows):
        quantity = i % 19 + 1
        unit_price = 1000 + (i * 137) % 90000
        amount = quantity * unit_price
        # 앞쪽 몇 건만 10배로 부풀려 IQR 이 걸러낼 이상치로 만든다
        if i < outliers:
            amount *= 10
        월 = i % 3 + 1
        일 = i % 28 + 1
        lines.append(
            f"{i + 1},2024-{월:02d}-{일:02d},"
            f"{P4_REGIONS[i % len(P4_REGIONS)]},{P4_CATEGORIES[i % len(P4_CATEGORIES)]},"
            f"상품_{i},{quantity},{unit_price},{P4_PAYMENTS[i % len(P4_PAYMENTS)]},"
            f"{20 + i % 50},{P4_GENDERS[i % len(P4_GENDERS)]},{amount}"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
    return path


@pytest.fixture
def sample_csv(tmp_path):
    """
    [기능] 테스트마다 새 임시 폴더에 시험용 CSV 를 만들어 경로를 넘긴다.
    [설명] tmp_path 는 테스트마다 서로 다른 폴더를 주므로, 한 테스트가 만든 파일이
           다른 테스트에 영향을 주지 않는다.

    Args:
        tmp_path (Path): pytest 가 제공하는 임시 폴더.

    Returns:
        Path: 만들어진 시험용 CSV 경로.
    """
    return write_sample_csv(tmp_path / "sample.csv")


@pytest.fixture
def bounds(practice, sample_csv):
    """
    [기능] 시험용 CSV 로 계산한 IQR 정상 범위를 넘긴다.
    [설명] 세 도구의 집계 함수는 모두 이 값을 인자로 받으므로,
           테스트마다 똑같이 만드는 코드를 반복하지 않도록 픽스처로 분리했다.

    Returns:
        IQRBounds: q1, q3, iqr, lower, upper 를 담은 계산 결과.
    """
    frame = practice.load_sales(sample_csv)
    return practice.compute_iqr_bounds(frame[practice.TARGET_COLUMN])
