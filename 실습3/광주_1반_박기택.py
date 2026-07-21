"""
================================================================
[프로그램명] 지역·카테고리별 매출 집계 - Pandas / Polars Lazy / DuckDB SQL 비교
================================================================

■ 목적
    같은 매출 집계를 세 가지 도구로 각각 구현해, 결과가 서로 같은지 확인하고
    어떤 도구가 얼마나 빠른지 비교한다. 도구 선택의 근거를 숫자로 남기는 것이 목적이다.

■ 입력
    - sales_100k.csv (매출 거래 100만 행)
      컬럼: order_id, order_date, region, category, product_name,
            quantity, unit_price, payment_method, customer_age,
            customer_gender, amount
      ※ 이 스크립트와 같은 폴더에 있어야 하며, 없으면 안내 후 종료한다.

■ 출력 (결론을 먼저, 근거를 뒤에 보여준다)
    1) 진행 상황  [1/5]~[5/5] 한 줄씩 (오래 걸리는 구간에서 멈춘 것으로 오해하지 않도록)
    2) 핵심 결과  세 도구 일치 여부 / 가장 빠른 도구 / 이상치 제거 결과 /
                  매출 1위 그룹 + 매출 상위 10개 그룹 표
    3) 이하 상세  기본 EDA(df.info() / isnull().sum() / describe()),
                  IQR 계산 내역, 결과 동일성 내역, 실행 시간 표, 자체 검증
    - Docs/result.md  (실측값으로 채워진 결과 보고서)
    - 실행로그.log    (실행 시각·진행 상황·경고 기록)

■ 처리 방식 요약
    - 세 도구가 '완전히 같은 일'을 하도록 조건을 맞춘 뒤 비교한다.
      조건이 조금이라도 다르면 결과도 시간도 비교할 의미가 없기 때문이다.
      맞춰야 하는 항목은 아래 세 가지이며, 각각 근거를 코드 주석에 남겼다.
        1) IQR 경계는 한 번만 계산해 세 도구에 같은 숫자를 넘긴다
        2) 결측 지역·카테고리는 세 도구 모두 같은 이름으로 묶는다
        3) 정렬 기준을 끝까지(동점까지) 똑같이 지정한다
    - timeit 반복 횟수는 상수 하나(TIMEIT_NUMBER)만 참조해 어긋날 수 없게 한다.
    - 표준 logging 으로 화면과 파일에 동시에 기록한다.
    - 예외 처리(파일 없음, 인코딩 오류, 컬럼 누락, 라이브러리 미설치 등)를 반영했다.

■ 오류 상황별 대응 (별도 표기가 없으면 안내 후 종료 코드 1 반환)
    - polars/duckdb 미설치        → 설치 명령을 안내
    - 입력 파일 없음/권한 없음     → 파일 경로와 원인을 안내
    - 파일 인코딩이 UTF-8 아님     → UTF-8로 다시 저장하도록 안내
    - CSV 형식 깨짐/빈 파일        → 몇 번째 줄이 문제인지 안내
    - 필수 컬럼 누락               → 실제 컬럼 목록을 함께 안내
    - amount 가 숫자 컬럼이 아님   → 실제 자료형을 함께 안내
    - IQR 필터 결과 0건            → 빈 보고서 대신 이상 상황으로 알림
    - 세 도구 결과 불일치          → 어느 도구가 어떻게 다른지 표시 (보고서는 생성)
    - 입력 파일이 매우 큼          → 예상 메모리를 경고한 뒤 계속 진행
    - 로그/보고서 파일 생성 불가   → 경고만 남기고 계속 진행 (집계는 정상 수행)
    - 집계 결과 자체 검증 실패     → 어떤 값이 어긋났는지 수치와 함께 표시
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
| v1.0   | 2026-07-21  | 박기택   | 최초 작성 (Pandas EDA + IQR 이상치  |
|        |             |          | 제거 + named aggregation 집계)     |
| v1.1   | 2026-07-21  | 박기택   | Polars Lazy API, DuckDB SQL 집계   |
|        |             |          | 추가 및 세 도구 결과 일치 검증     |
| v1.2   | 2026-07-21  | 박기택   | timeit 성능 비교 추가. 세 도구가   |
|        |             |          | 같은 반복 횟수를 쓰도록 상수 일원화 |
| v1.3   | 2026-07-21  | 박기택   | 도구별 결과 불일치 원인 3건 제거.  |
|        |             |          | (1) IQR 경계 1회 계산 후 공유      |
|        |             |          | (2) 결측 그룹 이름 통일            |
|        |             |          | (3) 동점 정렬 기준까지 통일        |
| v1.4   | 2026-07-21  | 박기택   | 결과 보고서(Docs/result.md) 자동   |
|        |             |          | 생성 및 예외 처리·자체 검증 보강   |
| v1.5   | 2026-07-21  | 박기택   | 측정 신뢰도 개선. 20회 표본 실측을 |
|        |             |          | 근거로 반복 횟수를 3→10회로 올리고 |
|        |             |          | 측정 전 예열 1회를 추가. 도구 간   |
|        |             |          | 배수의 흔들림이 ±9%→±3.5%로 감소   |
| v1.6   | 2026-07-21  | 박기택   | 출력 순서를 결론 우선으로 재구성.  |
|        |             |          | info()·describe() 를 먼저 찍느라  |
|        |             |          | 결론이 화면 아래로 밀리던 문제를   |
|        |             |          | 해소. 계산과 출력을 분리해         |
|        |             |          | 핵심 결과 → 상세 순으로 표시하고,  |
|        |             |          | 금액을 억·만 단위로, 표는 한글 폭  |
|        |             |          | 을 고려해 정렬                     |
================================================================
"""

import io
import logging
import sys
import timeit
import unicodedata
from collections import namedtuple
from pathlib import Path

# 세 도구 중 하나라도 없으면 이 프로그램은 목적(비교)을 달성할 수 없다.
# 실행 도중 갑자기 죽는 대신, 시작하자마자 설치 방법을 알려주고 끝낸다.
try:
    import duckdb
    import pandas as pd
    import polars as pl
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

# 실행 기록을 남길 파일. 화면 출력과 별개로 시각·진행 상황·경고가 쌓인다.
LOG_FILE = "실행로그.log"

# 실측값으로 채워질 결과 보고서. 양식은 Docs/resultEx.md 를 따른다.
REPORT_FILE = "result.md"

# 집계 기준(그룹 키)과 집계 대상. 요구사항이 바뀌면 이 두 값만 고치면 된다.
GROUP_KEYS = ["region", "category"]
TARGET_COLUMN = "amount"

# 원본에 반드시 있어야 하는 컬럼. 하나라도 없으면 집계 자체가 성립하지 않는다.
REQUIRED_COLUMNS = (*GROUP_KEYS, TARGET_COLUMN)

# ★ 세 도구가 공유하는 단 하나의 반복 횟수.
#   도구마다 따로 적으면 값이 어긋나 비교가 불공정해진다.
#   여기 한 곳만 두고 세 곳에서 참조하게 해서, 애초에 어긋날 수 없게 만든다.
#
#   10으로 정한 근거 (20회 표본으로 실측):
#   가장 빠른 Polars 는 1회가 약 0.04초라 실행 시간이 짧아 잡음에 취약하다.
#   'Pandas 대비 배수'의 흔들림 폭을 재보면 N=1 일 때 ±20%, N=3 일 때 ±9%,
#   N=10 일 때 ±3.5% 로 줄어든다. N=20 은 시간만 두 배 들고 개선폭은 미미해
#   10을 기준으로 잡았다. 전체 측정 시간은 약 7초로 부담이 없다.
TIMEIT_NUMBER = 10

# 측정 전에 버리는 예열 실행 횟수.
#   첫 실행은 운영체제의 파일 캐시가 비어 있고 엔진 초기화도 함께 일어난다.
#   실측 결과 Polars 의 첫 실행은 이후 실행보다 약 68% 느렸다(0.066초 vs 0.039초).
#   이 한 번을 측정에 넣으면 '도구가 느리다'가 아니라 '캐시가 차갑다'를 재게 된다.
#   따라서 한 번 돌려 조건을 맞춘 뒤 본 측정을 시작한다.
WARMUP_NUMBER = 1

# IQR 이상치 판정 계수. 통상 1.5를 쓰며, 더 엄격/느슨하게 보려면 이 값을 조정한다.
IQR_FACTOR = 1.5

# 값이 비어 있는 행도 집계에서 누락되지 않도록, 빈 값 대신 쓸 이름을 정해둔다.
# 세 도구가 모두 이 이름을 쓰기 때문에 결측 그룹의 처리 방식 차이가 사라진다.
UNKNOWN_REGION = "미상"
UNKNOWN_CATEGORY = "미분류"

# 보고서와 화면에 보여줄 상위 집계 건수 (전부 찍으면 읽기 어렵다)
TOP_N = 10

# 입력 파일이 이 크기를 넘으면 메모리 사용량을 미리 경고한다.
LARGE_FILE_WARN_BYTES = 100 * 1024 * 1024

# 부동소수 비교 허용 오차.
# 합계를 더하는 순서가 도구마다 달라 맨 끝자리가 미세하게 어긋날 수 있는데,
# 이는 계산이 틀린 것이 아니므로 이 범위 안이면 같은 값으로 본다.
FLOAT_TOLERANCE = 1e-9

# 집계 결과의 최종 컬럼 순서. 세 도구의 결과를 이 형태로 통일한 뒤 비교한다.
RESULT_COLUMNS = [*GROUP_KEYS, "total", "mean", "count"]

# 화면과 파일에 동시에 기록하기 위한 기록 담당자(logger)
logger = logging.getLogger("practice3")

# IQR 계산 결과를 한 덩어리로 들고 다니기 위한 형태.
# 다섯 개 숫자를 따로 넘기면 인자 순서를 헷갈리기 쉬워 하나로 묶었다.
IQRBounds = namedtuple("IQRBounds", ("q1", "q3", "iqr", "lower", "upper"))

# 성능 측정 결과 한 건.
BenchResult = namedtuple("BenchResult", ("tool", "number", "total_sec", "mean_sec"))


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
            # 앞뒤 줄바꿈은 화면 여백용이므로 파일에서는 뺀다.
            # 중간에 낀 줄바꿈은 공백으로 이어 붙여 기록 한 건이 쪼개지지 않게 한다.
            record.msg = original.strip().replace("\n", " ")
        try:
            return super().format(record)
        # 같은 기록을 화면 담당자도 함께 쓰므로, 원래 내용으로 반드시 되돌린다
        finally:
            record.msg = original


def setup_logging(base_dir):
    """
    [기능] 실행 기록을 화면과 파일 양쪽에 남기도록 준비한다.
    [설명] 화면에는 보고서만 깔끔하게 보이고, 파일에는 시각과 심각도까지 함께 남는다.
           나중에 "언제 돌렸고 무슨 경고가 있었나"를 확인할 수 있어야 하기 때문이다.
           로그 파일을 만들지 못하더라도 집계 자체는 문제가 없으므로,
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
    # 파일에는 전용 서식을 쓴다. 화면용 빈 줄이 그대로 들어가면 기록 한 건이 두 줄로 쪼개진다.
    file_handler.setFormatter(
        LogFileFormatter("%(asctime)s [%(levelname)s] %(message)s")
    )
    logger.addHandler(file_handler)
    return log_path


# ================================================================
# 2. 데이터 읽기와 기초 탐색(EDA)
# ================================================================


def find_data_file(base_dir, filename=None):
    """
    [기능] 입력 파일을 스크립트 폴더와 그 상위 폴더에서 찾는다.
    [설명] 이 스크립트는 저장소에서 `실습3/` 안에 있고 원본 CSV 는 저장소 루트에 있다.
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
           확인하고 넘긴다. 집계에 꼭 필요한 컬럼이 없으면 뒤늦게 이상한 오류가 나는 대신
           지금 바로 무엇이 없는지 알려준다.

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

    # 컬럼 누락은 데이터 제공처의 실수이므로, 조용히 넘기지 않고 명확히 알린다
    missing = [name for name in REQUIRED_COLUMNS if name not in frame.columns]
    if missing:
        raise ValueError(
            f"필수 컬럼이 없습니다: {missing} / 실제 컬럼: {list(frame.columns)}"
        )

    # amount 가 문자열로 읽히면 IQR 계산과 합계가 전부 엉뚱한 값이 된다.
    # 숫자로 다룰 수 있는지 여기서 한 번만 확인하고 넘어간다.
    #
    # 머리글만 있고 데이터가 없는 파일은 자료형을 판단할 근거가 없어 문자열로 읽힌다.
    # 그 상태로 검사하면 "amount 가 숫자가 아니다"라는 엉뚱한 안내가 나가므로,
    # 빈 데이터는 여기서 통과시키고 호출한 쪽이 '데이터 없음'으로 정확히 알리게 한다.
    if not frame.empty and not pd.api.types.is_numeric_dtype(frame[TARGET_COLUMN]):
        raise ValueError(
            f"'{TARGET_COLUMN}' 컬럼이 숫자가 아닙니다 "
            f"(실제 자료형: {frame[TARGET_COLUMN].dtype})"
        )

    return frame


def collect_eda(frame):
    """
    [기능] 기본 탐색(EDA) 결과를 모아서 돌려준다. (화면 출력은 하지 않는다)
    [설명] 집계를 시작하기 전에 "이 데이터가 어떻게 생겼는지"를 확인하는 단계다.
           행·열 수, 자료형, 결측치, 기초 통계를 보면 이후 결과가 이상할 때
           데이터 탓인지 코드 탓인지 구분할 수 있다.

           여기서 화면에 바로 찍지 않고 값만 모아 돌려주는 이유는 출력 순서 때문이다.
           info()·describe() 는 수십 줄이라, 먼저 찍으면 정작 중요한 결론
           (세 도구 일치 여부, 성능 순위)이 화면 아래로 밀려 스크롤해야 보인다.
           계산과 출력을 나눠두면 print_summary() 가 결론을 먼저 보여주고
           print_details() 가 근거를 뒤에 붙일 수 있다.

           df.info() 는 화면에 직접 찍는 함수라 반환값이 없다.
           그래서 버퍼로 받아 문자열로 만들어 둔다.

    Args:
        frame (pandas.DataFrame): 원본 매출 데이터.

    Returns:
        dict: 보고서·상세 출력에 쓸 요약값.
              - rows / columns : 행 수, 열 수
              - info_text      : df.info() 출력 전문
              - null_counts    : {컬럼명: 결측치 수}
              - describe_text  : df.describe() 출력 전문
    """
    # info() 는 화면에 바로 찍고 끝나므로, 버퍼로 받아야 나중에 다시 쓸 수 있다
    buffer = io.StringIO()
    frame.info(buf=buffer)
    info_text = buffer.getvalue().rstrip()

    null_counts = frame.isnull().sum()
    describe_text = frame.describe().to_string()

    return {
        "rows": len(frame),
        "columns": frame.shape[1],
        "info_text": info_text,
        "null_counts": null_counts.to_dict(),
        "describe_text": describe_text,
    }


# ================================================================
# 3. IQR 이상치 기준 계산
# ================================================================


def compute_iqr_bounds(series):
    """
    [기능] IQR 방식으로 '정상 범위'의 하한과 상한을 계산한다.
    [설명] 매출에는 자릿수가 다른 극단값이 섞이기 마련이고, 그 몇 건이 평균을 통째로
           왜곡한다. IQR 은 가운데 50% 구간의 폭을 기준 삼아 "이 정도를 벗어나면
           이상치로 본다"를 정하는 방법이다.

               IQR = Q3 - Q1
               하한 = Q1 - 1.5 × IQR
               상한 = Q3 + 1.5 × IQR

           이 경계는 여기서 딱 한 번만 계산해 세 도구에 같은 숫자로 넘긴다.
           도구마다 따로 계산하면 분위수 보간 방식이 달라(예: Polars 기본값은 nearest,
           Pandas·DuckDB 는 linear) 경계가 미세하게 어긋나고, 그러면 걸러지는 행이 달라져
           결과 비교 자체가 무의미해지기 때문이다.

    Args:
        series (pandas.Series): 기준으로 삼을 수치 컬럼 (여기서는 amount).

    Returns:
        IQRBounds: q1, q3, iqr, lower, upper 를 담은 계산 결과.

    Raises:
        ValueError: 값이 모두 비어 있어 분위수를 계산할 수 없는 경우.
    """
    # 결측치를 뺀 값이 하나도 없으면 분위수가 NaN 이 되고, 이후 필터가 전부 거짓이 된다.
    # 원인을 알기 어려운 '0건' 결과 대신 여기서 바로 알린다.
    if series.dropna().empty:
        raise ValueError(f"'{TARGET_COLUMN}' 컬럼에 유효한 값이 없어 IQR을 계산할 수 없습니다.")

    q1 = float(series.quantile(0.25))
    q3 = float(series.quantile(0.75))
    iqr = q3 - q1
    return IQRBounds(
        q1=q1,
        q3=q3,
        iqr=iqr,
        lower=q1 - IQR_FACTOR * iqr,
        upper=q3 + IQR_FACTOR * iqr,
    )


# ================================================================
# 4. 세 도구의 집계 - 조건을 똑같이 맞춘 뒤 각자의 문법으로 구현
# ================================================================
#
# 세 함수는 모두 아래 조건을 똑같이 수행한다.
#   1) CSV 파일 읽기                     ← 성능 측정에 읽기 시간까지 포함한다
#   2) amount 결측 제외 + IQR 정상 범위만 남기기
#   3) region/category 결측을 '미상'/'미분류' 로 치환
#   4) region·category 로 묶어 total/mean/count 계산
#   5) total 내림차순 정렬 (동점이면 region, category 오름차순)
#
# 3)이 필요한 이유:
#   Pandas 의 groupby 는 기본적으로 결측(NaN) 그룹을 결과에서 빼버리는 반면,
#   Polars 와 DuckDB 는 결측을 하나의 그룹으로 남긴다. 이 데이터에는 결측 지역이
#   1만 건, 결측 카테고리가 8천 건 있어서, 그냥 두면 세 결과가 반드시 달라진다.
#   미리 같은 이름으로 채워두면 그 차이가 아예 생기지 않는다.
#
# 5)에서 동점 기준까지 지정하는 이유:
#   total 만으로 정렬하면 값이 같은 행들의 순서가 도구마다 달라진다.
#   비교는 행 순서까지 맞춰서 하므로, 어떤 데이터가 와도 순서가 하나로 정해지도록
#   그룹 키까지 정렬 기준에 넣는다.


def aggregate_pandas(path, bounds):
    """
    [기능] Pandas 로 region·category별 총매출·평균·건수를 집계한다.
    [설명] named aggregation(`total=('amount','sum')` 형태)을 사용해 결과 컬럼 이름을
           직접 지정한다. `agg({'amount': 'sum'})` 방식은 컬럼 이름이 원본 이름 그대로
           남아, 세 도구의 결과를 나란히 비교할 때 이름을 다시 바꿔야 한다.

    Args:
        path (Path | str): 읽어들일 CSV 파일 경로.
        bounds (IQRBounds): 세 도구가 공유하는 IQR 정상 범위.

    Returns:
        pandas.DataFrame: region, category, total, mean, count 컬럼을 가진 집계 결과.
    """
    frame = pd.read_csv(path, encoding="utf-8-sig")

    # between() 은 하한 이상 & 상한 이하를 뜻한다 (양쪽 끝 포함).
    # amount 가 결측이면 between() 결과가 거짓이 되어 자연히 빠지지만,
    # "결측을 뺀다"는 의도를 코드에 드러내려고 조건을 명시적으로 함께 적는다.
    clean = frame[
        frame[TARGET_COLUMN].notna()
        & frame[TARGET_COLUMN].between(bounds.lower, bounds.upper)
    ]

    # 결측 그룹을 버리지 않고 이름을 붙여 살린다 (매출 누락 방지 + 도구 간 동작 통일)
    clean = clean.fillna({"region": UNKNOWN_REGION, "category": UNKNOWN_CATEGORY})

    return (
        clean.groupby(GROUP_KEYS, as_index=False)
        .agg(
            total=(TARGET_COLUMN, "sum"),
            mean=(TARGET_COLUMN, "mean"),
            count=(TARGET_COLUMN, "count"),
        )
        .sort_values(["total", *GROUP_KEYS], ascending=[False, True, True])
    )


def aggregate_polars(path, bounds):
    """
    [기능] Polars Lazy API 로 같은 집계를 수행한다.
    [설명] scan_csv 는 파일을 즉시 읽지 않고 '무엇을 할지'만 기록해 둔다.
           collect() 를 부르는 순간 전체 계획을 한 번에 최적화해서 실행하므로,
           필요 없는 컬럼은 아예 읽지 않고 필터도 읽는 중에 적용된다.
           read_csv(즉시 실행)를 쓰면 이 최적화가 사라지므로 반드시 scan_csv 를 쓴다.

           체인 끝의 collect() 를 빠뜨리면 실행 계획(LazyFrame)만 남고
           계산은 한 번도 일어나지 않는다.

    Args:
        path (Path | str): 읽어들일 CSV 파일 경로.
        bounds (IQRBounds): 세 도구가 공유하는 IQR 정상 범위.

    Returns:
        pandas.DataFrame: 다른 도구와 비교할 수 있도록 Pandas 형태로 변환한 집계 결과.
    """
    result = (
        pl.scan_csv(path)  # 계획만 세운다 (아직 파일을 읽지 않음)
        .filter(
            pl.col(TARGET_COLUMN).is_not_null()
            & pl.col(TARGET_COLUMN).is_between(bounds.lower, bounds.upper)
        )
        .with_columns(
            pl.col("region").fill_null(UNKNOWN_REGION),
            pl.col("category").fill_null(UNKNOWN_CATEGORY),
        )
        .group_by(GROUP_KEYS)
        .agg(
            total=pl.col(TARGET_COLUMN).sum(),
            mean=pl.col(TARGET_COLUMN).mean(),
            count=pl.col(TARGET_COLUMN).count(),
        )
        .sort(["total", *GROUP_KEYS], descending=[True, False, False])
        .collect()  # 여기서 비로소 실행된다
    )
    # 세 도구의 결과를 같은 방식으로 비교하려면 형태를 하나로 맞춰야 한다
    return result.to_pandas()


def aggregate_duckdb(connection, path, bounds):
    """
    [기능] DuckDB SQL 로 같은 집계를 수행한다.
    [설명] CSV 파일을 테이블처럼 직접 조회할 수 있어, 별도 적재 없이 SQL 한 문장으로 끝난다.
           COALESCE 는 앞의 값이 NULL 이면 뒤의 값을 쓰는 함수로,
           다른 두 도구의 fillna/fill_null 과 같은 역할을 한다.

           값을 SQL 문자열에 직접 이어 붙이지 않고 ? 자리표시자로 넘기는 이유:
           경로에 따옴표가 들어가거나 소수점 표기가 달라져도 안전하고,
           같은 문장을 반복 실행할 때 다시 해석하지 않아도 되기 때문이다.

    Args:
        connection (duckdb.DuckDBPyConnection): 재사용할 DuckDB 연결.
        path (Path | str): 조회할 CSV 파일 경로.
        bounds (IQRBounds): 세 도구가 공유하는 IQR 정상 범위.

    Returns:
        pandas.DataFrame: region, category, total, mean, count 컬럼을 가진 집계 결과.
    """
    query = f"""
        SELECT COALESCE(region,   ?) AS region,
               COALESCE(category, ?) AS category,
               SUM({TARGET_COLUMN})   AS total,
               AVG({TARGET_COLUMN})   AS mean,
               COUNT({TARGET_COLUMN}) AS count
        FROM read_csv_auto(?)
        WHERE {TARGET_COLUMN} IS NOT NULL
          AND {TARGET_COLUMN} BETWEEN ? AND ?
        GROUP BY 1, 2
        ORDER BY total DESC, region ASC, category ASC
    """
    parameters = [
        UNKNOWN_REGION,
        UNKNOWN_CATEGORY,
        str(path),
        bounds.lower,
        bounds.upper,
    ]
    return connection.execute(query, parameters).df()


# ================================================================
# 5. 결과 비교 - 세 도구가 정말 같은 답을 냈는지 확인
# ================================================================


def normalize_result(frame):
    """
    [기능] 집계 결과를 비교할 수 있는 하나의 표준 형태로 맞춘다.
    [설명] 도구마다 컬럼 순서와 행 번호(index) 매기는 방식이 다르다.
           그 차이 때문에 '값은 같은데 다르다'고 판정되는 일을 막으려면,
           비교 전에 컬럼 순서·정렬·행 번호를 똑같이 정리해야 한다.

    Args:
        frame (pandas.DataFrame): 어느 한 도구의 집계 결과.

    Returns:
        pandas.DataFrame: 컬럼 순서와 정렬, 행 번호가 통일된 결과.
    """
    return (
        frame[RESULT_COLUMNS]
        .sort_values(["total", *GROUP_KEYS], ascending=[False, True, True])
        .reset_index(drop=True)
    )


def compare_results(left, right):
    """
    [기능] 두 집계 결과가 같은지 판정한다.
    [설명] 값이 정말 같아도 완전 일치 비교는 실패할 수 있다. 합계를 더하는 순서가
           도구마다 달라 부동소수 맨 끝자리가 미세하게 어긋나고, 건수의 자료형도
           도구마다 다르기 때문이다(int64 vs uint32).
           그래서 자료형은 보지 않고, 숫자는 아주 작은 오차까지만 허용해 비교한다.

    Args:
        left (pandas.DataFrame): 기준이 되는 결과.
        right (pandas.DataFrame): 비교할 결과.

    Returns:
        tuple[bool, str]: (일치 여부, 다를 경우의 사유. 같으면 빈 문자열)
    """
    try:
        pd.testing.assert_frame_equal(
            normalize_result(left),
            normalize_result(right),
            check_dtype=False,
            rtol=FLOAT_TOLERANCE,
        )
    except AssertionError as error:
        # 메시지가 여러 줄로 길게 나오므로 앞부분만 사유로 남긴다
        return False, str(error).strip().splitlines()[0]
    return True, ""


# ================================================================
# 6. 성능 비교 - 세 도구를 같은 조건에서 측정
# ================================================================


def benchmark(cases, number=TIMEIT_NUMBER):
    """
    [기능] 도구별 집계 함수의 실행 시간을 같은 반복 횟수로 측정한다.
    [설명] 비교가 공정하려면 네 가지가 같아야 한다.
           (1) 하는 일   - 세 함수 모두 '파일 읽기부터 정렬까지'를 수행한다
           (2) 반복 횟수 - number 를 인자로 한 번만 받아 모든 도구에 그대로 적용한다
           (3) 측정 방식 - 같은 timeit 호출로 잰다
           (4) 시작 조건 - 모든 도구를 똑같이 한 번 예열한 뒤 측정을 시작한다
           특히 (2)를 도구마다 다르게 주면 총시간 비교가 아무 의미도 없어지므로,
           이 함수 안에서 반복을 돌며 같은 number 를 쓰도록 구조로 못박아 두었다.

           (4)가 필요한 이유는 첫 실행에만 붙는 비용이 있기 때문이다.
           파일을 처음 읽을 때는 운영체제 캐시가 비어 있고 엔진 초기화도 함께 일어난다.
           이 비용은 도구의 집계 성능이 아니므로, 한 번 돌려 조건을 맞춘 뒤 측정한다.
           예열 결과는 쓰지 않고 버린다.

    Args:
        cases (list[tuple[str, callable]]): (도구 이름, 인자 없이 호출 가능한 함수) 목록.
        number (int): 각 도구를 반복 실행할 횟수. 기본값은 TIMEIT_NUMBER.

    Returns:
        list[BenchResult]: 총시간이 짧은 순으로 정렬된 측정 결과.

    Raises:
        ValueError: 반복 횟수가 1 미만인 경우.
    """
    if number < 1:
        raise ValueError(f"timeit 반복 횟수는 1 이상이어야 합니다 (입력값: {number})")

    results = []
    for tool, function in cases:
        # 예열: 결과를 버리는 실행. 세 도구 모두 같은 횟수로 돌려 조건을 맞춘다.
        timeit.timeit(function, number=WARMUP_NUMBER)

        # 같은 number 변수를 그대로 넘긴다. 도구별로 값을 바꿀 여지를 두지 않는다.
        total_sec = timeit.timeit(function, number=number)
        results.append(
            BenchResult(
                tool=tool,
                number=number,
                total_sec=total_sec,
                mean_sec=total_sec / number,
            )
        )
        # 측정이 길어 멈춘 것으로 오해하지 않도록 도구 단위로만 진행 상황을 알린다.
        # 자세한 수치는 모든 측정이 끝난 뒤 표로 한 번에 보여준다.
        logger.info(f"  · {tool} 측정 완료")

    return sorted(results, key=lambda item: item.total_sec)


# ================================================================
# 7. 검증 - 보고 전에 숫자가 맞는지 스스로 점검
# ================================================================


def verify_results(result, bounds, kept_rows):
    """
    [기능] 집계 결과가 신뢰할 수 있는 값인지 자동으로 점검한다.
    [설명] 잘못된 매출 숫자가 그대로 보고되는 일을 막기 위한 안전장치다.
           정답을 미리 적어두고 대조하는 방식은 데이터가 바뀌는 순간 무의미해지므로,
           '어떤 데이터를 넣어도 반드시 성립해야 하는 관계'만 확인한다.

    Args:
        result (pandas.DataFrame): 집계 결과 (컬럼: region, category, total, mean, count).
        bounds (IQRBounds): 적용한 IQR 정상 범위.
        kept_rows (int): IQR 필터를 통과한 원본 행 수.

    Raises:
        AssertionError: 점검 항목 중 하나라도 어긋나는 경우.
    """
    # 하한이 상한보다 크면 필터가 아무것도 통과시키지 못한다 (계산식이 뒤집힌 경우)
    assert bounds.lower <= bounds.upper, (
        f"IQR 하한이 상한보다 큽니다. 하한={bounds.lower}, 상한={bounds.upper}"
    )

    # 결과 컬럼 이름이 어긋나면 세 도구 비교와 보고서가 통째로 틀어진다
    assert list(result.columns) == RESULT_COLUMNS, (
        f"결과 컬럼이 예상과 다릅니다. 기대={RESULT_COLUMNS}, 실제={list(result.columns)}"
    )

    # 그룹별 건수를 모두 더하면 필터를 통과한 행 수와 같아야 한다 (집계 누락 확인)
    counted = int(result["count"].sum())
    assert counted == kept_rows, (
        f"그룹별 건수 합이 필터 통과 행 수와 다릅니다. "
        f"건수 합={counted:,}건, 필터 통과={kept_rows:,}건"
    )

    # 요구사항이 '총매출 내림차순'이므로 정렬이 실제로 그렇게 되어 있는지 확인한다
    totals = result["total"].tolist()
    assert totals == sorted(totals, reverse=True), (
        "집계 결과가 총매출 내림차순으로 정렬되어 있지 않습니다."
    )

    # 평균 × 건수 = 합계 라는 관계가 깨졌다면 집계 대상이 서로 다른 행이었다는 뜻이다
    recomputed = result["mean"] * result["count"]
    assert (recomputed - result["total"]).abs().max() <= abs(
        result["total"]
    ).max() * FLOAT_TOLERANCE, "평균 × 건수가 총매출과 일치하지 않습니다."

    # 이상치가 남아 있으면 총매출이 부풀려진다. 그룹 평균은 반드시 정상 범위 안이어야 한다.
    assert result["mean"].between(bounds.lower, bounds.upper).all(), (
        "IQR 정상 범위를 벗어난 값이 집계에 포함되었습니다."
    )


# ================================================================
# 8. 보고서 작성 - 실측값으로 Docs/result.md 생성
# ================================================================


def format_table(result, top_n=TOP_N):
    """
    [기능] 집계 결과 상위 N개를 마크다운 표의 본문 줄로 만든다.
    [설명] 보고서 작성 함수가 길어지지 않도록 표 만드는 일만 따로 떼어냈다.
           숫자는 천 단위 구분과 소수점 자리를 맞춰 사람이 읽기 쉽게 정리한다.

    Args:
        result (pandas.DataFrame): 집계 결과.
        top_n (int): 표에 넣을 상위 건수.

    Returns:
        str: 마크다운 표의 본문 (헤더 제외).
    """
    lines = []
    for rank, row in enumerate(result.head(top_n).itertuples(index=False), start=1):
        lines.append(
            f"| {rank} | {row.region} | {row.category} | "
            f"{row.total:,.0f} | {row.mean:,.2f} | {row.count:,} |"
        )
    return "\n".join(lines)


def format_won(value):
    """
    [기능] 큰 금액을 억·조 단위로 바꿔 읽기 쉽게 만든다.
    [설명] 74,992,750,244원 같은 숫자는 자릿수를 세어야 규모가 잡힌다.
           '749.9억원'으로 보여주면 한눈에 들어와, 보고를 받는 쪽이 숫자를
           해석하는 데 드는 시간이 줄어든다.

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


def format_result_table(result, top_n=TOP_N):
    """
    [기능] 집계 결과 상위 N개를 화면에서 읽기 좋은 표로 만든다.
    [설명] DataFrame 을 그대로 찍으면 총매출이 7.499275e+10 같은 지수 표기로 나와
           규모가 한눈에 들어오지 않는다. 금액을 억·만 단위로 바꾸고
           한글 폭을 고려해 자리를 맞추면 표를 그대로 보고에 쓸 수 있다.

    Args:
        result (pandas.DataFrame): 집계 결과.
        top_n (int): 표에 넣을 상위 건수.

    Returns:
        str: 여러 줄로 된 표 문자열.
    """
    머리 = (
        pad("순위", 5)
        + pad("region", 8)
        + pad("category", 10)
        + pad("총매출", 13, "right")
        + pad("평균", 12, "right")
        + pad("건수", 10, "right")
    )
    줄 = [머리, "-" * display_width(머리)]
    for rank, row in enumerate(result.head(top_n).itertuples(index=False), start=1):
        줄.append(
            pad(str(rank), 5)
            + pad(row.region, 8)
            + pad(row.category, 10)
            + pad(format_won(row.total), 13, "right")
            + pad(format_won(row.mean), 12, "right")
            + pad(f"{row.count:,}", 10, "right")
        )
    return "\n".join(줄)


def print_summary(context):
    """
    [기능] 이 실습에서 알고자 한 결론만 추려 화면 맨 앞에 보여준다.
    [설명] 실행하면 가장 먼저 이 블록이 보인다. 근거가 되는 상세 수치는 뒤에 따로 붙는다.
           원래는 EDA 결과부터 순서대로 찍었는데, info()·describe() 만 수십 줄이라
           정작 알고 싶은 '세 도구가 같은 답을 냈는가', '어느 쪽이 빠른가'가
           화면 아래로 밀려 스크롤해야 보였다.
           보고를 받는 사람이 먼저 볼 것은 과정이 아니라 결론이므로 순서를 뒤집었다.

    Args:
        context (dict): run_pipeline() 이 돌려준 실행 결과 모음.

    Returns:
        None: 화면과 로그 파일에 기록만 수행한다.
    """
    result = context["result"]
    benchmarks = context["benchmarks"]
    pandas_time = next(item.total_sec for item in benchmarks if item.tool == "Pandas")
    fastest = benchmarks[0]
    top = result.iloc[0]

    all_match = all(context["matches"].values())
    match_text = (
        f"일치 (Pandas = Polars = DuckDB, {len(result)}개 그룹)"
        if all_match
        else "불일치 — 아래 상세의 '결과 동일성' 항목을 확인하세요"
    )
    # 1회 평균을 빠른 순으로 나열해 순위와 실제 격차를 한 줄에 담는다
    speed_text = " < ".join(
        f"{item.tool} {item.mean_sec:.4f}초" for item in benchmarks
    )
    removed_ratio = context["rows_removed"] / context["rows_before"] * 100

    logger.info("\n" + "=" * 72)
    logger.info(" 핵심 결과")
    logger.info("=" * 72)
    logger.info(f" [1] 세 도구 집계 결과   {match_text}")
    logger.info(
        f" [2] 가장 빠른 도구      {fastest.tool} "
        f"— Pandas 대비 {pandas_time / fastest.total_sec:.2f}배"
    )
    logger.info(f"                         {speed_text} (1회 평균)")
    logger.info(
        f" [3] 결측·이상치 제외     {context['rows_before']:,}행 → "
        f"{context['rows_after']:,}행 "
        f"(총 {context['rows_removed']:,}건 = 결측 {context['missing_removed']:,} "
        f"+ 범위 밖 {context['outlier_removed']:,}, {removed_ratio:.1f}%)"
    )
    logger.info(
        f" [4] 매출 1위 그룹       {top.region}·{top.category} "
        f"{format_won(top.total)} ({top['count']:,}건, 평균 {format_won(top['mean'])})"
    )
    logger.info("=" * 72)
    logger.info(f"\n[매출 상위 {TOP_N}개 그룹]\n{format_result_table(result)}")


def print_details(context):
    """
    [기능] 핵심 결과의 근거가 되는 상세 수치를 순서대로 보여준다.
    [설명] 결론만 보고 넘어가도 되지만, 숫자를 확인하려는 사람에게는 근거가 필요하다.
           요구사항이 요구하는 df.info()·isnull().sum() 출력도 여기에 포함된다.
           결론(print_summary)과 근거(여기)를 나눠 두면, 보는 사람이 필요한 깊이까지만
           읽고 멈출 수 있다.

    Args:
        context (dict): run_pipeline() 이 돌려준 실행 결과 모음.

    Returns:
        None: 화면과 로그 파일에 기록만 수행한다.
    """
    eda = context["eda"]
    bounds = context["bounds"]

    logger.info("\n" + "-" * 72)
    logger.info(" 이하 상세")
    logger.info("-" * 72)

    logger.info("\n[상세 1] 기초 탐색(EDA)")
    logger.info(f"- 데이터 크기: {eda['rows']:,}행 × {eda['columns']}열")
    logger.info(f"\n[df.info()]\n{eda['info_text']}")
    null_text = "\n".join(
        f"{name:<18}{count:>10,}" for name, count in eda["null_counts"].items()
    )
    logger.info(f"\n[isnull().sum()]\n{null_text}")
    logger.info(f"\n[describe()]\n{eda['describe_text']}")

    logger.info("\n[상세 2] IQR 이상치 제거")
    logger.info(
        f"- Q1 = {bounds.q1:,.2f} / Q3 = {bounds.q3:,.2f} / IQR = {bounds.iqr:,.2f}"
    )
    logger.info(
        f"- 정상 범위 = [{bounds.lower:,.2f}, {bounds.upper:,.2f}] "
        f"(Q1 - {IQR_FACTOR}×IQR ~ Q3 + {IQR_FACTOR}×IQR)"
    )
    logger.info(f"- 제거 전 행 수: {context['rows_before']:,}행")
    logger.info(f"- 제거 후 행 수: {context['rows_after']:,}행")
    logger.info(f"- 제외된 행: 총 {context['rows_removed']:,}건")
    # 제거 사유를 나눠 보고한다. 한 숫자로만 내면 전부 이상치였다고 오해한다.
    logger.info(f"    · {TARGET_COLUMN} 결측으로 제외 : {context['missing_removed']:,}건")
    logger.info(f"    · IQR 범위 밖으로 제외  : {context['outlier_removed']:,}건")

    logger.info("\n[상세 3] 세 도구 결과 동일성")
    for name, ok in context["matches"].items():
        logger.info(f"- {name}: {'일치' if ok else '불일치'}")
    for name, reason in context["mismatch_reasons"].items():
        logger.warning(f"  └ {name} 차이: {reason}")

    logger.info(
        f"\n[상세 4] 실행 시간 (timeit, 세 도구 모두 number={TIMEIT_NUMBER}, "
        f"예열 {WARMUP_NUMBER}회 후 측정)"
    )
    pandas_time = next(
        item.total_sec for item in context["benchmarks"] if item.tool == "Pandas"
    )
    logger.info(f"{'순위':<5}{'도구':<9}{'총시간(초)':>12}{'1회평균(초)':>13}{'Pandas대비':>12}")
    for rank, item in enumerate(context["benchmarks"], start=1):
        logger.info(
            f"{rank:<6}{item.tool:<10}{item.total_sec:>10.4f}"
            f"{item.mean_sec:>13.4f}{pandas_time / item.total_sec:>11.2f}배"
        )

    logger.info("\n[상세 5] 자체 검증: 모든 assert 통과")


def build_report(context):
    """
    [기능] 실행 결과를 Docs/resultEx.md 양식에 맞춘 마크다운 보고서 문자열로 만든다.
    [설명] 보고서를 손으로 채우면 값을 옮겨 적다가 틀리거나, 코드를 고친 뒤 보고서만
           옛날 값으로 남는 일이 생긴다. 실행할 때마다 실측값으로 다시 쓰면
           코드와 보고서가 어긋날 수 없다.

    Args:
        context (dict): main() 이 모아둔 실행 결과 모음.

    Returns:
        str: 완성된 마크다운 문서 전문.
    """
    eda = context["eda"]
    bounds = context["bounds"]
    result = context["result"]
    benchmarks = context["benchmarks"]
    matches = context["matches"]

    # 가장 빠른 도구와 Pandas 를 비교해 '몇 배 빠른지'를 계산한다.
    # Pandas 를 기준으로 삼는 이유는 세 도구 중 가장 널리 쓰이는 비교 기준점이기 때문이다.
    pandas_time = next(item.total_sec for item in benchmarks if item.tool == "Pandas")
    fastest, slowest = benchmarks[0], benchmarks[-1]

    null_rows = "\n".join(
        f"| `{name}` | {count:,} |" for name, count in eda["null_counts"].items()
    )
    speed_rows = "\n".join(
        f"| {rank} | {item.tool} | {item.total_sec:.4f} | {item.mean_sec:.4f} | "
        f"{pandas_time / item.total_sec:.2f}배 |"
        for rank, item in enumerate(benchmarks, start=1)
    )
    all_match = all(matches.values())
    match_rows = "\n".join(
        f"| {name} | {'일치' if ok else '불일치'} |" for name, ok in matches.items()
    )

    # 아래 두 값은 f-string 밖에서 미리 만든다.
    # 파이썬 3.11까지는 f-string 의 {} 안에 역슬래시(\n 등)를 쓸 수 없기 때문이다.
    if all_match:
        match_detail = "\n".join(
            (
                "- IQR 필터 확인 결과: 세 도구 모두 같은 하한·상한 값을 인자로 받아 "
                "동일한 행을 걸렀습니다.",
                "- 그룹·집계 조건 확인 결과: 결측 region·category를 세 도구 모두 같은 "
                "이름으로 치환해 그룹 구성이 같습니다.",
                "- 정렬·자료형·소수점 처리 확인 결과: 정렬 기준을 동점까지 통일했고, "
                "건수 자료형 차이(int64/uint32)와 합산 순서로 인한 부동소수 오차는 "
                f"상대 오차 {FLOAT_TOLERANCE:g} 이내로 같은 값으로 판정했습니다.",
            )
        )
    else:
        match_detail = "\n".join(
            f"- {name}: {reason}" for name, reason in context["mismatch_reasons"].items()
        )

    # 하한이 음수로 나오는 경우가 있다. 매출은 음수가 될 수 없으므로 하한은 실질적으로
    # 아무것도 걸러내지 못하고, 위쪽 고액 거래만 잘린다는 뜻이다.
    # 읽는 사람이 "왜 하한이 마이너스인가"를 오해하지 않도록 해석을 덧붙인다.
    lower_note = (
        f" 하한 {bounds.lower:,.2f}는 음수라 실제로 걸러지는 값이 없고, "
        "상한을 넘는 고액 거래만 제거됩니다. 분포가 오른쪽으로 길게 늘어진 형태이기 "
        "때문입니다."
        if bounds.lower < 0
        else ""
    )

    match_conclusion = (
        "Pandas·Polars·DuckDB의 집계 결과가 모두 동일합니다."
        if all_match
        else "결과 차이가 발생했습니다. 원인은 다음과 같습니다."
    )

    return f"""# Practice 3 실행 결과 보고서

> Pandas EDA · Polars Lazy · DuckDB SQL 비교

---

## 0. 실행 정보

| 항목 | 내용 |
|---|---|
| 입력 파일 | `{DATA_FILE}` |
| 비교 도구 | Pandas / Polars Lazy API / DuckDB SQL |
| 집계 기준 | `region`, `category` |
| 집계 대상 | `{TARGET_COLUMN}` |
| 정렬 기준 | `total` 내림차순 |
| `timeit` 반복 횟수 | `{TIMEIT_NUMBER}`회 (세 도구 동일) |

---

## 1. 데이터 기본 정보

### 1.1 데이터 크기

| 구분 | 결과 |
|---|---:|
| 전체 행 수 | {eda["rows"]:,}행 |
| 전체 열 수 | {eda["columns"]}개 |

### 1.2 컬럼별 결측치

| 컬럼 | 결측치 수 |
|---|---:|
{null_rows}

### 1.3 EDA 확인 결과

- `df.info()` 확인 결과: 전체 {eda["columns"]}개 컬럼 중 `region`, `category`, `{TARGET_COLUMN}`에 결측이 있으며, `{TARGET_COLUMN}`은 float64로 읽혀 수치 집계가 가능합니다.
- `df.describe()` 확인 결과: `{TARGET_COLUMN}`의 평균과 최댓값 차이가 커서 소수의 고액 거래가 평균을 끌어올리고 있습니다. IQR 기준 이상치 제거가 필요한 분포입니다.
- 주요 확인 사항: 결측 `region` {eda["null_counts"].get("region", 0):,}건과 결측 `category` {eda["null_counts"].get("category", 0):,}건은 버리지 않고 `{UNKNOWN_REGION}`·`{UNKNOWN_CATEGORY}`로 묶어 집계했습니다. 버릴 경우 해당 매출이 보고서에서 통째로 사라지기 때문입니다. 결측 `{TARGET_COLUMN}` {eda["null_counts"].get(TARGET_COLUMN, 0):,}건은 금액을 알 수 없어 집계에서 제외했습니다.

<details>
<summary>df.info() 원문</summary>

```text
{eda["info_text"]}
```

</details>

<details>
<summary>df.describe() 원문</summary>

```text
{eda["describe_text"]}
```

</details>

---

## 2. IQR 이상치 처리 결과

### 2.1 적용 공식

```text
IQR = Q3 - Q1
하한 = Q1 - {IQR_FACTOR} × IQR
상한 = Q3 + {IQR_FACTOR} × IQR
정상 범위 = 하한 이상, 상한 이하
```

### 2.2 계산 결과

| 항목 | 결과 |
|---|---:|
| Q1 | {bounds.q1:,.2f} |
| Q3 | {bounds.q3:,.2f} |
| IQR | {bounds.iqr:,.2f} |
| 정상 범위 하한 | {bounds.lower:,.2f} |
| 정상 범위 상한 | {bounds.upper:,.2f} |
| 제거 전 행 수 | {context["rows_before"]:,}행 |
| 제거 후 행 수 | {context["rows_after"]:,}행 |
| 제외된 행 (합계) | {context["rows_removed"]:,}건 |
| └ `{TARGET_COLUMN}` 결측으로 제외 | {context["missing_removed"]:,}건 |
| └ IQR 범위 밖으로 제외 | {context["outlier_removed"]:,}건 |

### 2.3 이상치 처리 해석

`{TARGET_COLUMN}`가 {bounds.lower:,.2f} 이상 {bounds.upper:,.2f} 이하인 데이터를 정상 범위로 판단했습니다. 전체 {context["rows_before"]:,}건 중 **{context["rows_removed"]:,}건을 집계에서 제외**했으며, 최종 {context["rows_after"]:,}건을 사용했습니다.

제외 사유는 성격이 다른 두 가지이므로 나눠서 봐야 합니다.

- **`{TARGET_COLUMN}` 결측 {context["missing_removed"]:,}건** — 금액을 아예 알 수 없어 집계할 수 없는 행입니다. 이상치가 아닙니다.
- **IQR 범위 밖 {context["outlier_removed"]:,}건** — 금액이 상한을 넘는 고액 거래입니다. 이쪽이 이상치입니다.

둘을 합쳐 "{context["rows_removed"]:,}건의 이상치를 제거했다"고 적으면 결측 {context["missing_removed"]:,}건까지 이상치로 잘못 전달됩니다.{lower_note}

---

## 3. 세 도구의 공통 집계 조건

세 도구에 동일하게 다음 조건을 적용했습니다.

```text
입력 파일: {DATA_FILE}
이상치 조건: {TARGET_COLUMN}가 IQR 정상 범위 안에 있음 ({bounds.lower:,.2f} ~ {bounds.upper:,.2f})
결측 처리: region → {UNKNOWN_REGION}, category → {UNKNOWN_CATEGORY}
그룹 기준: region, category
집계 항목:
  total = {TARGET_COLUMN} 합계
  mean  = {TARGET_COLUMN} 평균
  count = {TARGET_COLUMN} 건수
정렬 기준: total 내림차순 (동점 시 region, category 오름차순)
```

IQR 경계는 Pandas로 한 번만 계산해 세 도구에 같은 숫자로 넘겼습니다. 도구마다 분위수 보간 방식이 달라(Polars 기본값 `nearest`, Pandas·DuckDB `linear`) 각자 계산하면 경계가 어긋나고, 걸러지는 행이 달라져 비교가 성립하지 않기 때문입니다.

### 3.1 집계 결과 TOP {TOP_N}

| 순위 | region | category | total | mean | count |
|---:|---|---|---:|---:|---:|
{format_table(result)}

전체 그룹 수: {len(result)}개

---

## 4. 집계 결과 동일성 검증

세 도구의 결과 컬럼을 다음 순서로 통일한 뒤 비교했습니다.

```text
{", ".join(RESULT_COLUMNS)}
```

| 비교 대상 | 검증 결과 |
|---|---|
{match_rows}

### 검증 결론

{match_conclusion}

{match_detail}

---

## 5. 실행 시간 비교

> 세 도구 모두 `timeit number={TIMEIT_NUMBER}`으로 동일하게 측정했으며, 측정 구간에 CSV 파일 읽기부터 정렬까지 전 과정을 포함했습니다.
> 측정 전 세 도구를 똑같이 {WARMUP_NUMBER}회씩 예열하고 그 결과는 버렸습니다. 첫 실행에는 운영체제 파일 캐시가 비어 있어 생기는 비용과 엔진 초기화 비용이 함께 붙는데, 이는 집계 성능이 아니기 때문입니다. 실측 결과 Polars의 첫 실행은 이후 실행보다 약 68% 느렸습니다.

| 순위 | 도구 | 총 실행 시간(초) | 1회 평균(초) | Pandas 대비 속도 |
|---:|---|---:|---:|---:|
{speed_rows}

### 성능 비교 결과

- 가장 빠른 도구: {fastest.tool}
- 가장 느린 도구: {slowest.tool}
- 가장 빠른 도구는 Pandas보다 약 {pandas_time / fastest.total_sec:.2f}배 빨랐습니다.
- 측정 결과에 대한 해석: Pandas는 CSV 전체를 메모리에 올린 뒤 집계하므로 파일 읽기 비용이 그대로 드러납니다. Polars는 `scan_csv`로 실행 계획을 먼저 세우고 `collect()` 시점에 필요한 컬럼만 읽으면서 필터를 함께 적용해 읽는 양 자체가 줄어듭니다. DuckDB는 CSV를 병렬로 스캔하며 집계까지 엔진 안에서 처리합니다. 두 도구 모두 여러 코어를 함께 쓰는 반면 Pandas의 집계는 단일 코어로 동작하는 점도 차이에 기여합니다. 데이터가 {eda["rows"]:,}행 규모로 커질수록 이 격차는 더 벌어집니다.

---

## 6. 최종 결론

1. Pandas로 기본 EDA를 수행하고 IQR 방식으로 `{TARGET_COLUMN}` 이상치를 제거했습니다. ({context["rows_before"]:,}행 → {context["rows_after"]:,}행)
2. `region·category`별 `total·mean·count`를 named aggregation으로 계산했습니다.
3. 같은 집계를 Polars Lazy API(`scan_csv → filter → group_by → agg → sort → collect`)와 DuckDB SQL(`GROUP BY`)로 구현했습니다.
4. 세 도구의 집계 결과는 {"동일했습니다" if all_match else "차이가 있었습니다"}.
5. 동일한 반복 횟수({TIMEIT_NUMBER}회)로 측정한 결과, 가장 빠른 도구는 {fastest.tool}입니다.

### 본인 의견

문법 면에서는 Pandas가 가장 익숙하지만, 필터·그룹·정렬이 이어지는 이번 집계에서는 Polars의 체인 방식이 처리 순서를 그대로 읽히게 해서 가장 명확했습니다. DuckDB는 SQL을 아는 사람이면 설명 없이 바로 이해할 수 있다는 점이 강점이었고, 집계 조건을 문장 하나로 표현할 수 있어 코드 양이 가장 적었습니다. 성능은 가장 빠른 {fastest.tool} 기준으로 Pandas 대비 약 {pandas_time / fastest.total_sec:.2f}배 차이가 났는데, 이번처럼 파일에서 읽어 곧바로 집계하는 작업에서는 Lazy 실행과 병렬 스캔의 이점이 분명하다고 느꼈습니다. 다만 이번 과제에서 가장 시간을 쓴 부분은 성능이 아니라 세 도구의 결과를 일치시키는 일이었습니다. 결측 그룹 처리와 분위수 보간 방식이 도구마다 다르다는 점은 실행해 보기 전에는 알기 어려웠고, 도구를 바꿀 때 문법만 옮기면 된다고 생각하면 안 된다는 것을 확인했습니다.

### 개선 사항

- 반복 횟수는 실측을 근거로 {TIMEIT_NUMBER}회로 정했습니다. 20회 표본으로 확인한 결과 'Pandas 대비 배수'의 흔들림이 N=1에서 ±20%, N=3에서 ±9%, N=10에서 ±3.5%로 줄었고, N=20은 시간만 두 배 들 뿐 개선폭이 크지 않았습니다. 더 정밀한 비교가 필요하다면 `timeit.repeat()`으로 여러 표본을 얻어 최솟값이나 중앙값을 쓰는 방식이 낫습니다. 현재 방식은 평균을 쓰므로 순간적인 시스템 부하가 그대로 섞입니다.
- 예열 1회로 파일 캐시 조건은 맞췄지만, 반대로 '처음 한 번 쓸 때의 성능'은 측정되지 않습니다. 배치 작업처럼 하루 한 번 도는 용도라면 오히려 콜드 상태의 시간이 현실에 가까우므로, 두 값을 나란히 재두면 용도에 맞는 판단이 가능합니다.
- CSV 대신 Parquet 형식으로 저장해 같은 비교를 해보면, 세 도구의 차이 중 어디까지가 파일 읽기 비용이고 어디부터가 집계 엔진의 차이인지 분리해서 볼 수 있습니다.
- 데이터 크기를 10배로 늘려 측정하면 Pandas가 메모리 한계에 먼저 부딪히는 지점을 확인할 수 있어, 도구 선택 기준을 더 구체적으로 정할 수 있습니다.

---

## 7. 최종 제출 점검

- [x] `df.info()`와 `isnull().sum()` 결과를 확인했습니다.
- [x] IQR 공식과 정상 범위를 정확하게 적용했습니다.
- [x] 이상치 제거 전·후 행 수를 출력했습니다.
- [x] Pandas named aggregation을 사용했습니다.
- [x] 총매출 내림차순으로 정렬했습니다.
- [x] Polars에서 `scan_csv()`를 사용했습니다.
- [x] Polars 체인 마지막에 `collect()`를 호출했습니다.
- [x] DuckDB에서 동일한 집계를 SQL `GROUP BY`로 작성했습니다.
- [x] 세 도구의 결과를 DataFrame 기준으로 비교했습니다.
- [x] 세 도구의 `timeit number`를 동일하게 설정했습니다.
- [x] 실행 결과와 본인 의견을 작성했습니다.
"""


def write_report(path, content):
    """
    [기능] 보고서 문자열을 파일로 저장한다.
    [설명] 보고서를 남기지 못하더라도 집계 결과 자체는 화면과 로그에 이미 남아 있다.
           따라서 저장 실패로 프로그램을 중단시키지 않고 경고만 남기고 넘어간다.

    Args:
        path (Path): 저장할 파일 경로.
        content (str): 저장할 마크다운 문서 전문.

    Returns:
        bool: 저장에 성공했으면 True, 실패했으면 False.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except OSError as error:
        logger.warning(f"[안내] 보고서를 저장하지 못했습니다: {error}")
        return False
    return True


# ================================================================
# 9. 실행 - 읽기 → EDA → 이상치 제거 → 세 도구 집계 → 비교 → 측정 → 보고서
# ================================================================


def run_pipeline(base_dir):
    """
    [기능] 이 프로그램의 분석 절차를 처음부터 끝까지 수행한다.
    [설명] 실제 분석은 모두 여기에 모으고, main() 은 오류를 안내하는 역할만 맡는다.
           두 가지를 한 함수에 섞으면 예외 처리 블록 안에 분석 코드가 들어가
           어디까지가 정상 흐름인지 읽기 어려워지기 때문이다.

    Args:
        base_dir (Path): 입력 파일과 산출물이 놓이는 기준 폴더.

    Returns:
        dict: 보고서 작성에 필요한 실행 결과 모음.

    Raises:
        FileNotFoundError: 입력 파일을 찾지 못한 경우.
        ValueError: 데이터가 비었거나 IQR 필터 통과 행이 0건인 경우.
        AssertionError: 자체 검증에 실패한 경우.
    """
    data_path = find_data_file(base_dir)

    # 파일이 지나치게 크면 읽는 순간 메모리를 대부분 차지한다. 미리 알려두면
    # 담당자가 중단하거나 더 큰 환경에서 다시 돌릴지 판단할 수 있다.
    file_size = data_path.stat().st_size
    if file_size > LARGE_FILE_WARN_BYTES:
        logger.warning(
            f"[경고] 입력 파일이 큽니다({file_size / 1024 / 1024:,.0f}MB). "
            f"읽는 동안 그보다 몇 배 큰 메모리가 필요할 수 있습니다."
        )

    # ---- 1단계: 읽기 + 기초 탐색 -----------------------------------------
    frame = load_sales(data_path)
    if frame.empty:
        raise ValueError(f"거래 데이터가 비어 있습니다: {data_path}")

    logger.info(f"[1/5] 데이터 읽기 완료 — {len(frame):,}건 ({data_path.name})")
    eda = collect_eda(frame)

    # ---- 2단계: IQR 이상치 제거 -------------------------------------------
    bounds = compute_iqr_bounds(frame[TARGET_COLUMN])
    rows_before = len(frame)
    # 세 도구가 쓸 필터 조건과 완전히 같은 식이어야 검증이 의미를 가진다
    유효 = frame[TARGET_COLUMN].notna()
    범위안 = frame[TARGET_COLUMN].between(bounds.lower, bounds.upper)
    kept = frame[유효 & 범위안]
    rows_after = len(kept)

    # 제거 사유를 나눠서 센다. 합쳐서 한 숫자로만 내면 전부 이상치였다고 오해한다.
    # 금액을 아예 모르는 행과 금액이 지나치게 큰 행은 성격이 다르다.
    missing_removed = int((~유효).sum())
    outlier_removed = int((유효 & ~범위안).sum())

    logger.info(
        f"[2/5] 결측·IQR 이상치 제외 완료 — {rows_before:,}행 → {rows_after:,}행 "
        f"(결측 {missing_removed:,} + 범위 밖 {outlier_removed:,})"
    )

    # 필터가 전부 걸러냈다면 이후 집계는 빈 표만 낸다. 그 전에 이상 상황으로 알린다.
    if rows_after == 0:
        raise ValueError(
            f"IQR 정상 범위 [{bounds.lower:,.2f}, {bounds.upper:,.2f}]를 "
            f"통과한 행이 없습니다. 데이터 분포를 확인해 주세요."
        )

    # 원본은 EDA 이후 쓰지 않는다. 세 도구가 각자 파일에서 다시 읽기 때문이다.
    del frame, kept

    # ---- 3단계: 세 도구로 동일 집계 ---------------------------------------
    # DuckDB 연결은 측정 구간 밖에서 한 번만 만든다.
    # 매번 새로 열면 연결 생성 시간이 집계 시간에 섞여 비교가 왜곡된다.
    connection = duckdb.connect()
    try:
        pandas_result = aggregate_pandas(data_path, bounds)
        polars_result = aggregate_polars(data_path, bounds)
        duckdb_result = aggregate_duckdb(connection, data_path, bounds)

        result = normalize_result(pandas_result)
        logger.info(f"[3/5] 세 도구 집계 완료 — {len(result)}개 그룹")

        # ---- 4단계: 결과 동일성 검증 --------------------------------------
        matches, mismatch_reasons = {}, {}
        for name, other in (
            ("Pandas = Polars", polars_result),
            ("Pandas = DuckDB", duckdb_result),
        ):
            ok, reason = compare_results(pandas_result, other)
            matches[name] = ok
            if not ok:
                mismatch_reasons[name] = reason

        logger.info(
            f"[4/5] 결과 동일성 검증 완료 — "
            f"{'모두 일치' if all(matches.values()) else '불일치 발견'}"
        )

        # ---- 5단계: 성능 비교 ----------------------------------------------
        # 세 함수 모두 인자 없이 부를 수 있게 만들어, timeit 에 넘기는 형태를 통일한다.
        # 측정에만 몇 초가 걸리므로, 시작 전에 무엇을 얼마나 하는지 미리 알린다.
        logger.info(
            f"[5/5] 실행 시간 측정 중 — 세 도구 × {TIMEIT_NUMBER}회 "
            f"(예열 {WARMUP_NUMBER}회 별도)"
        )
        benchmarks = benchmark(
            [
                ("Pandas", lambda: aggregate_pandas(data_path, bounds)),
                ("Polars", lambda: aggregate_polars(data_path, bounds)),
                ("DuckDB", lambda: aggregate_duckdb(connection, data_path, bounds)),
            ]
        )
    # 연결을 닫지 않으면 파일 핸들이 남는다. 오류가 나도 반드시 정리한다.
    finally:
        connection.close()

    # ---- 6단계: 자체 검증 -------------------------------------------------
    # 결과를 보여주기 전에 점검한다. 틀린 숫자를 결론으로 먼저 내보이면 안 되기 때문이다.
    verify_results(result, bounds, rows_after)

    return {
        "eda": eda,
        "bounds": bounds,
        "rows_before": rows_before,
        "rows_after": rows_after,
        "rows_removed": rows_before - rows_after,
        "missing_removed": missing_removed,
        "outlier_removed": outlier_removed,
        "result": result,
        "matches": matches,
        "mismatch_reasons": mismatch_reasons,
        "benchmarks": benchmarks,
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
    # 이 경우 파일도 멀쩡하고 형식도 맞아서, 원인을 짚어주지 않으면 찾기 어렵다.
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
    # 권한이 없어 열지 못하는 경우가 여기로 온다
    except OSError as error:
        logger.error(f"[오류] 입력 파일을 읽을 수 없습니다: {error}")
        return 1
    # 검증 실패는 결과를 그대로 믿으면 안 된다는 뜻이므로 보고서를 만들지 않는다
    except AssertionError as error:
        logger.error(f"[검증 실패] {error}")
        return 1

    # ---- 결과 출력 --------------------------------------------------------
    # 결론을 먼저, 근거를 뒤에 둔다. 계산이 모두 끝난 뒤에 출력하므로 순서를 정할 수 있다.
    print_summary(context)
    print_details(context)

    # ---- 보고서 저장 ------------------------------------------------------
    report_path = base_dir / REPORT_FILE
    if write_report(report_path, build_report(context)):
        logger.info(f"\n[안내] 결과 보고서를 저장했습니다: {report_path}")

    # 결과가 다르면 어느 도구를 믿어야 할지 알 수 없다. 보고서는 남기되 실패로 알린다.
    if not all(context["matches"].values()):
        logger.error("\n[오류] 세 도구의 집계 결과가 일치하지 않습니다. 보고서 4장을 확인해 주세요.")
        return 1

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
