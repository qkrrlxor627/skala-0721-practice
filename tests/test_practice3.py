"""
================================================================
[프로그램명] 실습 3 단위 테스트
================================================================

■ 목적
    제출 파일(광주_1반_박기택.py)이 요구사항대로 동작하는지 자동으로 확인한다.
    특히 아래 다섯 가지는 어긋나면 곧바로 감점 대상이므로 회귀 테스트로 못박는다.
      1) IQR 공식        - 하한 Q1-1.5×IQR / 상한 Q3+1.5×IQR
      2) named aggregation - 결과 컬럼명이 total / mean / count
      3) Polars Lazy      - scan_csv 사용 (read_csv 아님)
      4) collect() 호출   - 반환값이 DataFrame (LazyFrame 아님)
      5) timeit 반복 횟수 - 세 도구가 모두 같은 number 사용

■ 시험 데이터
    원본(77MB, 100만 행) 대신 conftest.py 의 12행짜리 표본을 쓴다.
    기대값을 손으로 계산해 둘 수 있어 "왜 이 숫자가 맞는지" 설명할 수 있고,
    테스트 전체가 1초 안에 끝나 자주 돌릴 수 있다.

■ 실행 방법
    pytest                (커버리지 80% 미만이면 실패)

■ 작성자 : 박기택
■ 최초 작성일 : 2026-07-21
================================================================
"""

import logging

import pandas as pd
import polars as pl
import pytest
from conftest import (
    EXPECTED_GROUPS,
    EXPECTED_IQR,
    EXPECTED_KEPT_ROWS,
    EXPECTED_LOWER,
    EXPECTED_Q1,
    EXPECTED_Q3,
    EXPECTED_UPPER,
    write_sample_csv,
)


# ================================================================
# 1. 데이터 읽기 (load_sales)
# ================================================================


def test_load_sales_정상_읽기(practice, sample_csv):
    """[기능] 시험용 CSV 를 문제없이 읽어 12행을 돌려주는지 확인한다."""
    frame = practice.load_sales(sample_csv)

    assert len(frame) == 12
    assert frame["amount"].isna().sum() == 1  # amount 결측 1건
    assert frame["region"].isna().sum() == 2  # region 결측 2건
    assert frame["category"].isna().sum() == 2  # category 결측 2건


def test_load_sales_BOM_컬럼명_정상(practice, sample_csv):
    """
    [기능] BOM 이 붙은 파일에서도 첫 컬럼 이름이 깨지지 않는지 확인한다.
    [설명] encoding='utf-8-sig' 를 빠뜨리면 첫 컬럼이 '\\ufefforder_id' 로 읽힌다.
           눈에 보이지 않는 차이라 사람이 발견하기 어려워 테스트로 고정한다.
    """
    frame = practice.load_sales(sample_csv)

    assert frame.columns[0] == "order_id"
    assert not any(name.startswith("﻿") for name in frame.columns)


def test_load_sales_파일_없음(practice, tmp_path):
    """[기능] 없는 파일을 지정하면 OSError 가 나는지 확인한다."""
    with pytest.raises(OSError):
        practice.load_sales(tmp_path / "없는파일.csv")


def test_load_sales_필수컬럼_누락(practice, tmp_path):
    """[기능] amount 컬럼이 없으면 ValueError 와 함께 실제 컬럼 목록을 알려주는지 확인한다."""
    path = tmp_path / "컬럼누락.csv"
    path.write_text("order_id,region,category\n1,서울,전자\n", encoding="utf-8")

    with pytest.raises(ValueError, match="필수 컬럼이 없습니다"):
        practice.load_sales(path)


def test_load_sales_amount가_숫자가_아님(practice, tmp_path):
    """
    [기능] amount 가 문자열로 읽히면 ValueError 를 내는지 확인한다.
    [설명] 그냥 두면 합계가 문자열 이어붙이기가 되어 조용히 틀린 보고서가 나온다.
    """
    path = tmp_path / "문자금액.csv"
    path.write_text(
        "order_id,region,category,amount\n1,서울,전자,백만원\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="숫자가 아닙니다"):
        practice.load_sales(path)


# ================================================================
# 2. 기초 탐색 (collect_eda)
# ================================================================


def test_collect_eda_요약값(practice, sample_csv):
    """[기능] EDA 결과에 행·열 수와 컬럼별 결측치가 정확히 담기는지 확인한다."""
    frame = practice.load_sales(sample_csv)
    summary = practice.collect_eda(frame)

    assert summary["rows"] == 12
    assert summary["columns"] == 11
    assert summary["null_counts"]["region"] == 2
    assert summary["null_counts"]["amount"] == 1
    # info() / describe() 출력이 문자열로 잡혀야 로그와 보고서에 남길 수 있다
    assert "RangeIndex" in summary["info_text"]
    assert "count" in summary["describe_text"]


# ================================================================
# 3. IQR 계산 (compute_iqr_bounds) - 감점 항목 ①
# ================================================================


def test_compute_iqr_bounds_손계산과_일치(practice, sample_csv):
    """
    [기능] IQR 경계가 손으로 계산한 값과 정확히 같은지 확인한다.
    [설명] 표본의 amount(결측 제외 11개)로 계산하면
           Q1=350, Q3=850, IQR=500, 하한=-400, 상한=1600 이어야 한다.
           공식을 잘못 적용하면(예: 부호를 뒤집거나 1.5를 빠뜨리면) 여기서 걸린다.
    """
    frame = practice.load_sales(sample_csv)
    result = practice.compute_iqr_bounds(frame[practice.TARGET_COLUMN])

    assert result.q1 == EXPECTED_Q1
    assert result.q3 == EXPECTED_Q3
    assert result.iqr == EXPECTED_IQR
    assert result.lower == EXPECTED_LOWER
    assert result.upper == EXPECTED_UPPER


def test_compute_iqr_bounds_공식_자체를_검증(practice):
    """
    [기능] 어떤 값이 들어와도 하한/상한이 공식대로 계산되는지 확인한다.
    [설명] 위 테스트가 특정 표본에 대한 확인이라면, 이 테스트는 공식 자체를 본다.
           손으로 계산 가능한 값(1~9, 100)을 넣어 Q1=3.25, Q3=7.75 를 기대한다.
    """
    series = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 100], dtype="float64")
    result = practice.compute_iqr_bounds(series)

    assert result.q1 == pytest.approx(3.25)
    assert result.q3 == pytest.approx(7.75)
    assert result.iqr == pytest.approx(result.q3 - result.q1)
    assert result.lower == pytest.approx(result.q1 - 1.5 * result.iqr)
    assert result.upper == pytest.approx(result.q3 + 1.5 * result.iqr)


def test_compute_iqr_bounds_값이_전부_결측(practice):
    """[기능] 유효한 값이 하나도 없으면 ValueError 로 알리는지 확인한다."""
    with pytest.raises(ValueError, match="유효한 값이 없어"):
        practice.compute_iqr_bounds(pd.Series([None, None], dtype="float64"))


def test_iqr_필터_전후_행수(practice, sample_csv, bounds):
    """
    [기능] IQR 필터가 이상치와 결측만 정확히 걸러내는지 확인한다.
    [설명] 전체 12행 중 amount 결측 1건과 이상치(100000) 1건이 빠져 10행이 남아야 한다.
    """
    frame = practice.load_sales(sample_csv)
    kept = frame[
        frame["amount"].notna() & frame["amount"].between(bounds.lower, bounds.upper)
    ]

    assert len(frame) == 12
    assert len(kept) == EXPECTED_KEPT_ROWS
    assert 100000 not in kept["amount"].values


# ================================================================
# 4. Pandas 집계 - 감점 항목 ②
# ================================================================


def test_aggregate_pandas_컬럼명이_named_aggregation_형식(practice, sample_csv, bounds):
    """
    [기능] 결과 컬럼명이 total / mean / count 인지 확인한다.
    [설명] agg({'amount':'sum'}) 방식을 쓰면 컬럼명이 'amount' 로 남는다.
           named aggregation 을 썼는지 여부가 이 한 줄로 드러난다.
    """
    result = practice.aggregate_pandas(sample_csv, bounds)

    assert set(result.columns) == {"region", "category", "total", "mean", "count"}


def test_aggregate_pandas_그룹별_집계값(practice, sample_csv, bounds):
    """[기능] 그룹별 총매출·건수가 손으로 계산한 값과 일치하는지 확인한다."""
    result = practice.normalize_result(practice.aggregate_pandas(sample_csv, bounds))

    assert len(result) == len(EXPECTED_GROUPS)
    for row in result.itertuples(index=False):
        expected_total, expected_count = EXPECTED_GROUPS[(row.region, row.category)]
        assert row.total == pytest.approx(expected_total)
        assert row.count == expected_count


def test_aggregate_pandas_총매출_내림차순_정렬(practice, sample_csv, bounds):
    """[기능] 요구사항대로 총매출 내림차순으로 정렬되는지 확인한다."""
    result = practice.aggregate_pandas(sample_csv, bounds)
    totals = result["total"].tolist()

    assert totals == sorted(totals, reverse=True)


def test_결측_그룹이_이름을_얻어_살아남음(practice, sample_csv, bounds):
    """
    [기능] region·category 결측이 '미상'/'미분류' 그룹으로 집계에 포함되는지 확인한다.
    [설명] 결측을 버리면 해당 매출(600+700+800=2100원)이 보고서에서 통째로 사라진다.
           세 도구의 결과가 갈라지는 가장 큰 원인이기도 하다.
    """
    result = practice.aggregate_pandas(sample_csv, bounds)

    assert (result["region"] == practice.UNKNOWN_REGION).any()
    assert (result["category"] == practice.UNKNOWN_CATEGORY).any()
    # 결측 그룹의 매출이 실제로 합산되었는지 확인 (600 + 700 + 800)
    unknown_total = result[
        (result["region"] == practice.UNKNOWN_REGION)
        | (result["category"] == practice.UNKNOWN_CATEGORY)
    ]["total"].sum()
    assert unknown_total == pytest.approx(2100.0)


def test_amount_결측행은_건수에_포함되지_않음(practice, sample_csv, bounds):
    """[기능] 금액을 알 수 없는 행이 count 에 섞여 들어가지 않는지 확인한다."""
    result = practice.aggregate_pandas(sample_csv, bounds)

    assert result["count"].sum() == EXPECTED_KEPT_ROWS


# ================================================================
# 5. Polars Lazy 집계 - 감점 항목 ③, ④
# ================================================================


def test_aggregate_polars_collect_호출됨(practice, sample_csv, bounds):
    """
    [기능] 반환값이 실행이 끝난 결과인지 확인한다. (collect() 누락 회귀 방지)
    [설명] collect() 를 빠뜨리면 LazyFrame(실행 계획)만 돌아오고 계산은 일어나지 않는다.
           타입만 확인하면 이 실수를 확실히 잡을 수 있다.
    """
    result = practice.aggregate_polars(sample_csv, bounds)

    assert isinstance(result, pd.DataFrame)
    assert not isinstance(result, pl.LazyFrame)
    assert len(result) == len(EXPECTED_GROUPS)


def test_aggregate_polars_scan_csv_사용(practice):
    """
    [기능] Lazy API(scan_csv)를 썼는지, 즉시 실행(read_csv)을 쓰지 않았는지 확인한다.
    [설명] 소스 코드를 직접 확인하는 방식이다. 두 함수는 결과가 같아서 값만 봐서는
           구분할 수 없는데, Lazy API 사용 여부 자체가 요구사항이라 코드로 검사한다.
    """
    import inspect

    source = inspect.getsource(practice.aggregate_polars)

    assert "pl.scan_csv" in source
    assert "pl.read_csv" not in source
    assert ".collect()" in source


# ================================================================
# 6. DuckDB 집계
# ================================================================


def test_aggregate_duckdb_그룹별_집계값(practice, sample_csv, bounds):
    """[기능] SQL GROUP BY 집계 결과가 손으로 계산한 값과 일치하는지 확인한다."""
    import duckdb

    connection = duckdb.connect()
    try:
        result = practice.normalize_result(
            practice.aggregate_duckdb(connection, sample_csv, bounds)
        )
    finally:
        connection.close()

    assert len(result) == len(EXPECTED_GROUPS)
    for row in result.itertuples(index=False):
        expected_total, expected_count = EXPECTED_GROUPS[(row.region, row.category)]
        assert row.total == pytest.approx(expected_total)
        assert row.count == expected_count


# ================================================================
# 7. 세 도구 결과 동일성 - 이 실습의 핵심
# ================================================================


def test_세_도구_결과가_모두_동일(practice, sample_csv, bounds):
    """
    [기능] Pandas·Polars·DuckDB 세 결과가 완전히 같은지 확인한다.
    [설명] 결측 그룹 처리, IQR 경계, 정렬 기준 중 하나라도 어긋나면 여기서 실패한다.
           이 실습의 결론('세 도구는 같은 답을 낸다')을 코드로 보증하는 테스트다.
    """
    import duckdb

    connection = duckdb.connect()
    try:
        pandas_result = practice.aggregate_pandas(sample_csv, bounds)
        polars_result = practice.aggregate_polars(sample_csv, bounds)
        duckdb_result = practice.aggregate_duckdb(connection, sample_csv, bounds)
    finally:
        connection.close()

    ok_polars, reason_polars = practice.compare_results(pandas_result, polars_result)
    ok_duckdb, reason_duckdb = practice.compare_results(pandas_result, duckdb_result)

    assert ok_polars, f"Pandas 와 Polars 결과가 다릅니다: {reason_polars}"
    assert ok_duckdb, f"Pandas 와 DuckDB 결과가 다릅니다: {reason_duckdb}"


def test_compare_results_다른_결과를_잡아냄(practice, sample_csv, bounds):
    """
    [기능] 결과가 실제로 다를 때 비교 함수가 '불일치'로 판정하는지 확인한다.
    [설명] 항상 '일치'만 반환하는 비교 함수는 아무것도 검증하지 못한다.
           일부러 값을 틀어놓고 잡아내는지 확인해야 비교가 믿을 만해진다.
    """
    original = practice.aggregate_pandas(sample_csv, bounds)
    tampered = original.copy()
    tampered.iloc[0, tampered.columns.get_loc("total")] += 1000

    ok, reason = practice.compare_results(original, tampered)

    assert ok is False
    assert reason  # 어디가 달랐는지 사유가 남아야 한다


def test_normalize_result_컬럼순서_통일(practice, sample_csv, bounds):
    """[기능] 컬럼 순서와 행 번호가 표준 형태로 정리되는지 확인한다."""
    shuffled = practice.aggregate_pandas(sample_csv, bounds)[
        ["count", "mean", "total", "category", "region"]
    ]
    result = practice.normalize_result(shuffled)

    assert list(result.columns) == practice.RESULT_COLUMNS
    assert list(result.index) == list(range(len(result)))


# ================================================================
# 8. 성능 측정 - 감점 항목 ⑤
# ================================================================


def test_benchmark_세_도구가_같은_반복횟수(practice):
    """
    [기능] 세 도구가 모두 같은 number 로 측정되는지 확인한다.
    [설명] 반복 횟수가 다르면 총 실행 시간 비교가 성립하지 않는다.
           측정 결과에 number 를 함께 담아 두었으므로, 세 값이 같은지로 검증할 수 있다.
    """
    cases = [(name, lambda: sum(range(100))) for name in ("Pandas", "Polars", "DuckDB")]
    results = practice.benchmark(cases, number=2)

    assert len(results) == 3
    assert {item.number for item in results} == {2}


def test_benchmark_기본값이_TIMEIT_NUMBER(practice):
    """[기능] 반복 횟수를 따로 주지 않으면 상수 TIMEIT_NUMBER 가 그대로 쓰이는지 확인한다."""
    results = practice.benchmark([("Pandas", lambda: None)])

    assert results[0].number == practice.TIMEIT_NUMBER
    assert practice.TIMEIT_NUMBER >= 3  # 요구사항: 3번 이상


def test_benchmark_예열_후_측정(practice):
    """
    [기능] 측정 전에 예열이 수행되고, 예열 실행은 측정 결과에 포함되지 않는지 확인한다.
    [설명] 첫 실행에 붙는 캐시·초기화 비용을 걸러내는 장치다. 예열이 사라지면
           측정값이 다시 흔들리므로 호출 횟수로 고정해 둔다.
    """
    호출횟수 = []
    practice.benchmark([("Pandas", lambda: 호출횟수.append(1))], number=4)

    # 예열 1회 + 본 측정 4회 = 5회 호출되어야 한다
    assert len(호출횟수) == practice.WARMUP_NUMBER + 4


def test_benchmark_예열은_세_도구_모두_동일(practice):
    """[기능] 특정 도구만 예열해 유리해지는 일이 없도록 모든 도구가 같게 처리되는지 확인한다."""
    호출횟수 = {"Pandas": 0, "Polars": 0, "DuckDB": 0}

    def 세기(이름):
        def 실행():
            호출횟수[이름] += 1

        return 실행

    practice.benchmark([(이름, 세기(이름)) for 이름 in 호출횟수], number=2)

    assert set(호출횟수.values()) == {practice.WARMUP_NUMBER + 2}


def test_benchmark_총시간_짧은_순_정렬(practice):
    """[기능] 측정 결과가 빠른 순으로 정렬되어 순위를 바로 쓸 수 있는지 확인한다."""
    cases = [
        ("느림", lambda: sum(range(200_000))),
        ("빠름", lambda: None),
    ]
    results = practice.benchmark(cases, number=1)

    assert results[0].tool == "빠름"
    assert results[0].total_sec <= results[1].total_sec


def test_benchmark_반복횟수가_0이면_오류(practice):
    """[기능] 반복 횟수가 1 미만이면 ValueError 를 내는지 확인한다. (0으로 나누기 방지)"""
    with pytest.raises(ValueError, match="1 이상"):
        practice.benchmark([("Pandas", lambda: None)], number=0)


# ================================================================
# 9. 자체 검증 (verify_results)
# ================================================================


def test_verify_results_정상_결과는_통과(practice, sample_csv, bounds):
    """[기능] 정상적으로 계산된 결과는 검증을 통과하는지 확인한다."""
    result = practice.normalize_result(practice.aggregate_pandas(sample_csv, bounds))

    practice.verify_results(result, bounds, EXPECTED_KEPT_ROWS)  # 예외가 없어야 한다


def test_verify_results_건수_불일치를_잡아냄(practice, sample_csv, bounds):
    """[기능] 그룹별 건수 합이 필터 통과 행 수와 다르면 검증에 걸리는지 확인한다."""
    result = practice.normalize_result(practice.aggregate_pandas(sample_csv, bounds))

    with pytest.raises(AssertionError, match="건수 합"):
        practice.verify_results(result, bounds, EXPECTED_KEPT_ROWS + 1)


def test_verify_results_정렬_어긋남을_잡아냄(practice, sample_csv, bounds):
    """[기능] 총매출 내림차순이 아니면 검증에 걸리는지 확인한다."""
    result = practice.normalize_result(practice.aggregate_pandas(sample_csv, bounds))
    reversed_result = result.iloc[::-1].reset_index(drop=True)

    with pytest.raises(AssertionError, match="내림차순"):
        practice.verify_results(reversed_result, bounds, EXPECTED_KEPT_ROWS)


def test_verify_results_IQR_경계_뒤집힘을_잡아냄(practice, sample_csv, bounds):
    """[기능] 하한이 상한보다 크면(공식을 뒤집어 쓴 경우) 검증에 걸리는지 확인한다."""
    result = practice.normalize_result(practice.aggregate_pandas(sample_csv, bounds))
    flipped = practice.IQRBounds(
        q1=bounds.q1, q3=bounds.q3, iqr=bounds.iqr, lower=bounds.upper, upper=bounds.lower
    )

    with pytest.raises(AssertionError, match="하한이 상한보다"):
        practice.verify_results(result, flipped, EXPECTED_KEPT_ROWS)


def test_verify_results_컬럼명_어긋남을_잡아냄(practice, sample_csv, bounds):
    """[기능] 결과 컬럼명이 규칙과 다르면 검증에 걸리는지 확인한다."""
    result = practice.normalize_result(practice.aggregate_pandas(sample_csv, bounds))
    renamed = result.rename(columns={"total": "amount"})

    with pytest.raises(AssertionError, match="결과 컬럼이"):
        practice.verify_results(renamed, bounds, EXPECTED_KEPT_ROWS)


def test_verify_results_평균과_합계_불일치를_잡아냄(practice, sample_csv, bounds):
    """[기능] 평균 × 건수 ≠ 합계 이면(서로 다른 행을 집계한 경우) 검증에 걸리는지 확인한다."""
    result = practice.normalize_result(practice.aggregate_pandas(sample_csv, bounds))
    result.loc[0, "mean"] = result.loc[0, "mean"] * 2

    with pytest.raises(AssertionError, match="평균 × 건수"):
        practice.verify_results(result, bounds, EXPECTED_KEPT_ROWS)


# ================================================================
# 10. 보고서 작성 (format_table / build_report / write_report)
# ================================================================


@pytest.fixture
def report_context(practice, sample_csv, bounds):
    """
    [기능] 보고서 작성 함수에 넘길 실행 결과 모음을 만든다.
    [설명] 보고서 관련 테스트가 매번 같은 준비를 반복하지 않도록 픽스처로 분리했다.

    Returns:
        dict: build_report() 가 요구하는 형태의 실행 결과.
    """
    frame = practice.load_sales(sample_csv)
    result = practice.normalize_result(practice.aggregate_pandas(sample_csv, bounds))
    benchmarks = practice.benchmark(
        [
            ("Polars", lambda: None),
            ("DuckDB", lambda: None),
            ("Pandas", lambda: sum(range(10_000))),
        ],
        number=1,
    )
    return {
        "eda": practice.collect_eda(frame),
        "bounds": bounds,
        "rows_before": 12,
        "rows_after": EXPECTED_KEPT_ROWS,
        "rows_removed": 12 - EXPECTED_KEPT_ROWS,
        # 표본 12행 중 amount 결측 1건, IQR 범위 밖(100000) 1건이 빠진다.
        # 성격이 다른 두 사유를 합쳐서 보고하면 결측까지 이상치로 잘못 전달된다.
        "missing_removed": 1,
        "outlier_removed": 1,
        "result": result,
        "matches": {"Pandas = Polars": True, "Pandas = DuckDB": True},
        "mismatch_reasons": {},
        "benchmarks": benchmarks,
    }


def test_format_table_상위_N개만_출력(practice, sample_csv, bounds):
    """[기능] 표에 상위 N개 행만 담기는지 확인한다."""
    result = practice.normalize_result(practice.aggregate_pandas(sample_csv, bounds))
    table = practice.format_table(result, top_n=3)

    assert len(table.splitlines()) == 3
    assert table.startswith("| 1 |")


def test_build_report_플레이스홀더가_남지_않음(practice, report_context):
    """
    [기능] 보고서에 `[값 입력]` 같은 빈칸이 남지 않는지 확인한다.
    [설명] 양식(resultEx.md)을 그대로 복사해 두고 값만 채우지 않으면
           빈 보고서를 제출하게 된다. 자동 생성이 실제로 값을 채웠는지 확인한다.
    """
    report = practice.build_report(report_context)

    assert "입력]" not in report
    assert "[지역]" not in report
    assert "[카테고리]" not in report


def test_build_report_제외_사유가_분리되어_표기(practice, report_context):
    """
    [기능] 보고서가 제외 건수를 결측과 이상치로 나눠 적는지 확인한다.
    [설명] "2건의 이상치를 제거했다"고만 쓰면, 금액을 몰라서 뺀 행까지 이상치로
           읽힌다. 두 사유는 성격이 다르므로 나눠서 보고해야 한다.
    """
    report = practice.build_report(report_context)

    assert "결측으로 제외" in report
    assert "IQR 범위 밖으로 제외" in report
    # 합쳐서 한 숫자로만 내면 오해가 생긴다는 설명까지 들어 있어야 한다
    assert "이상치로 잘못 전달" in report


def test_build_report_실측값_포함(practice, report_context):
    """[기능] 보고서에 IQR 값·행 수·반복 횟수 같은 실측값이 실제로 들어가는지 확인한다."""
    report = practice.build_report(report_context)

    assert f"{EXPECTED_UPPER:,.2f}" in report  # 상한 1,600.00
    assert "12,000" not in report  # 잘못된 자리 표기가 없는지
    assert f"`{practice.TIMEIT_NUMBER}`회" in report
    assert "모두 동일합니다" in report


def test_build_report_불일치시_원인_표시(practice, report_context):
    """[기능] 세 도구 결과가 다를 때 보고서에 원인이 적히는지 확인한다."""
    report_context["matches"]["Pandas = Polars"] = False
    report_context["mismatch_reasons"]["Pandas = Polars"] = "총매출 값이 다릅니다"

    report = practice.build_report(report_context)

    assert "결과 차이가 발생했습니다" in report
    assert "총매출 값이 다릅니다" in report
    assert "| Pandas = Polars | 불일치 |" in report


def test_write_report_파일_생성(practice, tmp_path):
    """[기능] 상위 폴더가 없어도 만들어서 저장하는지 확인한다."""
    path = tmp_path / "Docs" / "result.md"

    assert practice.write_report(path, "# 보고서") is True
    assert path.read_text(encoding="utf-8") == "# 보고서"


def test_write_report_저장_실패해도_중단되지_않음(practice, tmp_path):
    """
    [기능] 저장에 실패해도 예외를 던지지 않고 False 만 돌려주는지 확인한다.
    [설명] 보고서 저장 실패는 집계 결과와 무관하다. 이미 화면과 로그에 결과가 남아 있으므로
           프로그램 전체를 중단시킬 이유가 없다.
    """
    # 파일이 있는 자리에 폴더를 만들려 하면 저장이 실패한다
    blocker = tmp_path / "blocked"
    blocker.write_text("파일", encoding="utf-8")

    assert practice.write_report(blocker / "result.md", "# 보고서") is False


# ================================================================
# 10-2. 화면 출력 (format_won / 표 정렬 / 출력 순서)
# ================================================================


@pytest.mark.parametrize(
    "금액, 기대",
    [
        (74_992_750_244, "749.9억원"),
        (2_495_267, "249.5만원"),
        (1_234_500_000_000, "1.23조원"),
        (5_000, "5,000원"),
    ],
)
def test_format_won_단위_변환(practice, 금액, 기대):
    """
    [기능] 큰 금액이 억·조 단위로 읽기 쉽게 바뀌는지 확인한다.
    [설명] 74,992,750,244원은 자릿수를 세어야 규모가 잡히지만 749.9억원은 바로 읽힌다.
    """
    assert practice.format_won(금액) == 기대


def test_display_width_한글은_두_칸(practice):
    """
    [기능] 한글이 영문자의 두 배 폭으로 계산되는지 확인한다.
    [설명] 표의 세로줄을 맞추려면 글자 수가 아니라 화면에서 차지하는 칸 수를 알아야 한다.
    """
    assert practice.display_width("서울") == 4
    assert practice.display_width("seoul") == 5
    assert practice.display_width("가A") == 3


def test_format_result_table_자리_정렬(practice, sample_csv, bounds):
    """
    [기능] 한글이 섞여도 표의 모든 줄이 같은 폭으로 맞춰지는지 확인한다.
    [설명] 지역·카테고리 이름은 길이가 제각각이라, 폭 계산이 틀리면 세로줄이 어긋난다.
    """
    result = practice.normalize_result(practice.aggregate_pandas(sample_csv, bounds))
    표 = practice.format_result_table(result, top_n=3)
    줄 = 표.splitlines()

    assert len(줄) == 2 + 3  # 머리글 + 구분선 + 자료 3줄
    폭 = {practice.display_width(한줄) for 한줄 in 줄}
    assert len(폭) == 1, f"줄마다 폭이 다릅니다: {폭}"


def test_format_result_table_지수표기_없음(practice, sample_csv, bounds):
    """
    [기능] 총매출이 7.49e+10 같은 지수 표기로 나오지 않는지 확인한다.
    [설명] 지수 표기는 규모가 한눈에 들어오지 않아 보고서에 그대로 쓸 수 없다.
    """
    result = practice.normalize_result(practice.aggregate_pandas(sample_csv, bounds))
    표 = practice.format_result_table(result)

    assert "e+" not in 표


def test_출력_순서가_결론_먼저(practice, 실행환경, capsys):
    """
    [기능] 결론(핵심 결과)이 상세 내역보다 먼저 출력되는지 확인한다.
    [설명] 이 프로그램의 출력 설계 자체를 고정하는 테스트다.
           예전에는 df.info()·describe() 를 먼저 찍어 정작 알고 싶은
           '세 도구가 같은 답을 냈는가', '어느 쪽이 빠른가'가 화면 아래로 밀렸다.
           나중에 출력을 손대다 순서가 되돌아가면 여기서 걸린다.
    """
    assert practice.main() == 0
    화면 = capsys.readouterr().out

    핵심 = 화면.index("핵심 결과")
    상세 = 화면.index("이하 상세")
    eda = 화면.index("df.info()")

    assert 핵심 < 상세 < eda, "결론이 상세 내역보다 뒤에 출력되고 있습니다."
    # 요구사항이 요구하는 출력이 상세 쪽에 빠짐없이 들어 있어야 한다
    assert "isnull().sum()" in 화면
    assert "describe()" in 화면


def test_출력에_핵심_수치가_모두_포함(practice, 실행환경, capsys):
    """[기능] 핵심 결과 블록에 네 가지 결론이 모두 담기는지 확인한다."""
    assert practice.main() == 0
    화면 = capsys.readouterr().out

    assert "세 도구 집계 결과" in 화면 and "일치" in 화면
    assert "가장 빠른 도구" in 화면
    assert "이상치 제거" in 화면
    assert "매출 1위 그룹" in 화면


# ================================================================
# 11. 로깅 준비 (setup_logging)
# ================================================================


def test_setup_logging_파일과_화면_모두_기록(practice, tmp_path):
    """[기능] 로그 파일이 만들어지고 화면 출력도 함께 설정되는지 확인한다."""
    log_path = practice.setup_logging(tmp_path)

    try:
        assert log_path == tmp_path / practice.LOG_FILE
        practice.logger.info("시험 기록")
        # 파일에 실제로 쓰였는지 확인하려면 버퍼를 비워야 한다
        for handler in practice.logger.handlers:
            handler.flush()
        assert "시험 기록" in log_path.read_text(encoding="utf-8")
        # 화면(stdout)과 파일 두 곳에 기록된다
        assert len(practice.logger.handlers) == 2
    finally:
        practice.logger.handlers.clear()


def test_setup_logging_파일_못만들면_화면만(practice, tmp_path, monkeypatch):
    """
    [기능] 로그 파일을 만들 수 없어도 중단하지 않고 화면 기록만으로 계속하는지 확인한다.
    [설명] 기록을 남기려다 본 작업(집계)을 멈추게 하면 안 된다.
    """

    def 실패하는_핸들러(*args, **kwargs):
        raise OSError("권한이 없습니다")

    monkeypatch.setattr(logging, "FileHandler", 실패하는_핸들러)

    try:
        assert practice.setup_logging(tmp_path) is None
        assert len(practice.logger.handlers) == 1  # 화면 담당자만 남는다
    finally:
        practice.logger.handlers.clear()


# ================================================================
# 12. 전체 흐름 (run_pipeline / main)
# ================================================================


@pytest.fixture
def 실행환경(practice, tmp_path, monkeypatch):
    """
    [기능] main() 을 임시 폴더에서 실행할 수 있도록 환경을 바꿔치기한다.
    [설명] main() 은 `Path(__file__).parent` 를 기준 폴더로 삼는다.
           모듈의 __file__ 을 임시 폴더 안으로 바꾸면 입력 파일도, 로그도, 보고서도
           모두 임시 폴더에 만들어져 실제 프로젝트 파일을 건드리지 않는다.

    Returns:
        Path: 시험용 CSV 가 놓인 임시 폴더.
    """
    monkeypatch.setattr(practice, "__file__", str(tmp_path / "실습.py"))
    monkeypatch.setattr(practice, "DATA_FILE", "sample.csv")
    write_sample_csv(tmp_path / "sample.csv")
    yield tmp_path
    practice.logger.handlers.clear()


def test_main_정상_실행(practice, 실행환경):
    """[기능] 전체 흐름이 끝까지 돌고 종료 코드 0 과 보고서를 남기는지 확인한다."""
    exit_code = practice.main()

    assert exit_code == 0
    report = (실행환경 / practice.REPORT_FILE).read_text(encoding="utf-8")
    assert "Practice 3 실행 결과 보고서" in report
    assert (실행환경 / practice.LOG_FILE).exists()


def test_main_대용량_파일_경고(practice, 실행환경, monkeypatch):
    """[기능] 큰 입력 파일에 대해 메모리 경고를 남기고도 정상 진행하는지 확인한다."""
    monkeypatch.setattr(practice, "LARGE_FILE_WARN_BYTES", 1)

    assert practice.main() == 0


def test_main_파일_없음(practice, 실행환경, monkeypatch):
    """[기능] 입력 파일이 없으면 안내 후 종료 코드 1 을 돌려주는지 확인한다."""
    monkeypatch.setattr(practice, "DATA_FILE", "없는파일.csv")

    assert practice.main() == 1


def test_main_머리글만_있고_데이터_없음(practice, 실행환경, capsys):
    """
    [기능] 머리글만 있는 파일은 '데이터 없음'으로 정확히 안내하는지 확인한다.
    [설명] 데이터가 없으면 amount 의 자료형을 판단할 근거도 없어 문자열로 읽힌다.
           이때 자료형부터 검사하면 "amount 가 숫자가 아니다"라는 엉뚱한 안내가 나간다.
           담당자가 원인을 헤매지 않도록 실제 원인을 알려야 한다.

           안내 문구는 caplog 가 아니라 화면 출력으로 확인한다.
           이 프로그램의 logger 는 propagate=False 라 기록이 최상위 logger 로
           올라가지 않아 caplog 로는 잡히지 않기 때문이다.
    """
    write_sample_csv(실행환경 / "sample.csv", rows=[])

    assert practice.main() == 1
    assert "비어 있습니다" in capsys.readouterr().out


def test_main_완전히_빈_파일(practice, 실행환경):
    """[기능] 내용이 한 글자도 없는 파일은 읽기 단계에서 안내하는지 확인한다."""
    (실행환경 / "sample.csv").write_text("", encoding="utf-8")

    assert practice.main() == 1


def test_main_CSV_형식_깨짐(practice, 실행환경, capsys):
    """
    [기능] 열 개수가 맞지 않는 행이 섞이면 형식 오류로 안내하는지 확인한다.
    [설명] 머리글이 4열인데 3번째 줄만 6열이라 파싱이 중단된다.
           몇 번째 줄이 문제인지까지 안내해야 담당자가 원본을 고칠 수 있다.
    """
    (실행환경 / "sample.csv").write_text(
        "order_id,region,category,amount\n"
        "1,서울,전자,100\n"
        "2,부산,의류,200,초과항목,하나더\n",
        encoding="utf-8",
    )

    assert practice.main() == 1
    assert "CSV 형식이 잘못됐습니다" in capsys.readouterr().out


def test_main_인코딩_오류(practice, 실행환경):
    """[기능] UTF-8 이 아닌 파일은 인코딩 문제로 안내하는지 확인한다."""
    # CP949(한국어 윈도우 기본값)로 저장하면 UTF-8 로는 읽을 수 없다
    (실행환경 / "sample.csv").write_bytes(
        "order_id,region,category,amount\n1,서울,전자,100\n".encode("cp949")
    )

    assert practice.main() == 1


def test_main_IQR_통과_행이_0건(practice, 실행환경, monkeypatch):
    """[기능] 필터가 모든 행을 걸러내면 빈 보고서 대신 오류로 알리는지 확인한다."""
    monkeypatch.setattr(
        practice,
        "compute_iqr_bounds",
        lambda series: practice.IQRBounds(0.0, 0.0, 0.0, 1e18, 1e18 + 1),
    )

    assert practice.main() == 1


def test_main_세_도구_결과_불일치(practice, 실행환경, monkeypatch):
    """
    [기능] 도구 간 결과가 다르면 보고서는 남기되 실패(종료 코드 1)로 알리는지 확인한다.
    [설명] 어느 쪽이 맞는지 알 수 없는 상태이므로 '성공'으로 보고해서는 안 된다.
    """
    원래함수 = practice.aggregate_polars

    def 값이_틀어진_집계(path, bounds):
        result = 원래함수(path, bounds)
        result.loc[0, "total"] += 999
        return result

    monkeypatch.setattr(practice, "aggregate_polars", 값이_틀어진_집계)

    assert practice.main() == 1
    # 결과가 달라도 원인을 확인할 수 있도록 보고서는 남아야 한다
    report = (실행환경 / practice.REPORT_FILE).read_text(encoding="utf-8")
    assert "결과 차이가 발생했습니다" in report


def test_main_자체검증_실패(practice, 실행환경, monkeypatch):
    """[기능] 자체 검증에 실패하면 보고서를 만들지 않고 종료 코드 1 을 돌려주는지 확인한다."""

    def 항상_실패(result, bounds, kept_rows):
        raise AssertionError("일부러 낸 검증 실패")

    monkeypatch.setattr(practice, "verify_results", 항상_실패)

    assert practice.main() == 1
    assert not (실행환경 / practice.REPORT_FILE).exists()
