# 파이썬 실습 과제 작성 규칙 (ref)

> 실습 3(`광주_1반_박기택.py`)에서 정착시킨 형식을 다음 과제에 그대로 쓰기 위한 참고 문서.
> 코드 블록은 **그대로 복사해 쓰는 것을 전제**로 적었다.

## 목차

1. [파일 머리말](#1-파일-머리말)
2. [상수 블록](#2-상수-블록)
3. [함수 docstring](#3-함수-docstring)
4. [로깅](#4-로깅)
5. [출력 — 결론 먼저, 근거는 뒤에](#5-출력--결론-먼저-근거는-뒤에)
6. [숫자·표 서식](#6-숫자표-서식)
7. [예외 처리](#7-예외-처리)
8. [자체 검증](#8-자체-검증)
9. [테스트 구성](#9-테스트-구성)
10. [체크리스트](#10-체크리스트)

---

## 1. 파일 머리말

평가 항목 "프로그램 전체 설명 및 변경 내역(머리말)"에 직접 대응한다.
**목적·입력·출력·처리 방식·오류 대응·실행 방법·작성자·변경 이력** 순서를 지킨다.

````python
"""
================================================================
[프로그램명] 무엇을 하는 프로그램인지 한 줄로
================================================================

■ 목적
    왜 만들었는지. 이 프로그램이 없으면 누가 무엇을 못 하는지.

■ 입력
    - 파일명 (형식, 필요한 컬럼/키)
      ※ 위치 조건과 없을 때의 동작을 함께 적는다.

■ 출력 (결론을 먼저, 근거를 뒤에 보여준다)
    1) 진행 상황  [1/N]~[N/N] 한 줄씩
    2) 핵심 결과  이 프로그램으로 알고자 한 답
    3) 이하 상세  그 답의 근거가 되는 수치
    - 저장되는 파일들

■ 처리 방식 요약
    - 눈에 띄지 않지만 중요한 판단을 여기 적는다.
      "왜 이렇게 했는지"를 남기지 않으면 나중에 되돌려진다.

■ 오류 상황별 대응 (별도 표기가 없으면 안내 후 종료 코드 1 반환)
    - 입력 파일 없음/권한 없음     → 파일 경로와 원인을 안내
    - 파일 인코딩이 UTF-8 아님     → UTF-8로 다시 저장하도록 안내
    - (상황)                      → (대응)
    - 실행 중 Ctrl+C              → 중단 안내 후 종료 코드 130
    - 메모리 부족                  → 나눠서 실행하도록 안내

■ 실행 방법
    python 광주_1반_박기택.py
    python 광주_1반_박기택.py > 실행결과.txt

■ 작성자 : 박기택
■ 최초 작성일 : YYYY-MM-DD

----------------------------------------------------------------
■ 변경 내역 (Change Log)
----------------------------------------------------------------
| 버전   | 날짜        | 작성자   | 변경 내용                          |
|--------|-------------|----------|------------------------------------|
| v1.0   | YYYY-MM-DD  | 박기택   | 최초 작성                          |
| v1.1   | YYYY-MM-DD  | 박기택   | (무엇을 왜 바꿨는지)               |
================================================================
"""
````

**변경 이력 쓰는 법**: "기능 추가"가 아니라 **무엇이 문제였고 어떻게 해결했는지**를 적는다.

```
나쁨: | v1.5 | ... | 성능 측정 개선 |
좋음: | v1.5 | ... | 20회 표본 실측을 근거로 반복 횟수를 3→10회로 올리고 |
      |      | ... | 예열 1회 추가. 도구 간 배수 흔들림 ±9%→±3.5%      |
```

---

## 2. 상수 블록

**담당자가 바꿀 값은 전부 파일 상단 한 곳에** 모은다. 코드 중간에 흩어진 숫자를 없애는 게 목적이다.

```python
# ================================================================
# 설정값 - 담당자가 바꿀 일이 있는 값은 모두 여기 모아둔다
# ================================================================

# 분석 대상 원본 파일. 데이터가 바뀌면 이 파일만 교체하면 된다.
DATA_FILE = "sales_100k.csv"

# ★ 여러 곳에서 같아야 하는 값은 상수 하나만 두고 전부 참조하게 한다.
#   각자 적으면 언젠가 반드시 어긋난다. 구조로 막는 편이 검토보다 확실하다.
TIMEIT_NUMBER = 10
```

> **핵심**: "세 곳의 값이 같아야 한다"는 규칙은 주석으로 부탁하지 말고 **상수 하나로 만들어** 어긋날 수 없게 한다.

숫자를 정할 때는 **근거를 주석에 남긴다**.

```python
# 10으로 정한 근거 (20회 표본으로 실측):
# 'Pandas 대비 배수'의 흔들림이 N=1일 때 ±20%, N=3일 때 ±9%, N=10일 때 ±3.5%.
# N=20은 시간만 두 배 들고 개선폭이 미미해 10을 기준으로 잡았다.
TIMEIT_NUMBER = 10
```

---

## 3. 함수 docstring

평가 항목 "함수·기능 설명(중간)"에 대응한다. **`[기능]` 한 줄 + `[설명]` 여러 줄** 형식.

```python
def compute_iqr_bounds(series):
    """
    [기능] IQR 방식으로 '정상 범위'의 하한과 상한을 계산한다.
    [설명] 매출에는 자릿수가 다른 극단값이 섞이기 마련이고, 그 몇 건이 평균을 왜곡한다.
           IQR은 가운데 50% 구간의 폭을 기준 삼아 "이 정도를 벗어나면 이상치로 본다"를
           정하는 방법이다.

           (판단이 필요했던 부분은 여기에 이유까지 적는다.
            "무엇을 하는지"는 코드를 읽으면 알지만 "왜 그렇게 했는지"는 알 수 없다.)

    Args:
        series (pandas.Series): 기준으로 삼을 수치 컬럼.

    Returns:
        IQRBounds: q1, q3, iqr, lower, upper 를 담은 계산 결과.

    Raises:
        ValueError: 값이 모두 비어 있어 분위수를 계산할 수 없는 경우.
    """
```

**규칙**

| 항목 | 내용 |
|---|---|
| `[기능]` | 한 줄. 무엇을 하는가 |
| `[설명]` | 왜 필요한가, 왜 이렇게 했는가. **판단의 근거가 여기 들어간다** |
| `Args` / `Returns` / `Raises` | 타입과 의미. 없으면 생략 |
| 한 줄 함수 | `"""[기능] ~한다."""` 한 줄로 끝내도 된다 |

**인라인 주석**은 "코드가 말하지 않는 것"만 적는다.

```python
# 나쁨 — 코드를 그대로 읽은 것
frame = pd.read_csv(path)  # CSV를 읽는다

# 좋음 — 왜 이 옵션인지
# 이 파일은 맨 앞에 BOM이 붙어 있다. 그냥 utf-8로 읽으면 첫 컬럼 이름이
# 'order_id'가 아니라 '﻿order_id'로 잡혀 컬럼 조회가 전부 어긋난다.
frame = pd.read_csv(path, encoding="utf-8-sig")
```

---

## 4. 로깅

**화면(stdout) + 파일 동시 기록.** 로그 파일을 못 만들어도 본 작업은 계속한다.

```python
import logging
import sys

logger = logging.getLogger("프로그램이름")


class LogFileFormatter(logging.Formatter):
    """
    [기능] 로그 파일에서 '한 줄 = 기록 한 건'이 유지되도록 메시지의 줄바꿈을 정리한다.
    [설명] 화면에서는 항목 사이를 띄우려고 메시지에 빈 줄을 넣는다. 그 줄바꿈이 파일에도
           들어가면 시각·심각도가 없는 줄이 생겨, 나중에 로그를 검색할 때 걸린다.
           화면 출력은 손대지 않고 파일에 적을 때만 정리한다.
    """

    def format(self, record):
        original = record.msg
        if isinstance(original, str):
            record.msg = original.strip().replace("\n", " ")
        try:
            return super().format(record)
        # 같은 기록을 화면 담당자도 쓰므로 반드시 원래대로 되돌린다
        finally:
            record.msg = original


def setup_logging(base_dir):
    """
    [기능] 실행 기록을 화면과 파일 양쪽에 남기도록 준비한다.
    [설명] 화면에는 결과만 깔끔하게, 파일에는 시각과 심각도까지 남긴다.
           로그 파일을 만들지 못해도 집계 자체는 문제가 없으므로 화면 기록만으로 낮춰 진행한다.
    """
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()   # 여러 번 불러도 기록이 중복되지 않게
    logger.propagate = False

    # stderr(기본값)가 아니라 stdout으로 보낸다.
    # 그래야 `python x.py > 실행결과.txt` 로 결과를 파일에 남길 수 있다.
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console)

    log_path = base_dir / LOG_FILE
    try:
        file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    except OSError as error:
        logger.warning(f"[안내] 로그 파일을 만들 수 없어 화면에만 기록합니다: {error}")
        return None

    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(LogFileFormatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(file_handler)
    return log_path
```

**메시지 말머리**

| 말머리 | 쓰임 |
|---|---|
| `[1/5]` `[2/5]` | 진행 상황. 오래 걸리는 구간에서 멈춘 것으로 오해하지 않게 |
| `[안내]` | 정상 흐름의 알림 |
| `[경고]` | 진행은 하지만 알아야 할 것 (`logger.warning`) |
| `[오류]` | 중단 사유 (`logger.error`) — 원인과 **해결 방법**을 함께 |
| `[검증 실패]` | 자체 검증 실패 |
| `[중단]` | Ctrl+C |
| `[완료]` | 정상 종료 |

> **주의**: `print()` 대신 `logger.info()`를 쓴다. 그래야 같은 내용이 로그 파일에도 남는다.

---

## 5. 출력 — 결론 먼저, 근거는 뒤에

**가장 중요한 규칙.** 계산하면서 바로 찍으면 순서를 바꿀 수 없다.
**계산 함수는 값만 모아 돌려주고, 출력은 마지막에 몰아서** 한다.

```
[1/5] 데이터 읽기 완료 — 1,000,000건        ← 진행 상황 (한 줄씩, 실시간)
[2/5] IQR 이상치 제거 완료 — ...
...
════════════════════════════════════════
 핵심 결과                                ← 결론
════════════════════════════════════════
 [1] ...
 [2] ...

[표]

──────── 이하 상세 ────────                ← 근거
[상세 1] ...
[상세 2] ...
```

```python
def collect_eda(frame):
    """
    [기능] 기본 탐색 결과를 모아서 돌려준다. (화면 출력은 하지 않는다)
    [설명] 여기서 바로 찍지 않는 이유는 출력 순서 때문이다.
           info()·describe()는 수십 줄이라, 먼저 찍으면 정작 중요한 결론이
           화면 아래로 밀려 스크롤해야 보인다.
           계산과 출력을 나눠두면 print_summary()가 결론을 먼저 보여줄 수 있다.
    """
    return {...}   # 값만 돌려준다


def print_summary(context):
    """[기능] 이 프로그램으로 알고자 한 결론만 추려 화면 맨 앞에 보여준다."""
    logger.info("\n" + "=" * 72)
    logger.info(" 핵심 결과")
    logger.info("=" * 72)
    logger.info(f" [1] 세 도구 집계 결과   {match_text}")
    logger.info(f" [2] 가장 빠른 도구      {fastest.tool}")
    logger.info("=" * 72)


def print_details(context):
    """[기능] 핵심 결과의 근거가 되는 상세 수치를 순서대로 보여준다."""
    logger.info("\n" + "-" * 72)
    logger.info(" 이하 상세")
    logger.info("-" * 72)
    logger.info("\n[상세 1] ...")


def main():
    context = run_pipeline(base_dir)   # 계산만
    print_summary(context)             # 결론 먼저
    print_details(context)             # 근거는 뒤에
```

**진행 상황은 남긴다.** 10초 이상 걸리는 작업에서 아무것도 안 나오면 멈춘 것으로 오해한다.
단, 진행 줄에는 **수치를 담지 않는다**(결과와 헷갈리므로 한 줄 요약만).

---

## 6. 숫자·표 서식

### 금액은 억·만 단위로

`74,992,750,244원`은 자릿수를 세어야 규모가 잡힌다. `749.9억원`은 바로 읽힌다.

```python
def format_won(value):
    """[기능] 큰 금액을 억·조 단위로 바꿔 읽기 쉽게 만든다."""
    조, 억, 만 = 1_0000_0000_0000, 1_0000_0000, 1_0000
    if abs(value) >= 조:
        return f"{value / 조:,.2f}조원"
    if abs(value) >= 억:
        return f"{value / 억:,.1f}억원"
    if abs(value) >= 만:
        return f"{value / 만:,.1f}만원"
    return f"{value:,.0f}원"
```

### 한글이 섞인 표는 폭을 직접 계산

`DataFrame.to_string()`은 지수 표기(`7.499275e+10`)가 나오고, `f"{text:<10}"`은
한글이 두 칸을 차지하는 걸 몰라 세로줄이 어긋난다.

```python
import unicodedata


def display_width(text):
    """[기능] 문자열이 터미널에서 차지하는 칸 수를 센다."""
    # 'W'(넓음)와 'F'(전각)로 분류된 문자가 두 칸을 차지한다
    return sum(2 if unicodedata.east_asian_width(char) in "WF" else 1 for char in text)


def pad(text, width, align="left"):
    """[기능] 터미널 표시 폭을 기준으로 문자열의 자리를 맞춘다."""
    gap = " " * max(0, width - display_width(text))
    return text + gap if align == "left" else gap + text
```

사용 예:

```python
머리 = pad("순위", 5) + pad("region", 8) + pad("총매출", 13, "right")
줄 = [머리, "-" * display_width(머리)]
for rank, row in enumerate(result.itertuples(index=False), start=1):
    줄.append(pad(str(rank), 5) + pad(row.region, 8) + pad(format_won(row.total), 13, "right"))
```

결과:

```
순위 region  category         총매출        평균      건수
----------------------------------------------------------
1    서울    의류          749.9억원   249.5만원    30,054
2    서울    식품          748.9억원   248.8만원    30,103
```

---

## 7. 예외 처리

평가 배점이 가장 큰 항목(35점). **분석 로직과 오류 안내를 분리**한다.

```python
def run_pipeline(base_dir):
    """[기능] 이 프로그램의 절차를 처음부터 끝까지 수행한다."""
    # 실제 작업만. 예외는 그대로 위로 올린다.


def main():
    """
    [기능] 프로그램 전체 흐름을 실행하고, 문제가 생기면 원인을 안내한다.
    [설명] 절차는 run_pipeline()이 맡고, 이 함수는 실패했을 때 "무엇이 잘못됐고
           어떻게 고치면 되는지"를 한글로 알려주는 역할만 한다.
    """
    base_dir = Path(__file__).resolve().parent   # 어느 폴더에서 실행하든 같은 파일을 찾는다
    setup_logging(base_dir)

    try:
        context = run_pipeline(base_dir)

    # ★ 상속 관계에 주의. 아래 둘은 ValueError의 하위 예외라,
    #   순서를 바꾸면 ValueError 블록에 먼저 잡혀 엉뚱한 원인을 안내하게 된다.
    except UnicodeDecodeError:
        logger.error(f"[오류] 파일 인코딩이 UTF-8이 아닙니다: {경로}")
        logger.error("       원본 파일을 UTF-8로 다시 저장한 뒤 실행해 주세요.")
        return 1
    except pd.errors.ParserError as error:
        logger.error(f"[오류] CSV 형식이 잘못됐습니다: {error}")
        return 1
    except ValueError as error:
        logger.error(f"[오류] 데이터가 예상과 다릅니다: {error}")
        return 1
    except OSError as error:   # 파일 없음과 권한 없음이 모두 여기로 온다
        logger.error(f"[오류] 입력 파일을 읽을 수 없습니다: {error}")
        return 1
    except AssertionError as error:
        logger.error(f"[검증 실패] {error}")
        return 1

    print_summary(context)
    print_details(context)
    logger.info("\n[완료] 모든 단계를 정상 수행했습니다.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    # Ctrl+C에 붉은 오류 화면 대신 한 줄 안내 (130 = 사용자가 중단함)
    except KeyboardInterrupt:
        logger.error("\n[중단] 사용자가 실행을 중단했습니다.")
        sys.exit(130)
    except MemoryError:
        logger.error("\n[오류] 메모리가 부족해 처리를 끝내지 못했습니다.")
        logger.error("       입력 파일을 나눠서 실행하거나 더 큰 환경에서 실행해 주세요.")
        sys.exit(1)
```

### 원칙

| 원칙 | 내용 |
|---|---|
| **원인별로 나눈다** | `except Exception` 하나로 뭉치면 무엇이 문제인지 알 수 없다 |
| **해결 방법까지 안내** | "인코딩 오류" (X) → "UTF-8로 다시 저장한 뒤 실행해 주세요" (O) |
| **상속 순서 확인** | 하위 예외를 먼저. `UnicodeDecodeError`/`ParserError` → `ValueError` 순 |
| **종료 코드 구분** | 정상 0 / 오류 1 / 사용자 중단 130 |
| **정확한 원인 우선** | 빈 파일에 "amount가 숫자가 아님"이 나오면 담당자가 헤맨다. 빈 데이터면 자료형 검사를 건너뛰고 "데이터가 비어 있습니다"로 |
| **부수 작업 실패는 중단 아님** | 로그·보고서 저장 실패는 경고만 남기고 진행 |

### 라이브러리 미설치는 시작하자마자

```python
try:
    import duckdb
    import pandas as pd
    import polars as pl
except ImportError as import_error:
    print(f"[오류] 필요한 라이브러리가 설치되어 있지 않습니다: {import_error.name}")
    print("       pip install -r requirements.txt")
    sys.exit(1)
```

---

## 8. 자체 검증

**정답을 하드코딩해 대조하는 방식은 데이터가 바뀌는 순간 무의미해진다.**
"어떤 데이터를 넣어도 반드시 성립해야 하는 관계"만 확인한다.

```python
def verify_results(result, bounds, kept_rows):
    """
    [기능] 결과가 신뢰할 수 있는 값인지 자동으로 점검한다.
    [설명] 잘못된 숫자가 그대로 보고되는 일을 막기 위한 안전장치다.
    """
    # 부분의 합 = 전체
    counted = int(result["count"].sum())
    assert counted == kept_rows, (
        f"그룹별 건수 합이 필터 통과 행 수와 다릅니다. "
        f"건수 합={counted:,}건, 필터 통과={kept_rows:,}건"
    )

    # 요구된 정렬이 실제로 지켜졌는가
    totals = result["total"].tolist()
    assert totals == sorted(totals, reverse=True), "총매출 내림차순이 아닙니다."

    # 항등식: 평균 × 건수 = 합계
    # 깨졌다면 서로 다른 행을 집계했다는 뜻이다
```

**assert 메시지에 실제 값을 넣는다.** "검증 실패"만 나오면 원인을 못 찾는다.

검증할 관계의 예:
- 부분의 합 = 전체 / 필터 결과 ≤ 원본
- 정렬·범위 등 요구된 조건이 실제로 지켜졌는가
- 같은 답을 다른 방법으로 구해 비교
- 항등식 (평균 × 건수 = 합계)

---

## 9. 테스트 구성

`pyproject.toml` — **커버리지를 기본 옵션에 넣는다.** 따로 붙여야 재는 구조면 아무도 안 잰다.

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
addopts = "-v --cov --cov-report=term-missing --cov-fail-under=80"

[tool.coverage.run]
include = ["광주_1반_박기택.py"]

[tool.coverage.report]
fail_under = 80
exclude_also = ["if __name__ == .__main__.:"]
```

`tests/conftest.py` — 한글 파일명은 `importlib`로 불러온다.

```python
import importlib.util
import sys
from pathlib import Path
import pytest

MODULE_PATH = Path(__file__).resolve().parent.parent / "광주_1반_박기택.py"


@pytest.fixture(scope="session")
def practice():
    """[기능] 제출 파일을 모듈로 불러와 테스트에 넘긴다."""
    spec = importlib.util.spec_from_file_location("practice3", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["practice3"] = module
    spec.loader.exec_module(module)
    return module
```

**원본 대용량 파일은 테스트에서 쓰지 않는다.** 손으로 계산해 검증할 수 있는 소형 표본을 만든다.

```python
# 12행짜리 표본에 결측·이상치·BOM을 모두 넣는다.
# 기대값을 손으로 계산해 둘 수 있어 "왜 이 숫자가 맞는지" 설명할 수 있고,
# 테스트 전체가 1초 안에 끝나 자주 돌릴 수 있다.
EXPECTED_Q1 = 350.0      # 손계산 결과
EXPECTED_LOWER = -400.0  # 350 - 1.5 × 500
```

`main()`을 임시 폴더에서 돌리려면 모듈의 `__file__`을 바꿔치기한다.

```python
@pytest.fixture
def 실행환경(practice, tmp_path, monkeypatch):
    """[기능] main()을 임시 폴더에서 실행하도록 환경을 바꿔치기한다."""
    monkeypatch.setattr(practice, "__file__", str(tmp_path / "실습.py"))
    monkeypatch.setattr(practice, "DATA_FILE", "sample.csv")
    write_sample_csv(tmp_path / "sample.csv")
    yield tmp_path
    practice.logger.handlers.clear()
```

### 반드시 넣을 테스트

| 종류 | 예 |
|---|---|
| **정상 경로** | 기대값과 정확히 일치하는가 |
| **오류 경로** | 파일 없음, 컬럼 누락, 형식 오류 → 각각 종료 코드 1 |
| **검증기 검증** | 일부러 값을 틀어놓고 잡아내는지. 항상 통과하는 검증은 무의미 |
| **감점 항목 고정** | 규칙을 어기면 실패하도록. 예: 반환 타입, 컬럼명, 소스 코드 검사 |
| **출력 순서** | 결론이 상세보다 먼저 나오는지 (`화면.index("핵심 결과") < 화면.index("상세")`) |

> `caplog`는 `logger.propagate = False`면 안 잡힌다. 화면 출력 확인은 **`capsys`**를 쓴다.

---

## 10. 체크리스트

제출 전 확인.

**코드**
- [ ] 머리말에 목적·입력·출력·오류 대응·실행 방법·변경 이력이 있는가
- [ ] 모든 함수에 `[기능]`/`[설명]` docstring이 있는가
- [ ] 바꿀 만한 값이 상단 상수 블록에 모여 있는가
- [ ] 여러 곳에서 같아야 하는 값이 상수 하나로 묶여 있는가
- [ ] 주석이 "무엇을"이 아니라 "왜"를 설명하는가

**로깅·출력**
- [ ] `print()` 대신 `logger`를 쓰는가 (파일에도 남는가)
- [ ] 결론이 상세 내역보다 **먼저** 나오는가
- [ ] 오래 걸리는 구간에 진행 표시가 있는가
- [ ] 큰 숫자가 지수 표기 없이 읽히는가
- [ ] 한글 섞인 표의 세로줄이 맞는가

**예외**
- [ ] 원인별로 나뉘어 있는가 (`except Exception` 뭉치기 금지)
- [ ] 해결 방법까지 안내하는가
- [ ] 하위 예외가 상위 예외보다 먼저 오는가
- [ ] Ctrl+C(130)와 종료 코드가 구분되는가
- [ ] 부수 작업(로그·보고서) 실패로 본 작업이 멈추지 않는가

**검증·테스트**
- [ ] 자체 검증이 하드코딩된 정답이 아니라 불변 관계를 보는가
- [ ] assert 메시지에 실제 값이 들어 있는가
- [ ] `pytest` 통과, 커버리지 80% 이상인가
- [ ] 오류 경로에도 테스트가 있는가
- [ ] 감점 항목이 테스트로 고정돼 있는가

---

## 부록. 과제에서 반복해 걸린 함정

다음에 또 만날 것들.

| 함정 | 증상 | 대응 |
|---|---|---|
| **BOM** | 첫 컬럼명이 `﻿order_id`로 잡힘 | `encoding="utf-8-sig"` |
| **f-string 백슬래시** | 파이썬 3.11까지 `f"{'\n'.join(x)}"`가 `SyntaxError` | 밖에서 변수로 만든 뒤 넣기 |
| **pandas groupby의 NaN** | 결측 그룹이 통째로 사라져 매출 누락 | 집계 전에 `fillna`로 이름 붙이기 |
| **도구별 분위수 보간** | Polars 기본 `nearest`, pandas·DuckDB `linear` | 한 번만 계산해 값으로 넘기기 |
| **동점 정렬** | 값이 같은 행 순서가 실행마다 달라짐 | 정렬 기준에 그룹 키까지 넣기 |
| **부동소수 비교** | 합산 순서 차이로 끝자리 불일치 | `rtol` 허용, `check_dtype=False` |
| **빈 파일의 자료형** | 데이터가 없으면 문자열로 읽혀 엉뚱한 오류 안내 | 빈 경우 자료형 검사 건너뛰기 |
| **성능 측정의 콜드 스타트** | 첫 실행이 68% 느려 결과 왜곡 | 예열 1회 후 측정 |
| **`caplog`가 안 잡힘** | `propagate = False`면 최상위로 안 올라감 | `capsys`로 화면 출력 확인 |
