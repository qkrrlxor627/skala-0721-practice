"""
================================================================
[프로그램명] 매출 데이터 시각화 · 통계 검정 · 예측 모델 (실습 4)
================================================================

■ 목적
    실습 3에서 정제한 매출 데이터를 이어받아 세 가지 질문에 답한다.
      1) 데이터가 어떻게 생겼는가          → EDA 차트 4종
      2) 지역·항목 사이에 실제 차이가 있는가 → 통계 검정 2종
      3) 매출을 예측할 수 있는가            → sklearn Pipeline
    "차이가 있어 보인다"를 눈이 아니라 숫자로 판정하는 것이 핵심이다.

■ 입력
    - sales_100k.csv (매출 거래 100만 행)
      컬럼: order_id, order_date, region, category, product_name,
            quantity, unit_price, payment_method, customer_age,
            customer_gender, amount
      ※ 스크립트와 같은 폴더 또는 그 상위 폴더에서 찾는다.
        (저장소에서는 상위 폴더, 채점 시에는 같은 폴더에 두는 경우를 모두 지원)

■ 실습 3과의 연계
    - 결측치·IQR 이상치 처리 방식을 실습 3과 동일하게 적용해 같은 정제 결과를 얻는다.
      (1,000,000행 → 973,806행)
    - region·category별 총매출 집계 결과를 Plotly 차트의 입력으로 재사용한다.
    - 정제된 DataFrame을 시각화·통계 검정·모델 학습의 공통 입력으로 쓴다.

■ 출력 (결론을 먼저, 근거를 뒤에 보여준다)
    1) 진행 상황  [1/5]~[5/5] 한 줄씩
    2) 핵심 결과  t-test 판정 / 카이제곱 판정 / 회귀 성능 / 저장 산출물
    3) 이하 상세  데이터 정제, 검정 해석, Pipeline 구성·평가, 생성 파일 목록
    - eda_2x2.png                     (2×2 서브플롯 차트 4종)
    - sales_model.joblib              (학습된 Pipeline)
    - sales_by_region_category.html   (Plotly 인터랙티브 차트)
    - 실행로그.log                     (실행 시각·진행 상황·경고 기록)

■ 처리 방식 요약
    - 차트 4종은 plt.subplots(2, 2)로 만든 하나의 Figure 에 그린다.
      각각 따로 띄우면 서로 비교할 수 없고, 파일로 남기기도 어렵다.
    - KDE 곡선은 표본 20,000건으로 계산한다. 97만 건 전체로 계산하면 수십 초가
      걸리는데, 분포의 모양은 2만 건이면 충분히 같은 곡선이 나온다.
    - 통계 검정은 p-value 만 찍지 않고 효과크기(Cohen's d, Cramér's V)를 함께 낸다.
      표본이 97만 건이면 아주 작은 차이도 '유의'해질 수 있어, p-value 하나로는
      "차이가 크다"를 말할 수 없기 때문이다.
    - 전처리(ColumnTransformer)를 한 번만 정의하고 모델만 바꿔 끼워 두 모델을 비교한다.
      전처리 코드를 모델마다 복사하지 않는 것이 Pipeline 을 쓰는 이유다.
    - 저장한 모델은 다시 불러와 같은 예측이 나오는지까지 확인한다.
      저장이 깨졌는지는 불러와서 써 봐야 알 수 있다.
    - 표준 logging 으로 화면과 파일에 동시에 기록한다.

■ 오류 상황별 대응 (별도 표기가 없으면 안내 후 종료 코드 1 반환)
    - 라이브러리 미설치            → 설치 명령을 안내
    - 입력 파일 없음/권한 없음     → 찾아본 경로를 모두 안내
    - 파일 인코딩이 UTF-8 아님     → UTF-8로 다시 저장하도록 안내
    - CSV 형식 깨짐/빈 파일        → 몇 번째 줄이 문제인지 안내
    - 필수 컬럼 누락               → 실제 컬럼 목록을 함께 안내
    - amount 가 숫자 컬럼이 아님   → 실제 자료형을 함께 안내
    - IQR 필터 결과 0건            → 빈 분석 대신 이상 상황으로 알림
    - 한글 폰트 없음               → 경고 후 계속 진행 (차트는 생성됨)
    - 차트 저장 실패               → 경고 후 계속 진행 (분석은 정상 수행)
    - t-test 그룹에 자료 없음      → 실제 존재하는 지역 목록을 함께 안내
    - 분할표 기대빈도 5 미만       → 카이제곱 가정 위반을 경고하고 참고용으로 표시
    - 학습 자료 부족               → 훈련/검증 분할이 불가함을 안내
    - 모델 저장 실패               → 필수 산출물이므로 오류로 처리
    - 재로딩 예측값 불일치         → 저장이 손상된 것이므로 실패로 알림
    - Plotly 차트 저장 실패        → 필수 산출물이므로 오류로 처리
    - 실행 중 Ctrl+C              → 오류 화면 대신 중단 안내 후 종료 코드 130
    - 메모리 부족                  → 나눠서 실행하도록 안내

■ 실행 방법
    python 광주_1반_박기택.py
    python 광주_1반_박기택.py > 실행결과.txt     (화면 출력을 파일로 남길 때)

■ 작성자 : 박기택
■ 최초 작성일 : 2026-07-21

----------------------------------------------------------------
■ 변경 내역 (Change Log)
----------------------------------------------------------------
| 버전   | 날짜        | 작성자   | 변경 내용                          |
|--------|-------------|----------|------------------------------------|
| v1.0   | 2026-07-21  | 박기택   | 최초 작성. 실습 3의 정제 로직을    |
|        |             |          | 이어받아 2×2 EDA 차트 4종 추가     |
| v1.1   | 2026-07-21  | 박기택   | 독립표본 t-test, 카이제곱 독립성   |
|        |             |          | 검정 및 p<0.05 판정·해석 추가      |
| v1.2   | 2026-07-21  | 박기택   | ColumnTransformer + Pipeline 구성. |
|        |             |          | 전처리를 한 번만 정의하고 모델만   |
|        |             |          | 교체해 선형·트리 두 모델 비교      |
| v1.3   | 2026-07-21  | 박기택   | joblib 저장·재로딩 및 예측값 일치  |
|        |             |          | 검증, Plotly 차트 HTML 저장 추가   |
| v1.4   | 2026-07-21  | 박기택   | p-value 단독 해석의 한계를 보완하  |
|        |             |          | 려고 효과크기(Cohen's d,          |
|        |             |          | Cramér's V) 병기. 표본 97만 건에서 |
|        |             |          | 는 미미한 차이도 유의해질 수 있음  |
| v1.5   | 2026-07-21  | 박기택   | OneHotEncoder 가 희소 행렬을 내보  |
|        |             |          | 내 트리 모델이 거부하던 문제 수정  |
|        |             |          | (sparse_output=False 로 통일).    |
|        |             |          | 선형 모델 R² 가 0.84 로 높게 나온  |
|        |             |          | 이유를 1차 근사로 규명해 해설 보강 |
| v1.6   | 2026-07-21  | 박기택   | 검토 의견 반영. (1) p>=0.05 를     |
|        |             |          | '평균이 같다'·'독립'으로 단정하던  |
|        |             |          | 표현을 '증거를 찾지 못했다'로 정정 |
|        |             |          | (귀무가설은 채택 대상이 아님).     |
|        |             |          | chi2 결과 키도 independent →      |
|        |             |          | associated 로 변경. (2) 제거 건수를 |
|        |             |          | 결측·이상치로 분리 보고. (3) 회귀  |
|        |             |          | 결과가 예측력이 아님을 명시.       |
|        |             |          | (4) 총매출 순위가 객단가가 아니라  |
|        |             |          | 거래량 순위임을 표에 주석          |
================================================================
"""

import io
import logging
import sys
import unicodedata
from pathlib import Path

# 이 프로그램은 시각화·통계·머신러닝 라이브러리가 모두 있어야 목적을 달성할 수 있다.
# 실행 도중 갑자기 멈추는 대신, 시작하자마자 무엇이 없는지와 설치 방법을 알려주고 끝낸다.
try:
    import joblib
    import matplotlib

    # 화면 장치가 없는 환경(터미널·서버·CI)에서도 차트를 파일로 저장할 수 있어야 한다.
    # pyplot 을 불러오기 전에 지정해야 적용된다.
    matplotlib.use("Agg")

    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import plotly.express as px
    from matplotlib import font_manager
    from scipy import stats
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_absolute_error
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
except ImportError as import_error:
    print(f"[오류] 필요한 라이브러리가 설치되어 있지 않습니다: {import_error.name}")
    print("       아래 명령으로 설치한 뒤 다시 실행해 주세요.")
    print("       pip install -r requirements.txt")
    sys.exit(1)


# ================================================================
# 설정값 - 담당자가 바꿀 일이 있는 값은 모두 여기 모아둔다
# ================================================================

# 분석 대상 원본 파일. 데이터가 바뀌면 이 파일만 교체하면 된다.
DATA_FILE = "sales_100k.csv"

# 실행할 때마다 새로 만들어지는 산출물
LOG_FILE = "실행로그.log"
CHART_FILE = "eda_2x2.png"
MODEL_FILE = "sales_model.joblib"
PLOTLY_FILE = "sales_by_region_category.html"

# 집계·분석의 중심이 되는 컬럼
TARGET_COLUMN = "amount"
GROUP_KEYS = ["region", "category"]
DATE_COLUMN = "order_date"

# 원본에 반드시 있어야 하는 컬럼. 하나라도 없으면 분석 자체가 성립하지 않는다.
REQUIRED_COLUMNS = (
    "region",
    "category",
    "payment_method",
    "customer_gender",
    "quantity",
    "unit_price",
    "customer_age",
    DATE_COLUMN,
    TARGET_COLUMN,
)

# IQR 이상치 판정 계수. 실습 3과 같은 값을 써야 같은 정제 결과가 나온다.
IQR_FACTOR = 1.5

# 값이 비어 있는 행도 집계에서 누락되지 않도록, 빈 값 대신 쓸 이름
UNKNOWN_REGION = "미상"
UNKNOWN_CATEGORY = "미분류"

# ---- 통계 검정 설정 ----
# 유의수준. "p < 0.05 면 유의하다"는 판정 기준을 코드에 상수로 못박아 둔다.
ALPHA = 0.05

# 독립표본 t-test 로 비교할 두 지역. 다른 지역이나 성별로 바꿔도 된다.
TTEST_GROUPS = ("서울", "부산")

# 카이제곱 독립성 검정에 쓸 두 범주형 컬럼
CHI2_COLUMNS = ("region", "category")

# 카이제곱 검정이 신뢰할 만하려면 분할표의 기대빈도가 이 값 이상이어야 한다.
MIN_EXPECTED_FREQUENCY = 5

# ---- 시각화 설정 ----
# KDE(분포 곡선) 계산에 쓸 표본 크기.
# gaussian_kde 는 자료 수에 비례해 느려져 97만 건 전체로는 수십 초가 걸린다.
# 곡선의 모양은 2만 건이면 사실상 같으므로, 표본으로 계산하고 그 사실을 밝힌다.
PLOT_SAMPLE_SIZE = 20_000

# 한글이 깨지지 않도록 시도할 폰트 후보 (macOS → Windows → Linux 순)
KOREAN_FONTS = ("AppleGothic", "Malgun Gothic", "NanumGothic", "NanumBarunGothic")

# 상관 히트맵에 넣을 수치형 컬럼
NUMERIC_COLUMNS = ["quantity", "unit_price", "customer_age", TARGET_COLUMN]

# ---- 모델 설정 ----
# 예측에 쓸 입력 변수. 전처리 방식이 달라 수치형과 범주형을 나눠 둔다.
NUMERIC_FEATURES = ["quantity", "unit_price", "customer_age"]
CATEGORICAL_FEATURES = ["region", "category", "payment_method", "customer_gender"]

# 검증용으로 떼어 둘 비율과 난수 씨앗(다시 실행해도 같은 결과가 나오도록)
TEST_SIZE = 0.2
RANDOM_STATE = 42

# 훈련/검증으로 나누려면 최소한 이 정도 행은 있어야 한다.
MIN_TRAINING_ROWS = 100

# 재로딩한 모델이 같은 예측을 내는지 확인할 때 쓸 표본 수
RELOAD_CHECK_ROWS = 100

# 화면·보고에 보여줄 상위 건수
TOP_N = 10

# 부동소수 비교 허용 오차
FLOAT_TOLERANCE = 1e-9

# 화면과 파일에 동시에 기록하기 위한 기록 담당자(logger)
logger = logging.getLogger("practice4")


# ================================================================
# 1. 실행 기록(로깅) 준비
# ================================================================


class LogFileFormatter(logging.Formatter):
    """
    [기능] 로그 파일에서 '한 줄 = 기록 한 건'이 유지되도록 메시지의 줄바꿈을 정리한다.
    [설명] 화면에서는 표나 항목 사이를 띄우려고 메시지에 줄바꿈을 넣는다. 그런데 그 줄바꿈이
           파일에도 그대로 들어가면 시각·심각도가 없는 줄이 생긴다.
           그러면 나중에 로그를 검색하거나 다른 도구로 읽을 때 그 줄이 걸린다.
           화면 출력은 손대지 않고, 파일에 적을 때만 줄바꿈을 정리한다.
    """

    def format(self, record):
        """
        [기능] 기록 한 건을 파일에 적을 한 줄짜리 문자열로 만든다.

        Args:
            record (logging.LogRecord): 기록할 내용 한 건.

        Returns:
            str: 시각·심각도가 앞에 붙은 한 줄짜리 기록.
        """
        original = record.msg
        if isinstance(original, str):
            record.msg = original.strip().replace("\n", " ")
        try:
            return super().format(record)
        # 같은 기록을 화면 담당자도 함께 쓰므로, 원래 내용으로 반드시 되돌린다
        finally:
            record.msg = original


def setup_logging(base_dir):
    """
    [기능] 실행 기록을 화면과 파일 양쪽에 남기도록 준비한다.
    [설명] 화면에는 결과만 깔끔하게 보이고, 파일에는 시각과 심각도까지 함께 남는다.
           로그 파일을 만들지 못하더라도 분석 자체는 문제가 없으므로,
           그 경우 화면 기록만으로 낮춰서 계속 진행한다.

    Args:
        base_dir (Path): 로그 파일을 만들 폴더.

    Returns:
        Path | None: 만들어진 로그 파일 경로. 만들지 못했으면 None.
    """
    logger.setLevel(logging.DEBUG)
    # 같은 프로그램을 여러 번 불러도 기록이 중복되지 않도록 기존 설정을 비우고 시작한다
    logger.handlers.clear()
    logger.propagate = False

    # 화면 출력은 기본값(stderr)이 아니라 stdout 으로 보낸다.
    # 그래야 `python 광주_1반_박기택.py > 실행결과.txt` 처럼 결과를 파일로 넘길 수 있다.
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console)

    log_path = base_dir / LOG_FILE
    try:
        file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    # 읽기 전용 폴더나 권한 문제로 로그 파일을 못 만드는 경우가 있다.
    # 기록을 남기려다 본 작업을 멈추게 하면 안 되므로 경고만 남기고 넘어간다.
    except OSError as error:
        logger.warning(f"[안내] 로그 파일을 만들 수 없어 화면에만 기록합니다: {error}")
        return None

    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(LogFileFormatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(file_handler)
    return log_path


# ================================================================
# 2. 데이터 읽기와 정제 (실습 3과 동일한 방식)
# ================================================================


def find_data_file(base_dir, filename=None):
    """
    [기능] 입력 파일을 스크립트 폴더와 그 상위 폴더에서 찾는다.
    [설명] 이 스크립트는 저장소에서 `실습4/` 안에 있고 원본 CSV 는 저장소 루트에 있다.
           반면 채점할 때는 스크립트와 CSV 를 같은 폴더에 두고 실행하는 경우가 많다.
           두 상황을 모두 지원하려고 가까운 곳부터 차례로 찾는다.

           filename 의 기본값을 DATA_FILE 로 직접 적지 않고 None 으로 둔 이유:
           기본값은 함수를 정의할 때 한 번만 계산되어 그 값이 그대로 굳는다.
           나중에 DATA_FILE 을 바꿔도 기본값은 예전 이름을 계속 가리켜,
           "분명히 파일명을 바꿨는데 옛 파일을 찾는다"는 혼란이 생긴다.
           호출할 때마다 읽도록 미뤄 두면 그런 일이 없다.

    Args:
        base_dir (Path): 스크립트가 있는 폴더.
        filename (str | None): 찾을 파일 이름. None 이면 DATA_FILE 을 쓴다.

    Returns:
        Path: 찾은 파일 경로.

    Raises:
        FileNotFoundError: 두 곳 모두에 파일이 없는 경우.
    """
    filename = filename or DATA_FILE
    candidates = [base_dir / filename, base_dir.parent / filename]
    for path in candidates:
        if path.exists():
            return path

    # 어디를 찾아봤는지 알려주지 않으면 담당자가 파일을 어디 둬야 할지 알 수 없다
    찾아본_곳 = " / ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"'{filename}'을 찾을 수 없습니다. 찾아본 경로: {찾아본_곳}")


def load_sales(path):
    """
    [기능] 매출 CSV 파일을 읽어 DataFrame 으로 반환한다.
    [설명] 이후 모든 분석이 이 결과 위에서 이뤄지므로, 여기서 '쓸 수 있는 데이터인지'를
           확인하고 넘긴다.

           encoding 을 utf-8-sig 로 지정하는 이유:
           이 파일은 맨 앞에 BOM(눈에 보이지 않는 표식)이 붙어 있다. 그냥 utf-8 로 읽으면
           첫 컬럼 이름이 'order_id' 가 아니라 '\\ufefforder_id' 로 잡혀서,
           컬럼 이름으로 찾는 코드가 전부 어긋난다.

    Args:
        path (Path): 읽어들일 CSV 파일 경로.

    Returns:
        pandas.DataFrame: 매출 거래 데이터.

    Raises:
        OSError: 파일이 없거나 권한이 없어 열 수 없는 경우.
        UnicodeDecodeError: 파일 인코딩이 UTF-8 계열이 아닌 경우.
        pandas.errors.ParserError: CSV 형식이 깨진 경우.
        pandas.errors.EmptyDataError: 파일이 비어 있는 경우.
        ValueError: 필수 컬럼이 없거나 amount 가 숫자 컬럼이 아닌 경우.
    """
    frame = pd.read_csv(path, encoding="utf-8-sig")

    missing = [name for name in REQUIRED_COLUMNS if name not in frame.columns]
    if missing:
        raise ValueError(
            f"필수 컬럼이 없습니다: {missing} / 실제 컬럼: {list(frame.columns)}"
        )

    # 머리글만 있고 데이터가 없는 파일은 자료형을 판단할 근거가 없어 문자열로 읽힌다.
    # 그 상태로 검사하면 "amount 가 숫자가 아니다"라는 엉뚱한 안내가 나가므로,
    # 빈 데이터는 여기서 통과시키고 호출한 쪽이 '데이터 없음'으로 정확히 알리게 한다.
    if not frame.empty and not pd.api.types.is_numeric_dtype(frame[TARGET_COLUMN]):
        raise ValueError(
            f"'{TARGET_COLUMN}' 컬럼이 숫자가 아닙니다 "
            f"(실제 자료형: {frame[TARGET_COLUMN].dtype})"
        )

    return frame


def clean_sales(frame):
    """
    [기능] 결측치를 채우고 IQR 이상치를 제거해 분석용 데이터를 만든다.
    [설명] 실습 3과 똑같은 방식으로 처리해야 같은 정제 결과(973,806행)가 나오고,
           두 실습의 숫자를 이어서 이야기할 수 있다. 처리 순서는 이렇다.

             1) amount 결측 제외      - 금액을 모르면 어떤 분석에도 쓸 수 없다
             2) IQR 정상 범위만 남김  - 하한 Q1-1.5×IQR, 상한 Q3+1.5×IQR
             3) region/category 결측을 '미상'/'미분류'로 치환
                (버리지 않는 이유: 버리면 그만큼의 매출이 보고서에서 사라진다)

           이 데이터의 이상치는 무작위 잡음이 아니라 amount 가 quantity×unit_price 의
           8~15배로 부풀려진 오염 행이다. IQR 이 걸러내는 대상이 바로 이들이다.

    Args:
        frame (pandas.DataFrame): 원본 매출 데이터.

    Returns:
        tuple[pandas.DataFrame, dict]:
            - 정제된 DataFrame
            - 정제 내역 dict (q1, q3, iqr, lower, upper, rows_before, rows_after,
              rows_removed, missing_removed, outlier_removed)

    Raises:
        ValueError: 유효한 amount 가 없거나 IQR 필터를 통과한 행이 없는 경우.
    """
    values = frame[TARGET_COLUMN]
    if values.dropna().empty:
        raise ValueError(f"'{TARGET_COLUMN}' 컬럼에 유효한 값이 없어 정제할 수 없습니다.")

    q1 = float(values.quantile(0.25))
    q3 = float(values.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - IQR_FACTOR * iqr
    upper = q3 + IQR_FACTOR * iqr

    rows_before = len(frame)
    # between() 은 하한 이상 & 상한 이하를 뜻한다 (양쪽 끝 포함).
    # amount 가 결측이면 between() 이 거짓이 되어 자연히 빠지지만,
    # "결측을 뺀다"는 의도를 코드에 드러내려고 조건을 명시적으로 함께 적는다.
    유효 = values.notna()
    범위안 = values.between(lower, upper)
    clean = frame[유효 & 범위안].copy()
    clean = clean.fillna({"region": UNKNOWN_REGION, "category": UNKNOWN_CATEGORY})
    rows_after = len(clean)

    if rows_after == 0:
        raise ValueError(
            f"IQR 정상 범위 [{lower:,.2f}, {upper:,.2f}]를 통과한 행이 없습니다. "
            f"데이터 분포를 확인해 주세요."
        )

    # 제거 사유를 나눠서 센다.
    # 둘을 합쳐 "26,194건 제거"라고만 하면, 읽는 쪽은 그 전부가 이상치라고 이해한다.
    # 금액을 아예 모르는 행과 금액이 지나치게 큰 행은 성격이 다르므로 따로 보고한다.
    missing_removed = int((~유효).sum())
    outlier_removed = int((유효 & ~범위안).sum())

    return clean, {
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "lower": lower,
        "upper": upper,
        "rows_before": rows_before,
        "rows_after": rows_after,
        "rows_removed": rows_before - rows_after,
        "missing_removed": missing_removed,
        "outlier_removed": outlier_removed,
    }


def aggregate_by_group(frame):
    """
    [기능] region·category별 총매출·평균·건수를 집계한다.
    [설명] 실습 3에서 만든 집계와 같은 결과다. 여기서는 Plotly 차트의 입력으로 쓴다.
           named aggregation(`total=(...)` 형태)으로 결과 컬럼 이름을 직접 지정해,
           나중에 컬럼 이름을 다시 바꿀 일이 없게 한다.

    Args:
        frame (pandas.DataFrame): 정제된 매출 데이터.

    Returns:
        pandas.DataFrame: region, category, total, mean, count 컬럼을 가진 집계 결과.
    """
    return (
        frame.groupby(GROUP_KEYS, as_index=False)
        .agg(
            total=(TARGET_COLUMN, "sum"),
            mean=(TARGET_COLUMN, "mean"),
            count=(TARGET_COLUMN, "count"),
        )
        .sort_values(["total", *GROUP_KEYS], ascending=[False, True, True])
        .reset_index(drop=True)
    )


# ================================================================
# 3. EDA 시각화 4종 - 하나의 Figure 에 2×2 로 배치
# ================================================================


def setup_korean_font():
    """
    [기능] 차트에서 한글이 깨지지 않도록 사용 가능한 한글 폰트를 설정한다.
    [설명] matplotlib 의 기본 폰트에는 한글 글리프가 없어서, 지역명·카테고리명이
           전부 네모(□)로 표시된다. 운영체제마다 설치된 폰트가 다르므로 후보를
           차례로 확인해 처음 발견한 것을 쓴다.

           폰트를 하나도 찾지 못해도 분석 결과 자체는 정상이므로 중단하지 않고
           경고만 남기고 진행한다. 차트의 한글만 깨진다.

           unicode_minus 를 끄는 것은 별개 문제다. 한글 폰트에는 유니코드 음수 기호(−)가
           없는 경우가 많아, 축에 음수가 있으면 그 기호만 네모로 표시된다.
           ASCII 하이픈(-)을 쓰도록 바꾸면 해결된다.

    Returns:
        str | None: 설정한 폰트 이름. 찾지 못했으면 None.
    """
    # 음수 기호 문제는 폰트를 찾든 못 찾든 항상 막아 둔다
    plt.rcParams["axes.unicode_minus"] = False

    설치된_폰트 = {font.name for font in font_manager.fontManager.ttflist}
    for name in KOREAN_FONTS:
        if name in 설치된_폰트:
            plt.rcParams["font.family"] = name
            return name

    logger.warning(
        f"[경고] 한글 폰트를 찾지 못했습니다(후보: {', '.join(KOREAN_FONTS)}). "
        f"차트의 한글이 깨질 수 있습니다. 분석 결과에는 영향이 없습니다."
    )
    return None


def draw_histogram_with_kde(ax, frame):
    """
    [기능] amount 분포를 히스토그램과 KDE 곡선으로 함께 보여준다.
    [설명] 히스토그램은 구간을 몇 개로 나누느냐에 따라 모양이 달라진다. KDE(커널 밀도 추정)
           곡선을 겹쳐 그리면 구간 나누기와 무관한 분포의 윤곽을 함께 볼 수 있다.

           KDE 를 표본으로 계산하는 이유: gaussian_kde 는 자료 수에 비례해 느려져
           97만 건 전체로는 수십 초가 걸린다. 분포의 모양을 보는 것이 목적이므로
           2만 건 표본이면 사실상 같은 곡선이 나온다.

    Args:
        ax (matplotlib.axes.Axes): 그릴 대상 서브플롯.
        frame (pandas.DataFrame): 정제된 매출 데이터.
    """
    values = frame[TARGET_COLUMN]

    # 원 단위 그대로 그리면 축이 0.0~0.8 에 '1e6' 오프셋이 붙어 읽기 어렵다.
    # 백만원 단위로 바꿔 축 숫자와 축 이름이 서로 맞게 한다.
    백만원 = values / 1_0000_00

    # density=True 로 그려야 KDE 곡선(확률밀도)과 세로 축 단위가 맞는다
    ax.hist(백만원, bins=50, density=True, alpha=0.6, color="#4C78A8", label="히스토그램")

    표본 = 백만원.sample(min(PLOT_SAMPLE_SIZE, len(백만원)), random_state=RANDOM_STATE)
    kde = stats.gaussian_kde(표본)
    grid = np.linspace(백만원.min(), 백만원.max(), 200)
    ax.plot(grid, kde(grid), color="#E45756", linewidth=2, label=f"KDE (표본 {len(표본):,}건)")

    ax.set_title("매출액 분포 (히스토그램 + KDE)")
    ax.set_xlabel("매출액 (백만원)")
    ax.set_ylabel("확률밀도")
    ax.legend()


def draw_boxplot(ax, frame):
    """
    [기능] 지역별 매출액 분포를 박스플롯으로 비교한다.
    [설명] 박스플롯은 중앙값·사분위수·이상치를 한 번에 보여줘서, 지역 간 분포가
           실제로 다른지 눈으로 먼저 가늠할 수 있다. 여기서 "비슷해 보인다"를
           확인한 뒤 t-test 로 그 인상이 맞는지 판정하는 흐름이다.

    Args:
        ax (matplotlib.axes.Axes): 그릴 대상 서브플롯.
        frame (pandas.DataFrame): 정제된 매출 데이터.
    """
    지역 = sorted(frame["region"].unique())
    # 히스토그램과 같은 백만원 단위로 맞춰야 두 차트를 나란히 읽을 수 있다
    자료 = [
        frame.loc[frame["region"] == name, TARGET_COLUMN].to_numpy() / 1_0000_00
        for name in 지역
    ]

    ax.boxplot(자료, tick_labels=지역, showfliers=False)
    ax.set_title("지역별 매출액 분포 (박스플롯)")
    ax.set_xlabel("지역")
    ax.set_ylabel("매출액 (백만원)")
    ax.tick_params(axis="x", rotation=45)


def analyze_monthly(frame):
    """
    [기능] 월별 총매출과, 그 달의 일수로 나눈 일평균 매출을 함께 집계한다.
    [설명] 월별 총매출만 보면 2월이 유독 낮아 계절성이 있는 것처럼 보인다.
           그런데 2월은 28~29일이고 다른 달은 30~31일이다. 즉 장사가 안 된 게 아니라
           영업일이 짧았을 뿐일 수 있다.
           이를 구분하려고 일수로 나눈 일평균을 함께 계산한다. 일평균이 평평하다면
           변동의 정체는 계절성이 아니라 달력이다.

           날짜 변환에 errors="coerce" 를 쓰는 이유: 형식이 깨진 날짜가 몇 건 있다고
           전체 분석을 멈출 수는 없다. 변환에 실패한 행은 NaT 가 되어 자연히 빠지고,
           몇 건이 빠졌는지는 경고로 남긴다.

    Args:
        frame (pandas.DataFrame): 정제된 매출 데이터.

    Returns:
        dict: 월별 집계 결과.
              - table       : 월·총매출·일수·일평균을 담은 DataFrame
              - cv_total    : 총매출의 변동계수(%)
              - cv_daily    : 일평균의 변동계수(%) — 일수를 보정한 뒤의 변동
              - months      : 집계된 개월 수
    """
    날짜 = pd.to_datetime(frame[DATE_COLUMN], errors="coerce")
    실패 = int(날짜.isna().sum())
    if 실패:
        logger.warning(f"[경고] 날짜 형식이 잘못된 {실패:,}건은 월별 추이에서 제외했습니다.")

    table = (
        frame.assign(_월=날짜.dt.to_period("M"))
        .dropna(subset=["_월"])
        .groupby("_월", observed=True)[TARGET_COLUMN]
        .sum()
        .sort_index()
        .to_frame("총매출")
    )
    table["일수"] = table.index.days_in_month
    table["일평균"] = table["총매출"] / table["일수"]

    # 변동계수 = 표준편차 / 평균. 단위가 다른 두 지표의 '출렁임'을 같은 자로 비교할 수 있다.
    def 변동계수(series):
        return float(series.std() / series.mean() * 100) if series.mean() else 0.0

    return {
        "table": table,
        "cv_total": 변동계수(table["총매출"]),
        "cv_daily": 변동계수(table["일평균"]),
        "months": len(table),
    }


def draw_monthly_line(ax, monthly):
    """
    [기능] 월별 총매출 추이와 일평균 매출 추이를 함께 선 그래프로 보여준다.
    [설명] 시간에 따른 변화는 표로 보면 흐름이 안 잡힌다. 선으로 이어 그리면
           계절성이나 추세가 있는지 한눈에 확인할 수 있다.

           두 선을 겹쳐 그리는 이유: 총매출 선만 보면 2월마다 뚝 떨어져 계절성처럼 보인다.
           일수로 나눈 일평균 선이 평평하다면, 그 하락은 장사가 안 된 것이 아니라
           달이 짧았던 것이다. 한 그림에 두 선을 두면 이 차이를 바로 확인할 수 있다.
           단위가 달라(억원 vs 억원/일) 오른쪽에 보조 축을 따로 둔다.

    Args:
        ax (matplotlib.axes.Axes): 그릴 대상 서브플롯.
        monthly (dict): analyze_monthly() 가 돌려준 월별 집계 결과.
    """
    table = monthly["table"]
    라벨 = [str(period) for period in table.index]

    ax.plot(
        라벨, table["총매출"].to_numpy() / 1_0000_0000,
        marker="o", markersize=4, color="#54A24B", label="월별 총매출 (좌)",
    )
    ax.set_title(f"월별 매출 추이 ({monthly['months']}개월)")
    ax.set_xlabel("월")
    ax.set_ylabel("총매출 (억원)")
    ax.tick_params(axis="x", rotation=90, labelsize=8)
    ax.grid(alpha=0.3)

    # 보조 축: 일수로 나눈 일평균. 총매출 선의 출렁임이 여기서 사라지는지 본다.
    보조 = ax.twinx()
    보조.plot(
        라벨, table["일평균"].to_numpy() / 1_0000_0000,
        marker="s", markersize=3, linestyle="--", color="#E45756",
        label="일평균 매출 (우)",
    )
    보조.set_ylabel("일평균 매출 (억원/일)")

    # ★ 보조 축의 범위를 주 축과 '같은 비율'로 맞춘다.
    #   그냥 두면 matplotlib 이 각 축을 자기 자료 범위에 꽉 채워 자동 확대한다.
    #   그러면 실제로는 0.7%밖에 안 움직이는 일평균 선이 3% 움직이는 총매출 선과
    #   똑같이 출렁여 보여서, 보는 사람이 정반대로 읽게 된다.
    #   주 축 범위를 평균 일수로 나눠 옮기면 두 선의 '출렁임 정도'를 눈으로 비교할 수 있다.
    평균일수 = table["일수"].mean()
    보조.set_ylim(tuple(값 / 평균일수 for 값 in ax.get_ylim()))

    # 두 축의 범례를 하나로 합쳐야 어느 선이 무엇인지 한 번에 읽힌다
    선, 이름 = ax.get_legend_handles_labels()
    보조_선, 보조_이름 = 보조.get_legend_handles_labels()
    ax.legend(선 + 보조_선, 이름 + 보조_이름, fontsize=8, loc="lower left")


def draw_correlation_heatmap(ax, frame):
    """
    [기능] 수치형 컬럼 사이의 상관계수를 히트맵으로 보여준다.
    [설명] 어떤 변수가 매출과 관계있는지 한눈에 보려는 것이다. 모델을 만들기 전에
           이걸 확인하면 "무엇을 넣어야 예측이 되는가"를 미리 가늠할 수 있다.

           각 칸에 수치를 함께 적는 이유: 색만으로는 0.3 과 0.5 를 구분하기 어렵다.

    Args:
        ax (matplotlib.axes.Axes): 그릴 대상 서브플롯.
        frame (pandas.DataFrame): 정제된 매출 데이터.
    """
    상관 = frame[NUMERIC_COLUMNS].corr()

    # vmin/vmax 를 -1~1 로 고정해야 색의 진하기를 값 그대로 읽을 수 있다
    이미지 = ax.imshow(상관, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(NUMERIC_COLUMNS)), NUMERIC_COLUMNS, rotation=45, ha="right")
    ax.set_yticks(range(len(NUMERIC_COLUMNS)), NUMERIC_COLUMNS)

    for i in range(len(NUMERIC_COLUMNS)):
        for j in range(len(NUMERIC_COLUMNS)):
            값 = 상관.iloc[i, j]
            # 배경이 진한 칸에서는 검은 글씨가 안 보이므로 밝기에 따라 글자색을 바꾼다
            ax.text(
                j, i, f"{값:.2f}",
                ha="center", va="center",
                color="white" if abs(값) > 0.5 else "black",
                fontsize=9,
            )

    ax.set_title("수치형 변수 간 상관계수")
    ax.figure.colorbar(이미지, ax=ax, fraction=0.046, pad=0.04)


def create_eda_charts(frame, monthly, output_path):
    """
    [기능] EDA 차트 4종을 하나의 Figure 에 2×2로 그려 파일로 저장한다.
    [설명] 차트를 각각 따로 띄우면 서로 비교할 수 없고, 창을 닫아야 다음 코드가 실행된다.
           하나의 Figure 에 모으면 네 관점을 나란히 보면서 이야기할 수 있고,
           그림 파일 하나로 남길 수 있어 보고에도 그대로 쓸 수 있다.

           저장에 실패해도 통계 검정과 모델 학습은 영향을 받지 않으므로,
           경고만 남기고 계속 진행한다.

    Args:
        frame (pandas.DataFrame): 정제된 매출 데이터.
        monthly (dict): analyze_monthly() 가 돌려준 월별 집계 결과.
        output_path (Path): 저장할 이미지 경로.

    Returns:
        Path | None: 저장된 경로. 저장하지 못했으면 None.
    """
    # ★ 감점 항목: 차트 4개를 각각 plt.show() 하지 않고 2×2 서브플롯 하나로 묶는다
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))

    draw_histogram_with_kde(axes[0, 0], frame)
    draw_boxplot(axes[0, 1], frame)
    draw_monthly_line(axes[1, 0], monthly)      # 월별 집계는 해석에도 쓰므로 미리 계산해 받는다
    draw_correlation_heatmap(axes[1, 1], frame)

    # fontweight="bold" 는 쓰지 않는다. AppleGothic 등 한글 폰트에는 굵은 자족이 없어
    # matplotlib 이 "Failed to find font weight bold" 경고를 매번 내기 때문이다.
    fig.suptitle(f"매출 데이터 EDA (IQR 이상치 제거 후 {len(frame):,}행)", fontsize=15)
    fig.tight_layout()

    try:
        fig.savefig(output_path, dpi=120, bbox_inches="tight")
    except OSError as error:
        logger.warning(f"[경고] 차트를 저장하지 못했습니다: {error}")
        return None
    finally:
        # 저장 성공 여부와 관계없이 Figure 를 닫아 메모리를 돌려준다
        plt.close(fig)

    return output_path


# ================================================================
# 4. 통계 검정 - 눈으로 본 차이가 실제인지 판정
# ================================================================


def run_ttest(frame, groups=TTEST_GROUPS):
    """
    [기능] 두 지역의 평균 매출이 통계적으로 다른지 독립표본 t-test 로 판정한다.
    [설명] 박스플롯에서 "비슷해 보인다"고 느낀 것을 숫자로 확인하는 단계다.
           p-value 가 0.05 보다 작으면 "두 그룹의 평균이 같다"는 가정을 기각한다.

           equal_var=False (Welch 검정)를 쓰는 이유:
           두 그룹의 분산이 같다는 보장이 없다. 표본 수도 서울 24만 건, 부산 12만 건으로
           두 배 차이가 나는데, 이런 상황에서 등분산을 가정하면 결과가 왜곡될 수 있다.
           Welch 검정은 분산이 달라도 쓸 수 있어 기본으로 두는 편이 안전하다.

           효과크기(Cohen's d)를 함께 내는 이유:
           표본이 97만 건이면 실무적으로 무시할 만한 차이도 '통계적으로 유의'해질 수 있다.
           p-value 는 "차이가 있는가"만 답하고 "얼마나 큰가"는 답하지 못한다.
           둘을 같이 봐야 "유의하지만 의미는 없다" 같은 상황을 구분할 수 있다.

    Args:
        frame (pandas.DataFrame): 정제된 매출 데이터.
        groups (tuple[str, str]): 비교할 두 지역 이름.

    Returns:
        dict: 검정 결과 (groups, means, counts, statistic, pvalue, cohens_d,
              significant, interpretation).

    Raises:
        ValueError: 지정한 지역의 자료가 없는 경우.
    """
    first, second = groups
    a = frame.loc[frame["region"] == first, TARGET_COLUMN]
    b = frame.loc[frame["region"] == second, TARGET_COLUMN]

    # 지역명이 바뀌거나 오타가 있으면 빈 배열로 검정이 돌아 NaN 이 나온다.
    # 원인을 바로 알 수 있도록 실제 존재하는 지역 목록을 함께 알린다.
    for name, 자료 in ((first, a), (second, b)):
        if 자료.empty:
            raise ValueError(
                f"'{name}' 지역의 자료가 없습니다. "
                f"실제 지역: {sorted(frame['region'].unique())}"
            )

    result = stats.ttest_ind(a, b, equal_var=False)

    # Cohen's d - 두 평균의 차이를 표준편차 단위로 환산한 값.
    # 통상 0.2 작음 / 0.5 중간 / 0.8 큼 으로 해석한다.
    합동표준편차 = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
    cohens_d = (a.mean() - b.mean()) / 합동표준편차 if 합동표준편차 else 0.0

    significant = bool(result.pvalue < ALPHA)
    return {
        "groups": groups,
        "means": (float(a.mean()), float(b.mean())),
        "counts": (len(a), len(b)),
        "statistic": float(result.statistic),
        "pvalue": float(result.pvalue),
        "cohens_d": float(cohens_d),
        "significant": significant,
        "interpretation": interpret_ttest(
            groups, (float(a.mean()), float(b.mean())), float(result.pvalue),
            float(cohens_d), significant, len(a) + len(b),
        ),
    }


def interpret_ttest(groups, means, pvalue, cohens_d, significant, total_rows):
    """
    [기능] t-test 결과를 사람이 읽을 문장으로 바꾼다.
    [설명] 숫자만 찍어두면 "그래서 어떻다는 것인가"가 남는다. 판정과 그 뜻을 문장으로
           남겨야 보고를 받는 쪽이 바로 판단할 수 있다.
           문장은 실제 측정값에 따라 갈라 쓴다(미리 적어두지 않는다).

    Args:
        groups (tuple[str, str]): 비교한 두 그룹 이름.
        means (tuple[float, float]): 두 그룹의 평균.
        pvalue (float): 검정의 p-value.
        cohens_d (float): 효과크기.
        significant (bool): 유의 여부.
        total_rows (int): 검정에 쓴 전체 표본 수.

    Returns:
        str: 해석 문장.
    """
    차이 = abs(means[0] - means[1])
    비율 = 차이 / max(means) * 100 if max(means) else 0.0

    if significant:
        크기 = "작은" if abs(cohens_d) < 0.2 else "중간 이상의"
        return (
            f"p={pvalue:.4f} < {ALPHA}이므로 {groups[0]}과 {groups[1]}의 평균 매출에 "
            f"차이가 있다고 판단합니다. 다만 효과크기 d={cohens_d:.3f}로 {크기} 차이이므로, "
            f"실제 금액 차이({차이:,.0f}원, {비율:.2f}%)가 의사결정에 쓸 만한지는 별도로 판단해야 합니다."
        )

    # ※ p >= 유의수준은 '평균이 같다'를 증명한 것이 아니다.
    #   '차이가 있다고 볼 근거를 찾지 못했다'는 뜻일 뿐이다.
    #   실무적으로 "차이가 없다"고 말하려면 효과크기와 표본 크기를 함께 근거로 대야 한다.
    return (
        f"p={pvalue:.4f} >= {ALPHA}이므로 {groups[0]}과 {groups[1]}의 평균 매출에 "
        f"차이가 있다는 증거를 찾지 못했습니다. 이는 '두 평균이 같다'가 증명된 것이 아니라, "
        f"차이가 있다고 판단할 근거가 부족하다는 뜻입니다. "
        f"다만 표본이 {total_rows:,}건으로 충분히 크고 효과크기도 d={cohens_d:.3f}로 "
        f"무시할 수준이므로(평균 차이 {차이:,.0f}원, {비율:.2f}%), "
        f"실무적으로 의미 있는 차이는 없다고 봐도 무리가 없습니다. "
        f"두 지역을 나눠 다르게 대응할 근거는 확인되지 않았습니다."
    )


def run_chi2_test(frame, columns=CHI2_COLUMNS):
    """
    [기능] 두 범주형 변수가 서로 독립인지 카이제곱 검정으로 판정한다.
    [설명] "지역에 따라 잘 팔리는 카테고리가 다른가"를 확인하는 검정이다.
           분할표(교차표)를 만들어 관측빈도가 기대빈도에서 얼마나 벗어나는지 본다.
           p-value 가 0.05 보다 작으면 "두 변수는 독립"이라는 가정을 기각한다.

           효과크기로 Cramér's V 를 함께 낸다. 카이제곱 통계량은 표본이 커지면
           같이 커지므로, 값 자체로는 관계의 강도를 말할 수 없기 때문이다.
           V 는 0~1 범위로 표준화되어 표본 수의 영향을 받지 않는다.

    Args:
        frame (pandas.DataFrame): 정제된 매출 데이터.
        columns (tuple[str, str]): 검정할 두 범주형 컬럼 이름.

    Returns:
        dict: 검정 결과 (columns, table_shape, statistic, pvalue, dof, cramers_v,
              associated, min_expected, interpretation).
              associated 는 '연관성이 확인되었는가'(p < 유의수준)를 뜻한다.
              '독립인가'로 이름 붙이지 않은 이유는, 검정이 독립임을 증명할 수는 없고
              연관이 있다는 증거를 찾았는지만 답할 수 있기 때문이다.

    Raises:
        ValueError: 분할표를 만들 수 없는 경우.
    """
    first, second = columns
    table = pd.crosstab(frame[first], frame[second])

    # 한 변수의 값이 한 종류뿐이면 교차표가 한 줄짜리가 되어 검정이 성립하지 않는다
    if table.shape[0] < 2 or table.shape[1] < 2:
        raise ValueError(
            f"분할표가 너무 작아 카이제곱 검정을 할 수 없습니다 "
            f"({first}: {table.shape[0]}종, {second}: {table.shape[1]}종)"
        )

    chi2, pvalue, dof, expected = stats.chi2_contingency(table)

    # 기대빈도가 너무 작은 칸이 있으면 카이제곱 근사가 부정확해진다.
    # 결과를 못 쓰는 것은 아니지만, 그대로 믿으면 안 되므로 알린다.
    min_expected = float(expected.min())
    if min_expected < MIN_EXPECTED_FREQUENCY:
        logger.warning(
            f"[경고] 분할표의 최소 기대빈도가 {min_expected:.1f}로 "
            f"{MIN_EXPECTED_FREQUENCY} 미만입니다. 카이제곱 검정의 가정을 만족하지 못해 "
            f"결과를 참고용으로만 보셔야 합니다."
        )

    # Cramér's V = sqrt(chi2 / (n × min(행-1, 열-1)))
    n = int(table.to_numpy().sum())
    cramers_v = np.sqrt(chi2 / (n * min(table.shape[0] - 1, table.shape[1] - 1)))

    associated = bool(pvalue < ALPHA)
    return {
        "columns": columns,
        "table_shape": table.shape,
        "statistic": float(chi2),
        "pvalue": float(pvalue),
        "dof": int(dof),
        "cramers_v": float(cramers_v),
        "associated": associated,
        "min_expected": min_expected,
        "interpretation": interpret_chi2(
            columns, float(pvalue), float(cramers_v), associated, n
        ),
    }


def interpret_chi2(columns, pvalue, cramers_v, associated, total_rows):
    """
    [기능] 카이제곱 검정 결과를 사람이 읽을 문장으로 바꾼다.
    [설명] 연관성을 확인했는지와 그것이 실무적으로 무엇을 뜻하는지를 함께 적는다.

    Args:
        columns (tuple[str, str]): 검정한 두 컬럼 이름.
        pvalue (float): 검정의 p-value.
        cramers_v (float): 효과크기 Cramér's V.
        associated (bool): 연관성이 확인되었는지 여부.
        total_rows (int): 검정에 쓴 전체 표본 수.

    Returns:
        str: 해석 문장.
    """
    first, second = columns
    if associated:
        강도 = "약한" if cramers_v < 0.1 else ("중간" if cramers_v < 0.3 else "강한")
        return (
            f"p={pvalue:.4f} < {ALPHA}이므로 {first}와 {second} 사이에 연관성이 있다고 "
            f"판단합니다. 즉 지역에 따라 팔리는 카테고리 구성에 차이가 있습니다. "
            f"다만 Cramér's V={cramers_v:.4f}로 {강도} 관계이므로, 차이의 크기까지 고려해 "
            f"대응 여부를 정해야 합니다(표본 {total_rows:,}건)."
        )

    # ※ p >= 유의수준은 '두 변수가 독립'임을 증명한 것이 아니다.
    #   '연관이 있다고 볼 근거를 찾지 못했다'는 뜻일 뿐이다.
    return (
        f"p={pvalue:.4f} >= {ALPHA}이므로 {first}와 {second} 사이에 연관성이 있다는 증거를 "
        f"찾지 못했습니다. 이는 '두 변수가 독립'임이 증명된 것이 아니라, 연관이 있다고 "
        f"판단할 근거가 부족하다는 뜻입니다. "
        f"다만 효과크기 Cramér's V={cramers_v:.4f}로 연관의 강도도 거의 0이므로"
        f"(표본 {total_rows:,}건), 지역별로 상품 구성을 달리할 근거는 확인되지 않았습니다."
    )


# ================================================================
# 5. sklearn Pipeline - 전처리와 모델을 하나로 묶어 학습
# ================================================================


def build_preprocessor():
    """
    [기능] 수치형과 범주형 컬럼을 각각에 맞게 변환하는 전처리기를 만든다.
    [설명] 두 종류의 컬럼은 필요한 처리가 다르다.
             - 수치형: 단위가 제각각이라(개수 vs 원) 표준화해 크기를 맞춘다
             - 범주형: 문자열은 모델이 계산할 수 없어 One-Hot 으로 0/1 컬럼을 만든다
           ColumnTransformer 는 이 둘을 한 객체로 묶어 준다. 따로 처리하면
           훈련 데이터와 검증 데이터에 같은 변환을 적용했는지 사람이 보증해야 하는데,
           묶어 두면 그 실수가 구조적으로 불가능해진다.

           handle_unknown="ignore" 를 주는 이유: 검증·운영 데이터에 훈련 때 없던
           범주가 나타나면 기본값은 오류를 낸다. 그 한 건 때문에 예측 전체가
           멈추는 대신, 모든 0으로 처리하고 넘어가게 한다.

           sparse_output=False 를 주는 이유: OneHotEncoder 는 기본적으로 희소 행렬을
           내보내는데, HistGradientBoostingRegressor 는 조밀 행렬만 받는다.
           두 모델이 같은 전처리기를 공유해야 비교가 공정하므로 조밀로 통일한다.
           범주가 22종뿐이라 조밀로 펼쳐도 메모리 부담이 크지 않다.

    Returns:
        sklearn.compose.ColumnTransformer: 전처리기.
    """
    return ColumnTransformer(
        [
            ("num", StandardScaler(), NUMERIC_FEATURES),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
        ]
    )


def train_and_evaluate(frame):
    """
    [기능] 전처리와 모델을 Pipeline 으로 묶어 학습하고, 두 모델의 성능을 비교한다.
    [설명] 예측 대상은 거래별 매출액(amount)이다.

           이 데이터에서 amount 는 quantity × unit_price 로 결정된다(정제 후 사실상 100%).
           즉 '곱셈' 관계인데, 선형 모델은 입력의 가중합만 표현할 수 있어 곱을
           직접 만들어내지는 못한다. 그런데도 선형 모델의 R² 는 0.84 수준으로 꽤 높게
           나오는데, 이유는 평균 주위에서의 1차 근사가 잘 통하기 때문이다.

               q×p ≈ p̄·q + q̄·p - q̄·p̄  +  (q-q̄)(p-p̄)
                     └─ 선형 결합으로 표현 가능 ─┘   └─ 표현 불가 ─┘

           남는 (q-q̄)(p-p̄) 교호작용 항이 전체 분산의 약 14%를 차지하고, 이것이
           선형 모델이 원리적으로 넘을 수 없는 한계선이 된다(이론상 최대 R² ≈ 0.86).
           트리 기반 모델은 구간을 나눠가며 이 교호작용을 학습하므로 그 벽을 넘는다.

           두 모델을 나란히 돌리는 목적은 성능 경쟁이 아니라, 전처리를 그대로 둔 채
           모델만 바꿔 끼울 수 있다는 Pipeline 의 이점을 숫자로 보여주는 것이다.

           HistGradientBoostingRegressor 를 고른 이유: 97만 행에서 RandomForest 는
           수 분이 걸리지만 이 모델은 10~20초면 끝난다.

    Args:
        frame (pandas.DataFrame): 정제된 매출 데이터.

    Returns:
        dict: 학습 결과.
              - results  : 모델별 성능 목록 (name, r2, mae, pipeline)
              - best      : 성능이 가장 좋은 결과
              - train_rows / test_rows : 학습·검증에 쓴 행 수
              - x_test / y_test        : 재로딩 검증에 쓸 검증 데이터

    Raises:
        ValueError: 학습에 쓸 자료가 부족한 경우.
    """
    if len(frame) < MIN_TRAINING_ROWS:
        raise ValueError(
            f"학습에 쓸 자료가 부족합니다({len(frame):,}행). "
            f"훈련/검증으로 나누려면 최소 {MIN_TRAINING_ROWS}행이 필요합니다."
        )

    features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    x = frame[features]
    y = frame[TARGET_COLUMN]

    # 학습에 쓰지 않은 자료로 평가해야 성능을 부풀리지 않는다
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )

    # ★ 전처리는 한 번만 정의하고 모델만 바꿔 끼운다.
    #   모델마다 전처리 코드를 복사하면, 나중에 전처리를 고칠 때 한쪽만 고치는 사고가 난다.
    후보 = [
        ("LinearRegression", LinearRegression()),
        ("HistGradientBoosting", HistGradientBoostingRegressor(random_state=RANDOM_STATE)),
    ]

    results = []
    for name, model in 후보:
        # ★ 감점 항목: 전처리와 모델을 분리 실행하지 않고 하나의 Pipeline 객체로 묶는다
        pipeline = Pipeline([("prep", build_preprocessor()), ("model", model)])
        pipeline.fit(x_train, y_train)                 # 1) 훈련
        predicted = pipeline.predict(x_test)           # 2) 예측
        results.append(
            {
                "name": name,
                "r2": float(pipeline.score(x_test, y_test)),   # 3) 평가
                "mae": float(mean_absolute_error(y_test, predicted)),
                "pipeline": pipeline,
            }
        )
        logger.info(f"  · {name} 학습·평가 완료 (R²={results[-1]['r2']:.4f})")

    return {
        "results": results,
        "best": max(results, key=lambda item: item["r2"]),
        "train_rows": len(x_train),
        "test_rows": len(x_test),
        "x_test": x_test,
        "y_test": y_test,
    }


def save_and_reload_model(pipeline, path, x_test):
    """
    [기능] 학습한 Pipeline 을 파일로 저장하고, 다시 불러와 같은 예측이 나오는지 확인한다.
    [설명] 저장만 하고 끝내면 그 파일이 실제로 쓸 수 있는지 알 수 없다.
           불러와서 같은 입력에 같은 답이 나오는지까지 확인해야 저장이 성공했다고 말할 수 있다.
           전처리가 Pipeline 안에 들어 있으므로 이 파일 하나만 있으면
           원본 데이터 없이도 새 입력을 그대로 예측할 수 있다.

    Args:
        pipeline (sklearn.pipeline.Pipeline): 저장할 학습된 Pipeline.
        path (Path): 저장할 파일 경로.
        x_test (pandas.DataFrame): 예측 일치를 확인할 검증 데이터.

    Returns:
        dict: 저장 결과 (path, size_bytes, reload_ok, checked_rows).

    Raises:
        OSError: 파일을 저장하거나 읽을 수 없는 경우.
        AssertionError: 재로딩한 모델의 예측이 원본과 다른 경우.
    """
    # ★ 감점 항목: 학습만 하고 끝내지 않고 joblib 으로 모델 파일을 만든다
    joblib.dump(pipeline, path)
    loaded = joblib.load(path)

    표본 = x_test.head(RELOAD_CHECK_ROWS)
    원본_예측 = pipeline.predict(표본)
    재로딩_예측 = loaded.predict(표본)

    # 저장 과정에서 모델이 손상되면 예측값이 달라진다. 조용히 넘어가면 안 되는 문제다.
    assert np.allclose(원본_예측, 재로딩_예측, rtol=FLOAT_TOLERANCE), (
        f"재로딩한 모델의 예측이 원본과 다릅니다. "
        f"최대 차이={np.abs(원본_예측 - 재로딩_예측).max():,.6f}"
    )

    return {
        "path": path,
        "size_bytes": path.stat().st_size,
        "reload_ok": True,
        "checked_rows": len(표본),
    }


# ================================================================
# 6. Plotly 인터랙티브 차트
# ================================================================


def create_plotly_chart(aggregated, path):
    """
    [기능] 지역·카테고리별 총매출을 인터랙티브 막대 차트로 만들어 HTML 로 저장한다.
    [설명] 정적 이미지와 달리 HTML 차트는 마우스를 올리면 정확한 값이 보이고,
           범례를 눌러 특정 카테고리만 볼 수도 있다. 보고를 받는 쪽이 직접
           궁금한 부분을 확인할 수 있어, 질문을 주고받는 횟수가 줄어든다.

           화면에 띄우기만 하면 실행이 끝나는 순간 사라지므로 반드시 파일로 저장한다.

    Args:
        aggregated (pandas.DataFrame): region·category별 집계 결과.
        path (Path): 저장할 HTML 경로.

    Returns:
        dict: 저장 결과 (path, size_bytes, bars).

    Raises:
        OSError: 파일을 저장할 수 없는 경우.
    """
    chart = aggregated.assign(총매출_억원=aggregated["total"] / 1_0000_0000)

    fig = px.bar(
        chart,
        x="region",
        y="총매출_억원",
        color="category",
        barmode="group",
        title="지역·카테고리별 총매출 (IQR 이상치 제거 후)",
        labels={"region": "지역", "총매출_억원": "총매출 (억원)", "category": "카테고리"},
        hover_data={"count": ":,", "mean": ":,.0f"},
    )
    fig.update_layout(legend_title_text="카테고리", hovermode="x unified")

    # ★ 감점 항목: fig.show() 로 끝내지 않고 HTML 파일로 저장한다
    fig.write_html(path)

    return {"path": path, "size_bytes": path.stat().st_size, "bars": len(chart)}


# ================================================================
# 7. 출력 - 결론을 먼저, 근거를 뒤에
# ================================================================


def display_width(text):
    """
    [기능] 문자열이 터미널에서 차지하는 칸 수를 센다.
    [설명] 한글·한자는 영문자 한 글자의 두 칸을 차지한다. len() 은 글자 수만 세므로
           그대로 자리를 맞추면 한글이 섞인 표의 세로줄이 어긋난다.

    Args:
        text (str): 폭을 잴 문자열.

    Returns:
        int: 터미널에서 차지하는 칸 수.
    """
    # 'W'(넓음)와 'F'(전각)로 분류된 문자가 두 칸을 차지한다
    return sum(2 if unicodedata.east_asian_width(char) in "WF" else 1 for char in text)


def pad(text, width, align="left"):
    """
    [기능] 터미널 표시 폭을 기준으로 문자열의 자리를 맞춘다.
    [설명] 파이썬 기본 서식(f"{text:<10}")은 글자 수로 자리를 맞춰서
           한글이 섞이면 표가 어긋난다. 실제 표시 폭으로 계산해 채운다.

    Args:
        text (str): 맞출 문자열.
        width (int): 목표 폭(칸 수).
        align (str): "left" 면 왼쪽 정렬, 그 외에는 오른쪽 정렬.

    Returns:
        str: 폭이 맞춰진 문자열.
    """
    gap = " " * max(0, width - display_width(text))
    return text + gap if align == "left" else gap + text


def format_won(value):
    """
    [기능] 큰 금액을 억·조 단위로 바꿔 읽기 쉽게 만든다.
    [설명] 74,992,750,244원 같은 숫자는 자릿수를 세어야 규모가 잡힌다.
           '749.9억원'으로 보여주면 한눈에 들어온다.

    Args:
        value (float): 원 단위 금액.

    Returns:
        str: 억·조 단위로 정리한 금액 문자열.
    """
    조, 억, 만 = 1_0000_0000_0000, 1_0000_0000, 1_0000
    if abs(value) >= 조:
        return f"{value / 조:,.2f}조원"
    if abs(value) >= 억:
        return f"{value / 억:,.1f}억원"
    if abs(value) >= 만:
        return f"{value / 만:,.1f}만원"
    return f"{value:,.0f}원"


def print_summary(context):
    """
    [기능] 이 실습에서 알고자 한 결론만 추려 화면 맨 앞에 보여준다.
    [설명] 실행하면 가장 먼저 이 블록이 보인다. 근거가 되는 상세 수치는 뒤에 따로 붙는다.
           EDA 원문이나 모델 설정을 먼저 찍으면 정작 알고 싶은 판정 결과가
           화면 아래로 밀려 스크롤해야 보이기 때문이다.

    Args:
        context (dict): run_pipeline() 이 돌려준 실행 결과 모음.

    Returns:
        None: 화면과 로그 파일에 기록만 수행한다.
    """
    ttest = context["ttest"]
    chi2 = context["chi2"]
    training = context["training"]
    선형, 트리 = training["results"][0], training["results"][1]

    logger.info("\n" + "=" * 76)
    logger.info(" 핵심 결과")
    logger.info("=" * 76)
    # 판정 문구에 '같다' / '독립' 을 쓰지 않는다.
    # 검정이 답할 수 있는 것은 '차이·연관을 확인했는가'뿐이고,
    # 없음을 증명할 수는 없기 때문이다.
    logger.info(
        f" [1] t-test ({ttest['groups'][0]} vs {ttest['groups'][1]})"
        f"      t={ttest['statistic']:.3f}, p={ttest['pvalue']:.4f} "
        f"→ {'차이 확인됨' if ttest['significant'] else '차이 미확인'} "
        f"(d={ttest['cohens_d']:.3f})"
    )
    logger.info(
        f" [2] 카이제곱 ({chi2['columns'][0]}×{chi2['columns'][1]})"
        f"   χ²={chi2['statistic']:.2f}, p={chi2['pvalue']:.4f} "
        f"→ {'연관성 확인됨' if chi2['associated'] else '연관성 미확인'} "
        f"(V={chi2['cramers_v']:.4f})"
    )
    logger.info(
        f" [3] 회귀 성능                  "
        f"{선형['name']} R²={선형['r2']:.4f} / {트리['name']} R²={트리['r2']:.4f}"
    )
    logger.info(
        f"                                전처리 동일, 모델만 교체 — 예측력이 아니라 "
        f"모델 교체 효과를 본 실습입니다 (상세 3 참고)"
    )
    logger.info(
        f" [4] 저장 산출물                차트 PNG / 모델 joblib / Plotly HTML "
        f"(재로딩 예측 일치 확인 완료)"
    )
    logger.info("=" * 76)

    표 = context["aggregated"].head(TOP_N)
    머리 = (
        pad("순위", 5) + pad("region", 8) + pad("category", 10)
        + pad("총매출", 13, "right") + pad("평균", 12, "right") + pad("건수", 10, "right")
    )
    줄 = [머리, "-" * display_width(머리)]
    for rank, row in enumerate(표.itertuples(index=False), start=1):
        줄.append(
            pad(str(rank), 5) + pad(row.region, 8) + pad(row.category, 10)
            + pad(format_won(row.total), 13, "right")
            + pad(format_won(row.mean), 12, "right")
            + pad(f"{row.count:,}", 10, "right")
        )
    logger.info(f"\n[매출 상위 {TOP_N}개 그룹]\n" + "\n".join(줄))
    # 총매출 순위를 '어디가 더 잘 판다'로 읽으면 규모와 객단가를 혼동하게 된다.
    평균범위 = (표["mean"].min(), 표["mean"].max())
    logger.info(
        f"  ※ 이 순위는 거래 '건수'가 많은 지역이 올라온 결과입니다. "
        f"상위 {TOP_N}개 그룹의 평균 객단가는 "
        f"{format_won(평균범위[0])}~{format_won(평균범위[1])}로 서로 비슷하므로,\n"
        f"    '어디가 더 비싸게 파는가'가 아니라 '어디에 거래가 몰려 있는가'로 읽어야 합니다."
    )


def print_details(context):
    """
    [기능] 핵심 결과의 근거가 되는 상세 내역을 순서대로 보여준다.
    [설명] 결론만 보고 넘어가도 되지만, 숫자를 확인하려는 사람에게는 근거가 필요하다.
           결론과 근거를 나눠 두면 보는 사람이 필요한 깊이까지만 읽고 멈출 수 있다.

    Args:
        context (dict): run_pipeline() 이 돌려준 실행 결과 모음.

    Returns:
        None: 화면과 로그 파일에 기록만 수행한다.
    """
    정제 = context["cleaning"]
    ttest = context["ttest"]
    chi2 = context["chi2"]
    training = context["training"]

    logger.info("\n" + "-" * 76)
    logger.info(" 이하 상세")
    logger.info("-" * 76)

    # ---- 상세 1: 데이터 정제 ----
    logger.info("\n[상세 1] 데이터 정제 (실습 3과 동일한 방식)")
    logger.info(
        f"- Q1 = {정제['q1']:,.2f} / Q3 = {정제['q3']:,.2f} / IQR = {정제['iqr']:,.2f}"
    )
    logger.info(
        f"- 정상 범위 = [{정제['lower']:,.2f}, {정제['upper']:,.2f}] "
        f"(Q1 - {IQR_FACTOR}×IQR ~ Q3 + {IQR_FACTOR}×IQR)"
    )
    logger.info(
        f"- 제거 전 {정제['rows_before']:,}행 → 제거 후 {정제['rows_after']:,}행 "
        f"(총 {정제['rows_removed']:,}건 제외)"
    )
    # 제거 사유를 나눠 보고한다. 합쳐서 한 숫자로만 내면 전부 이상치였다고 오해한다.
    logger.info(f"    · {TARGET_COLUMN} 결측으로 제외 : {정제['missing_removed']:,}건")
    logger.info(f"    · IQR 범위 밖으로 제외  : {정제['outlier_removed']:,}건")
    logger.info(f"\n[df.info()]\n{context['info_text']}")
    logger.info(f"\n[describe()]\n{context['describe_text']}")

    # ---- 상세 1-1: 월별 추이에서 발견한 것 ----
    # 차트만 보고 "2월에 매출이 떨어진다"고 보고하면 잘못된 결론이 된다.
    # 숫자로 근거를 남겨 오해를 막는다.
    월별 = context["monthly"]
    최저 = 월별["table"].nsmallest(3, "총매출")
    logger.info(f"\n[월별 추이 해석]")
    logger.info(f"- 총매출 기준 변동계수: {월별['cv_total']:.2f}%")
    logger.info(f"- 일평균 기준 변동계수: {월별['cv_daily']:.2f}%  (그 달의 일수로 나눈 뒤)")
    logger.info(
        f"- 총매출이 가장 낮은 3개월: "
        + ", ".join(
            f"{period}({int(row.일수)}일, {row.총매출 / 1_0000_0000:,.0f}억원)"
            for period, row in 최저.iterrows()
        )
    )
    if 월별["cv_daily"] < 월별["cv_total"] / 2:
        logger.info(
            f"- 월별 총매출이 출렁이는 것처럼 보이지만, 일수로 나누면 변동이 "
            f"{월별['cv_total']:.2f}% → {월별['cv_daily']:.2f}%로 줄어듭니다.\n"
            f"  즉 2월 매출이 낮은 것은 장사가 안 돼서가 아니라 그 달이 28~29일로 짧기 "
            f"때문입니다.\n"
            f"  계절성으로 오해해 2월에 판촉을 넣는 식의 판단을 하지 않도록 주의해야 합니다."
        )
    else:
        logger.info(
            f"- 일수를 보정한 뒤에도 변동이 {월별['cv_daily']:.2f}% 남아 있어, "
            f"달력 외의 요인이 있을 수 있습니다."
        )

    # ---- 상세 2: 통계 검정 ----
    logger.info("\n[상세 2] 통계 검정")
    logger.info(f"\n▶ 독립표본 t-test (Welch, 등분산 가정하지 않음)")
    logger.info(f"- 비교 그룹: {ttest['groups'][0]} vs {ttest['groups'][1]}")
    logger.info(
        f"- 표본 수  : {ttest['counts'][0]:,}건 vs {ttest['counts'][1]:,}건"
    )
    logger.info(
        f"- 평균 매출: {ttest['means'][0]:,.0f}원 vs {ttest['means'][1]:,.0f}원"
    )
    logger.info(f"- 통계량   : t = {ttest['statistic']:.4f}")
    logger.info(f"- p-value  : {ttest['pvalue']:.6f}")
    logger.info(f"- 효과크기 : Cohen's d = {ttest['cohens_d']:.4f}")
    logger.info(
        f"- 판정     : p {'<' if ttest['significant'] else '>='} {ALPHA} → "
        + (
            "차이가 있다고 판단"
            if ttest["significant"]
            else "차이가 있다는 증거를 찾지 못함 (평균이 같음을 증명한 것은 아님)"
        )
    )
    logger.info(f"- 해석     : {ttest['interpretation']}")

    logger.info(f"\n▶ 카이제곱 독립성 검정")
    logger.info(f"- 검정 변수: {chi2['columns'][0]} × {chi2['columns'][1]}")
    logger.info(
        f"- 분할표   : {chi2['table_shape'][0]}행 × {chi2['table_shape'][1]}열 "
        f"(자유도 {chi2['dof']}, 최소 기대빈도 {chi2['min_expected']:,.1f})"
    )
    logger.info(f"- 통계량   : χ² = {chi2['statistic']:.4f}")
    logger.info(f"- p-value  : {chi2['pvalue']:.6f}")
    logger.info(f"- 효과크기 : Cramér's V = {chi2['cramers_v']:.4f}")
    logger.info(
        f"- 판정     : p {'<' if chi2['associated'] else '>='} {ALPHA} → "
        + (
            "연관성이 있다고 판단"
            if chi2["associated"]
            else "연관성이 있다는 증거를 찾지 못함 (독립임을 증명한 것은 아님)"
        )
    )
    logger.info(f"- 해석     : {chi2['interpretation']}")

    # ---- 상세 3: Pipeline ----
    logger.info("\n[상세 3] sklearn Pipeline")
    logger.info(f"- 예측 대상: {TARGET_COLUMN} (거래별 매출액)")
    logger.info(f"- 수치형 변수({len(NUMERIC_FEATURES)}개): {', '.join(NUMERIC_FEATURES)} → StandardScaler")
    logger.info(
        f"- 범주형 변수({len(CATEGORICAL_FEATURES)}개): {', '.join(CATEGORICAL_FEATURES)} → OneHotEncoder"
    )
    logger.info(
        f"- 데이터 분할: 훈련 {training['train_rows']:,}행 / 검증 {training['test_rows']:,}행 "
        f"(test_size={TEST_SIZE}, random_state={RANDOM_STATE})"
    )
    logger.info(f"- Pipeline 구성: {' → '.join(name for name, _ in training['results'][0]['pipeline'].steps)}")

    머리 = pad("모델", 24) + pad("R²", 12, "right") + pad("MAE", 16, "right")
    줄 = [머리, "-" * display_width(머리)]
    for item in training["results"]:
        줄.append(
            pad(item["name"], 24)
            + pad(f"{item['r2']:.4f}", 12, "right")
            + pad(format_won(item["mae"]), 16, "right")
        )
    logger.info("\n" + "\n".join(줄))
    선형, 트리 = training["results"][0], training["results"][1]
    logger.info(
        f"\n- 두 모델은 완전히 같은 전처리(ColumnTransformer)를 쓰고 마지막 단계만 다릅니다.\n"
        f"  이 데이터의 amount 는 quantity × unit_price 로 결정되는 '곱셈' 관계입니다.\n"
        f"  선형 모델은 가중합만 표현할 수 있어 곱을 직접 만들지 못하지만, 평균 주위의\n"
        f"  1차 근사(p̄·q + q̄·p)가 잘 통해 R²={선형['r2']:.4f}까지 올라갑니다.\n"
        f"  남는 (q-q̄)(p-p̄) 교호작용 항이 전체 분산의 약 14%를 차지하고, 이것이\n"
        f"  선형 모델이 원리적으로 넘을 수 없는 한계선(이론상 최대 R² ≈ 0.86)입니다.\n"
        f"  {트리['name']} 은 구간을 나눠 이 교호작용을 학습해 R²={트리['r2']:.4f}로 그 벽을 넘습니다."
    )
    # 성능 숫자만 남으면 "매출을 잘 맞히는 모델을 만들었다"로 읽힌다.
    # 이 실습에서 확인한 것이 무엇이고 무엇이 아닌지를 분명히 적어 둔다.
    logger.info(
        f"\n- [이 결과의 한계] 예측력이 좋다는 뜻이 아닙니다.\n"
        f"  예측 대상 {TARGET_COLUMN} 가 입력 변수 quantity × unit_price 로 이미 결정되는 값이라,\n"
        f"  모델에 정답의 재료를 그대로 넣어 준 셈입니다. 여기서 확인한 것은\n"
        f"  '비선형 모델이 곱셈 관계를 선형 모델보다 잘 학습한다'는 사실과,\n"
        f"  전처리를 Pipeline 으로 묶어 두면 모델만 갈아끼워 이런 비교를 할 수 있다는 점입니다.\n"
        f"  실제 예측 과제라면 주문 시점에 아직 알 수 없는 값(예: 다음 달 수요)을 대상으로 삼고,\n"
        f"  quantity·unit_price 같은 사후 정보는 입력에서 빼야 합니다."
    )

    # ---- 상세 4: 생성 파일 ----
    logger.info("\n[상세 4] 생성된 파일")
    for 설명, 정보 in context["artifacts"].items():
        if 정보 is None:
            logger.info(f"- {설명}: (생성하지 못함)")
        else:
            logger.info(f"- {설명}: {정보['path']} ({정보['size_bytes'] / 1024:,.1f} KB)")
    logger.info(
        f"- 모델 재로딩 검증: 검증 데이터 {context['artifacts']['모델 파일']['checked_rows']}건에 대해 "
        f"원본과 재로딩 모델의 예측이 일치했습니다."
    )


# ================================================================
# 8. 실행 - 읽기 → 정제 → 시각화 → 검정 → 모델 → 저장
# ================================================================


def run_pipeline(base_dir):
    """
    [기능] 이 프로그램의 분석 절차를 처음부터 끝까지 수행한다.
    [설명] 실제 분석은 모두 여기에 모으고, main() 은 오류를 안내하는 역할만 맡는다.
           두 가지를 한 함수에 섞으면 예외 처리 블록 안에 분석 코드가 들어가
           어디까지가 정상 흐름인지 읽기 어려워지기 때문이다.

    Args:
        base_dir (Path): 산출물을 만들 기준 폴더.

    Returns:
        dict: 출력에 필요한 실행 결과 모음.

    Raises:
        FileNotFoundError: 입력 파일을 찾지 못한 경우.
        ValueError: 데이터가 비었거나 분석에 쓸 수 없는 경우.
        OSError: 필수 산출물을 저장하지 못한 경우.
        AssertionError: 재로딩한 모델의 예측이 원본과 다른 경우.
    """
    # ---- 1단계: 읽기 + 정제 -----------------------------------------------
    data_path = find_data_file(base_dir)
    frame = load_sales(data_path)
    if frame.empty:
        raise ValueError(f"거래 데이터가 비어 있습니다: {data_path}")

    # info() 는 화면에 바로 찍고 끝나므로, 버퍼로 받아야 나중에 원하는 순서로 출력할 수 있다
    buffer = io.StringIO()
    frame.info(buf=buffer)
    info_text = buffer.getvalue().rstrip()

    clean, cleaning = clean_sales(frame)
    logger.info(
        f"[1/5] 데이터 읽기·정제 완료 — "
        f"{cleaning['rows_before']:,}행 → {cleaning['rows_after']:,}행 ({data_path.name})"
    )
    describe_text = clean[NUMERIC_COLUMNS].describe().to_string()
    aggregated = aggregate_by_group(clean)
    del frame  # 원본은 이후 쓰지 않는다. 참조를 끊어야 메모리가 실제로 반환된다.

    # ---- 2단계: EDA 차트 4종 ----------------------------------------------
    font_name = setup_korean_font()
    # 월별 집계는 차트와 해석 양쪽에서 쓰므로 한 번만 계산해 함께 넘긴다
    monthly = analyze_monthly(clean)
    chart_path = create_eda_charts(clean, monthly, base_dir / CHART_FILE)
    logger.info(
        f"[2/5] EDA 차트 4종 생성 완료 — 2×2 서브플롯 "
        f"(한글 폰트: {font_name or '없음'})"
    )

    # ---- 3단계: 통계 검정 --------------------------------------------------
    ttest = run_ttest(clean)
    chi2 = run_chi2_test(clean)
    logger.info(
        f"[3/5] 통계 검정 완료 — t-test {'유의함' if ttest['significant'] else '유의하지 않음'} / "
        f"카이제곱 {'연관성 확인됨' if chi2['associated'] else '연관성 미확인'}"
    )

    # ---- 4단계: Pipeline 학습·평가·저장 ------------------------------------
    logger.info(f"[4/5] Pipeline 학습 중 — 모델 2종 비교 (전처리 동일)")
    training = train_and_evaluate(clean)
    model_info = save_and_reload_model(
        training["best"]["pipeline"], base_dir / MODEL_FILE, training["x_test"]
    )

    # ---- 5단계: Plotly 차트 ------------------------------------------------
    plotly_info = create_plotly_chart(aggregated, base_dir / PLOTLY_FILE)
    logger.info(f"[5/5] 모델·차트 저장 완료 — 재로딩 예측 일치 확인")

    return {
        "data_path": data_path,
        "info_text": info_text,
        "describe_text": describe_text,
        "cleaning": cleaning,
        "aggregated": aggregated,
        "monthly": monthly,
        "font_name": font_name,
        "ttest": ttest,
        "chi2": chi2,
        "training": training,
        "artifacts": {
            "EDA 차트": None if chart_path is None else {
                "path": chart_path, "size_bytes": chart_path.stat().st_size
            },
            "모델 파일": model_info,
            "Plotly 차트": plotly_info,
        },
    }


def main():
    """
    [기능] 프로그램 전체 흐름을 실행하고, 문제가 생기면 원인을 안내한다.
    [설명] 분석 절차는 run_pipeline() 이 맡고, 이 함수는 실패했을 때
           "무엇이 잘못됐고 어떻게 고치면 되는지"를 한글로 알려주는 역할만 한다.
           종료 코드를 구분해 돌려주므로 자동화 스케줄러에서도 성공/실패를 판단할 수 있다.

    Returns:
        int: 정상 종료면 0, 오류가 발생하면 1.
    """
    # __file__ 기준으로 경로를 잡으면 어느 폴더에서 실행하든 같은 파일을 찾는다
    base_dir = Path(__file__).resolve().parent
    setup_logging(base_dir)

    try:
        context = run_pipeline(base_dir)

    # 아래 UnicodeDecodeError 와 pandas 파서 예외는 모두 ValueError 의 하위 예외다.
    # 순서를 바꾸면 ValueError 블록에 먼저 잡혀 엉뚱한 원인을 안내하게 되므로,
    # 반드시 ValueError 보다 먼저 둔다.

    # 원본을 메모장·엑셀에서 저장하면 UTF-8 이 아닌 인코딩(CP949 등)으로 저장되는 일이 잦다.
    except UnicodeDecodeError:
        logger.error(f"[오류] 파일 인코딩이 UTF-8이 아닙니다: {DATA_FILE}")
        logger.error("       원본 파일을 UTF-8로 다시 저장한 뒤 실행해 주세요.")
        return 1
    except pd.errors.EmptyDataError:
        logger.error(f"[오류] CSV 파일에 내용이 없습니다: {DATA_FILE}")
        return 1
    except pd.errors.ParserError as error:
        logger.error(f"[오류] CSV 형식이 잘못됐습니다: {DATA_FILE}")
        logger.error(f"       {error}")
        return 1
    # 파일을 못 찾은 경우는 어디를 찾아봤는지까지 알려야 담당자가 조치할 수 있다.
    # FileNotFoundError 는 OSError 의 하위 예외라 그보다 먼저 둔다.
    except FileNotFoundError as error:
        logger.error(f"[오류] {error}")
        logger.error(f"       실습 자료의 {DATA_FILE}을 위 경로 중 한 곳에 두고 실행해 주세요.")
        return 1
    except ValueError as error:
        logger.error(f"[오류] 데이터가 예상과 다릅니다: {error}")
        return 1
    # 필수 산출물(모델·Plotly)을 저장하지 못한 경우가 여기로 온다
    except OSError as error:
        logger.error(f"[오류] 산출물을 저장하지 못했습니다: {error}")
        logger.error("       폴더 쓰기 권한과 남은 디스크 공간을 확인해 주세요.")
        return 1
    # 재로딩 검증 실패는 저장된 모델을 믿을 수 없다는 뜻이다
    except AssertionError as error:
        logger.error(f"[검증 실패] {error}")
        return 1

    # ---- 결과 출력: 결론을 먼저, 근거를 뒤에 ------------------------------
    print_summary(context)
    print_details(context)

    logger.info("\n[완료] 모든 단계를 정상 수행했습니다.")
    return 0


# 다른 파일에서 불러다 쓸 때는 실행되지 않고, 이 파일을 직접 실행할 때만 동작한다
if __name__ == "__main__":
    try:
        sys.exit(main())
    # Ctrl+C 로 중단했을 때 붉은 오류 화면 대신 한 줄 안내만 남긴다
    # (130 은 '사용자가 중단함'을 뜻하는 표준 종료 코드)
    except KeyboardInterrupt:
        logger.error("\n[중단] 사용자가 실행을 중단했습니다.")
        sys.exit(130)
    # 입력이 감당할 수 없을 만큼 큰 경우다. 무엇을 하면 되는지까지 알려준다.
    except MemoryError:
        logger.error("\n[오류] 메모리가 부족해 처리를 끝내지 못했습니다.")
        logger.error("       입력 파일을 나눠서 실행하거나 더 큰 환경에서 실행해 주세요.")
        sys.exit(1)
