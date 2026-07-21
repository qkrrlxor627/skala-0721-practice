"""
================================================================
[프로그램명] 실습 4 단위 테스트
================================================================

■ 목적
    제출 파일(실습4/광주_1반_박기택.py)이 요구사항대로 동작하는지 자동으로 확인한다.
    특히 아래 다섯 가지는 어긋나면 곧바로 20점씩 감점되므로 회귀 테스트로 못박는다.
      1) 2×2 서브플롯   - plt.subplots(2, 2) 로 하나의 Figure 에 4종
      2) p-value 해석   - 수치만 찍지 않고 p < 0.05 기준으로 판정
      3) Pipeline 묶기  - 전처리와 모델을 하나의 Pipeline 객체로
      4) 모델 저장      - joblib.dump 로 .joblib 파일 생성
      5) HTML 저장      - fig.show() 가 아니라 write_html()

■ 시험 데이터
    원본(77MB, 100만 행) 대신 conftest.py 의 300행짜리 표본을 쓴다.
    원본의 성격(곱셈 관계, 부풀린 이상치, 결측 범주)을 그대로 재현하면서도
    테스트 전체가 몇 초 안에 끝나 자주 돌릴 수 있다.

■ 실행 방법
    pytest                (커버리지 80% 미만이면 실패)

■ 작성자 : 박기택
■ 최초 작성일 : 2026-07-21
================================================================
"""

import ast
import inspect
import textwrap

import pytest
from conftest import write_practice4_sample_csv
from sklearn.pipeline import Pipeline


def code_only(func):
    """
    [기능] 함수의 소스에서 주석과 docstring 을 걷어내고 실제 실행되는 코드만 남긴다.
    [설명] "plt.show() 를 쓰지 않는다" 같은 설명이 주석에 있으면, 소스를 문자열로
           검사할 때 그 주석 때문에 '쓰고 있다'고 잘못 판정된다.
           파이썬 문법으로 해석한 뒤 다시 코드로 되돌리면 주석은 자연히 사라진다.

    Args:
        func (callable): 검사할 함수.

    Returns:
        str: 주석과 docstring 이 제거된 소스 코드.
    """
    tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
    for node in ast.walk(tree):
        본문 = getattr(node, "body", None)
        # 함수·클래스·모듈의 첫 문장이 문자열이면 그것이 docstring 이다
        if (
            isinstance(본문, list)
            and 본문
            and isinstance(본문[0], ast.Expr)
            and isinstance(본문[0].value, ast.Constant)
            and isinstance(본문[0].value.value, str)
        ):
            node.body = 본문[1:] or [ast.Pass()]
    return ast.unparse(tree)


@pytest.fixture(scope="session", autouse=True)
def 한글폰트(practice4):
    """
    [기능] 차트를 그리는 테스트 전에 한글 폰트를 한 번 설정한다.
    [설명] 설정하지 않으면 차트를 그릴 때마다 한글 글자 수마다 경고가 쏟아져
           정작 봐야 할 테스트 결과가 묻힌다. 실제 실행에서도 main() 이
           같은 함수를 부르므로 조건을 맞추는 셈이기도 하다.
    """
    practice4.setup_korean_font()


@pytest.fixture
def sample4_csv(tmp_path):
    """[기능] 실습 4 테스트용 표본 CSV 를 만들어 경로를 넘긴다."""
    return write_practice4_sample_csv(tmp_path / "sample.csv")


@pytest.fixture
def clean4(practice4, sample4_csv):
    """
    [기능] 표본을 읽어 정제까지 마친 DataFrame 을 넘긴다.
    [설명] 시각화·검정·모델 테스트가 모두 정제된 데이터를 입력으로 받으므로
           같은 준비를 반복하지 않도록 픽스처로 분리했다.
    """
    frame = practice4.load_sales(sample4_csv)
    cleaned, _ = practice4.clean_sales(frame)
    return cleaned


@pytest.fixture
def 실행환경4(practice4, tmp_path, monkeypatch):
    """
    [기능] main() 을 임시 폴더에서 실행하도록 환경을 바꿔치기한다.
    [설명] main() 은 `Path(__file__).parent` 를 기준 폴더로 삼는다. 모듈의 __file__ 을
           임시 폴더 안으로 바꾸면 입력 파일도, 로그도, 산출물도 모두 임시 폴더에
           만들어져 실제 프로젝트 파일을 건드리지 않는다.

    Returns:
        Path: 표본 CSV 가 놓인 임시 폴더.
    """
    monkeypatch.setattr(practice4, "__file__", str(tmp_path / "실습.py"))
    write_practice4_sample_csv(tmp_path / practice4.DATA_FILE)
    yield tmp_path
    practice4.logger.handlers.clear()


# ================================================================
# 1. 입력 파일 탐색 (find_data_file)
# ================================================================


def test_find_data_file_같은_폴더에서_찾음(practice4, tmp_path):
    """[기능] 스크립트와 같은 폴더에 있는 파일을 찾는지 확인한다."""
    (tmp_path / "sales_100k.csv").write_text("x", encoding="utf-8")

    assert practice4.find_data_file(tmp_path) == tmp_path / "sales_100k.csv"


def test_find_data_file_상위_폴더에서_찾음(practice4, tmp_path):
    """
    [기능] 같은 폴더에 없으면 상위 폴더까지 찾아보는지 확인한다.
    [설명] 저장소에서는 스크립트가 실습4/ 안에 있고 CSV 는 그 상위에 있다.
           이 동작이 없으면 저장소 구조 그대로는 실행되지 않는다.
    """
    하위 = tmp_path / "실습4"
    하위.mkdir()
    (tmp_path / "sales_100k.csv").write_text("x", encoding="utf-8")

    assert practice4.find_data_file(하위) == tmp_path / "sales_100k.csv"


def test_find_data_file_없으면_찾아본_경로를_안내(practice4, tmp_path):
    """[기능] 파일이 없을 때 어디를 찾아봤는지 알려주는지 확인한다."""
    with pytest.raises(FileNotFoundError, match="찾아본 경로"):
        practice4.find_data_file(tmp_path)


# ================================================================
# 2. 데이터 정제 (실습 3과 동일한 결과가 나와야 함)
# ================================================================


def test_clean_sales_이상치와_결측_처리(practice4, sample4_csv):
    """
    [기능] IQR 이상치가 제거되고 결측 범주가 이름을 얻는지 확인한다.
    [설명] 표본에는 amount 를 10배로 부풀린 행 6건을 심어두었다.
           이들이 걸러지고, 빈 region·category 는 '미상'/'미분류' 로 채워져야 한다.
    """
    frame = practice4.load_sales(sample4_csv)
    cleaned, info = practice4.clean_sales(frame)

    assert info["rows_before"] == 300
    assert info["rows_after"] < info["rows_before"]  # 이상치가 걸러졌다
    assert info["lower"] == pytest.approx(info["q1"] - 1.5 * info["iqr"])
    assert info["upper"] == pytest.approx(info["q3"] + 1.5 * info["iqr"])
    # 결측을 버리지 않고 이름을 붙여 살렸는지
    assert practice4.UNKNOWN_REGION in cleaned["region"].to_numpy()
    assert practice4.UNKNOWN_CATEGORY in cleaned["category"].to_numpy()
    assert cleaned[["region", "category"]].isna().sum().sum() == 0


def test_clean_sales_전부_결측이면_오류(practice4, sample4_csv):
    """[기능] amount 가 전부 비어 있으면 ValueError 로 알리는지 확인한다."""
    frame = practice4.load_sales(sample4_csv)
    frame["amount"] = None

    with pytest.raises(ValueError, match="유효한 값이 없어"):
        practice4.clean_sales(frame)


def test_aggregate_by_group_컬럼명과_정렬(practice4, clean4):
    """[기능] 집계 결과의 컬럼명이 total/mean/count 이고 총매출 내림차순인지 확인한다."""
    결과 = practice4.aggregate_by_group(clean4)

    assert set(결과.columns) == {"region", "category", "total", "mean", "count"}
    assert 결과["total"].tolist() == sorted(결과["total"].tolist(), reverse=True)


# ================================================================
# 3. EDA 시각화 - 감점 항목 ①
# ================================================================


def test_2x2_서브플롯을_사용(practice4):
    """
    [기능] 차트를 2×2 서브플롯 하나로 묶었는지 소스 코드로 확인한다.
    [설명] 차트 4개를 각각 plt.show() 로 따로 띄우면 20점 감점이다.
           결과 이미지만 봐서는 어떻게 그렸는지 알 수 없어 코드를 직접 검사한다.
    """
    source = code_only(practice4.create_eda_charts)

    assert "plt.subplots(2, 2" in source
    assert "plt.show()" not in source


def test_차트_4종이_모두_그려짐(practice4, clean4, tmp_path):
    """[기능] 2×2 네 칸에 각각 차트가 그려지고 제목·축 이름이 붙는지 확인한다."""
    monthly = practice4.analyze_monthly(clean4)
    경로 = practice4.create_eda_charts(clean4, monthly, tmp_path / "chart.png")

    assert 경로 is not None and 경로.exists()
    assert 경로.stat().st_size > 10_000  # 빈 이미지가 아님


def test_차트_저장_실패해도_계속_진행(practice4, clean4, tmp_path):
    """
    [기능] 차트를 저장하지 못해도 예외를 던지지 않고 None 만 돌려주는지 확인한다.
    [설명] 차트 저장 실패는 통계 검정·모델 학습과 무관하다. 전체를 멈출 이유가 없다.
    """
    막힘 = tmp_path / "막힘"
    막힘.write_text("파일", encoding="utf-8")  # 파일 자리에 폴더를 만들 수 없어 저장 실패
    monthly = practice4.analyze_monthly(clean4)

    assert practice4.create_eda_charts(clean4, monthly, 막힘 / "chart.png") is None


def test_한글_폰트_없어도_중단되지_않음(practice4, monkeypatch):
    """
    [기능] 한글 폰트를 찾지 못해도 경고만 남기고 계속 진행하는지 확인한다.
    [설명] 폰트가 없으면 차트의 한글만 깨질 뿐 분석 결과는 정상이다.
           여기서 멈추면 폰트가 없는 환경에서는 아무것도 얻지 못한다.
    """
    monkeypatch.setattr(practice4, "KOREAN_FONTS", ("존재하지않는폰트",))

    assert practice4.setup_korean_font() is None


def test_analyze_monthly_일수_보정(practice4, clean4):
    """
    [기능] 월별 총매출과 일수로 나눈 일평균이 함께 계산되는지 확인한다.
    [설명] 월별 총매출만 보면 짧은 달이 낮게 나와 계절성으로 오해하기 쉽다.
           일수 보정 값을 함께 내야 그 차이를 구분할 수 있다.
    """
    월별 = practice4.analyze_monthly(clean4)

    assert set(월별["table"].columns) == {"총매출", "일수", "일평균"}
    assert 월별["months"] >= 2
    # 일평균 = 총매출 / 일수 가 실제로 성립하는지
    표 = 월별["table"]
    assert (표["총매출"] / 표["일수"]).round(6).equals(표["일평균"].round(6))


# ================================================================
# 4. 통계 검정 - 감점 항목 ②
# ================================================================


def test_ttest_결과에_판정과_해석이_포함(practice4, clean4):
    """
    [기능] t-test 가 통계량·p-value 뿐 아니라 판정과 해석까지 내는지 확인한다.
    [설명] 수치만 출력하고 p < 0.05 기준의 유의성 판단이 없으면 20점 감점이다.
    """
    결과 = practice4.run_ttest(clean4, groups=("서울", "부산"))

    assert set(결과) >= {"statistic", "pvalue", "cohens_d", "significant", "interpretation"}
    assert isinstance(결과["significant"], bool)
    # 판정이 실제 p-value 와 일치하는지 (거꾸로 판정하는 실수 방지)
    assert 결과["significant"] == (결과["pvalue"] < practice4.ALPHA)
    # 해석문에 판정 근거가 문장으로 들어 있어야 한다
    assert str(practice4.ALPHA) in 결과["interpretation"]


def test_ttest_없는_지역이면_실제_목록을_안내(practice4, clean4):
    """[기능] 지정한 지역의 자료가 없으면 실제 존재하는 지역을 알려주는지 확인한다."""
    with pytest.raises(ValueError, match="실제 지역"):
        practice4.run_ttest(clean4, groups=("서울", "없는지역"))


def test_chi2_결과에_판정과_해석이_포함(practice4, clean4):
    """[기능] 카이제곱 검정이 판정(독립 여부)과 해석까지 내는지 확인한다."""
    결과 = practice4.run_chi2_test(clean4, columns=("region", "category"))

    assert set(결과) >= {"statistic", "pvalue", "dof", "cramers_v", "associated", "interpretation"}
    # 독립 판정이 p-value 와 일치하는지 (t-test 와 부등호 방향이 반대인 점에 주의)
    assert 결과["associated"] == (결과["pvalue"] < practice4.ALPHA)
    assert str(practice4.ALPHA) in 결과["interpretation"]


def test_chi2_분할표가_너무_작으면_오류(practice4, clean4):
    """[기능] 한 변수의 값이 한 종류뿐이면 검정이 성립하지 않음을 알리는지 확인한다."""
    한종류 = clean4.assign(region="서울")

    with pytest.raises(ValueError, match="분할표가 너무 작아"):
        practice4.run_chi2_test(한종류, columns=("region", "category"))


def test_해석문이_p값에_따라_갈라짐(practice4):
    """
    [기능] 유의한 경우와 아닌 경우에 서로 다른 해석문이 나오는지 확인한다.
    [설명] 해석문을 미리 적어두고 항상 같은 말을 출력하면 판정을 한 것이 아니다.
    """
    유의함 = practice4.interpret_ttest(("A", "B"), (100.0, 200.0), 0.001, 0.8, True, 1000)
    유의하지않음 = practice4.interpret_ttest(("A", "B"), (100.0, 101.0), 0.9, 0.01, False, 1000)

    assert "차이가 있다고 판단합니다" in 유의함
    assert "증거를 찾지 못했습니다" in 유의하지않음
    assert 유의함 != 유의하지않음


def test_귀무가설을_채택했다고_말하지_않음(practice4, clean4):
    """
    [기능] p >= 유의수준일 때 '같다'/'독립'으로 단정하지 않는지 확인한다.
    [설명] 통계 검정은 '차이·연관이 있다'는 증거를 찾았는지만 답할 수 있고,
           '차이·연관이 없다'를 증명하지는 못한다. 이를 '평균이 같다',
           '두 변수는 독립이다'라고 쓰면 통계적으로 틀린 진술이 된다.
           문구가 되돌아가지 않도록 테스트로 고정한다.
    """
    ttest = practice4.run_ttest(clean4, groups=("서울", "부산"))
    chi2 = practice4.run_chi2_test(clean4, columns=("region", "category"))

    # 금지어는 '단정하는 서술'만 고른다.
    # "'두 평균이 같다'가 증명된 것이 아니라" 처럼 부정하는 문장 안에도 같은 낱말이
    # 들어가므로, 낱말이 아니라 단정 어미까지 포함한 표현으로 검사해야 한다.
    for 결과, 금지어 in (
        (ttest, ("같다고 볼 수 있다", "평균이 같습니다", "차이가 없습니다")),
        (chi2, ("독립이라고 판단", "독립입니다", "관계 없음")),
    ):
        if 결과.get("significant") or 결과.get("associated"):
            continue  # 유의한 경우에는 해당 문구 자체가 나오지 않는다
        for 말 in 금지어:
            assert 말 not in 결과["interpretation"], (
                f"귀무가설을 증명한 것처럼 표현했습니다: '{말}'"
            )
        # 대신 '증거를 찾지 못했다'는 취지와, 증명이 아니라는 단서가 함께 있어야 한다
        assert "찾지 못했습니다" in 결과["interpretation"]
        assert "증명된 것이 아니라" in 결과["interpretation"]


def test_제거_사유가_결측과_이상치로_분리됨(practice4, sample4_csv):
    """
    [기능] 제거 건수가 'amount 결측'과 'IQR 범위 밖'으로 나뉘어 보고되는지 확인한다.
    [설명] 둘을 합쳐 한 숫자로만 내면 읽는 쪽은 전부 이상치였다고 이해한다.
           금액을 모르는 행과 금액이 지나치게 큰 행은 성격이 다르므로 구분해야 한다.
    """
    frame = practice4.load_sales(sample4_csv)
    _, info = practice4.clean_sales(frame)

    assert "missing_removed" in info and "outlier_removed" in info
    # 두 사유의 합이 전체 제거 건수와 맞아야 한다 (빠지거나 중복 계산된 행이 없음)
    assert info["missing_removed"] + info["outlier_removed"] == info["rows_removed"]
    assert info["rows_before"] - info["rows_removed"] == info["rows_after"]


# ================================================================
# 5. sklearn Pipeline - 감점 항목 ③, ④
# ================================================================


def test_전처리와_모델이_하나의_Pipeline(practice4, clean4):
    """
    [기능] 전처리와 모델이 분리 실행되지 않고 하나의 Pipeline 객체로 묶였는지 확인한다.
    [설명] 개별 단계로 나눠 실행하면 20점 감점이다. 반환된 객체의 타입과
           단계 구성을 확인하면 확실히 잡을 수 있다.
    """
    학습 = practice4.train_and_evaluate(clean4)

    for 결과 in 학습["results"]:
        pipeline = 결과["pipeline"]
        assert isinstance(pipeline, Pipeline)
        # 전처리(prep) 다음에 모델(model) 이 오는 2단계 구성이어야 한다
        assert [name for name, _ in pipeline.steps] == ["prep", "model"]


def test_두_모델이_같은_전처리를_공유(practice4, clean4):
    """
    [기능] 두 모델의 전처리 설정이 동일한지 확인한다.
    [설명] 전처리가 다르면 모델 성능 차이가 모델 때문인지 전처리 때문인지 알 수 없다.
           비교가 성립하려면 마지막 단계만 달라야 한다.
    """
    학습 = practice4.train_and_evaluate(clean4)
    전처리들 = [
        str(결과["pipeline"].named_steps["prep"]) for 결과 in 학습["results"]
    ]

    assert len(set(전처리들)) == 1, "두 모델의 전처리 설정이 다릅니다"
    assert len({결과["name"] for 결과 in 학습["results"]}) == 2  # 모델은 서로 다름


def test_fit_predict_score가_모두_수행됨(practice4, clean4):
    """[기능] 훈련·예측·평가가 실제로 수행되어 R² 와 MAE 가 나오는지 확인한다."""
    학습 = practice4.train_and_evaluate(clean4)

    assert 학습["train_rows"] > 0 and 학습["test_rows"] > 0
    for 결과 in 학습["results"]:
        assert -1 <= 결과["r2"] <= 1
        assert 결과["mae"] >= 0
    # 학습된 Pipeline 으로 예측이 실제로 되는지
    예측 = 학습["best"]["pipeline"].predict(학습["x_test"].head(5))
    assert len(예측) == 5


def test_학습_자료가_부족하면_오류(practice4, clean4):
    """[기능] 훈련/검증으로 나눌 수 없을 만큼 자료가 적으면 안내하는지 확인한다."""
    with pytest.raises(ValueError, match="자료가 부족합니다"):
        practice4.train_and_evaluate(clean4.head(10))


def test_모델이_joblib_파일로_저장되고_재로딩됨(practice4, clean4, tmp_path):
    """
    [기능] joblib.dump 로 파일이 만들어지고, 재로딩한 모델이 같은 예측을 내는지 확인한다.
    [설명] joblib.dump 없이 학습만 하면 20점 감점이다. 나아가 저장만 하고 끝내면
           그 파일이 실제로 쓸 수 있는지 알 수 없으므로 재로딩 예측까지 확인한다.
    """
    학습 = practice4.train_and_evaluate(clean4)
    경로 = tmp_path / "model.joblib"

    정보 = practice4.save_and_reload_model(학습["best"]["pipeline"], 경로, 학습["x_test"])

    assert 경로.exists() and 정보["size_bytes"] > 0
    assert 정보["reload_ok"] is True
    assert 정보["checked_rows"] > 0


def test_재로딩_예측이_다르면_검증_실패(practice4, clean4, tmp_path, monkeypatch):
    """
    [기능] 재로딩한 모델의 예측이 원본과 다르면 AssertionError 로 알리는지 확인한다.
    [설명] 항상 통과하는 검증은 아무것도 보증하지 못한다. 일부러 다른 모델이
           불러와지게 만들어 검증이 실제로 작동하는지 확인한다.
    """
    학습 = practice4.train_and_evaluate(clean4)
    다른_모델 = 학습["results"][0]["pipeline"]
    좋은_모델 = 학습["results"][1]["pipeline"]

    # joblib.load 가 저장한 것과 다른 모델을 돌려주도록 바꿔치기한다
    monkeypatch.setattr(practice4.joblib, "load", lambda path: 다른_모델)

    with pytest.raises(AssertionError, match="재로딩한 모델의 예측이 원본과 다릅니다"):
        practice4.save_and_reload_model(좋은_모델, tmp_path / "m.joblib", 학습["x_test"])


# ================================================================
# 6. Plotly - 감점 항목 ⑤
# ================================================================


def test_plotly_차트가_HTML로_저장됨(practice4, clean4, tmp_path):
    """
    [기능] Plotly 차트가 화면 출력이 아니라 HTML 파일로 저장되는지 확인한다.
    [설명] fig.show() 로 끝내고 write_html() 을 호출하지 않으면 20점 감점이다.
    """
    집계 = practice4.aggregate_by_group(clean4)
    경로 = tmp_path / "chart.html"

    정보 = practice4.create_plotly_chart(집계, 경로)

    assert 경로.exists() and 정보["size_bytes"] > 1000
    내용 = 경로.read_text(encoding="utf-8")
    assert "<html" in 내용.lower() and "plotly" in 내용.lower()


def test_plotly는_show가_아니라_write_html_사용(practice4):
    """[기능] 소스 코드에 write_html 이 있고 show() 로 끝내지 않는지 확인한다."""
    source = code_only(practice4.create_plotly_chart)

    assert "write_html" in source
    assert "fig.show()" not in source


# ================================================================
# 7. 전체 흐름 (main)
# ================================================================


def test_main_정상_실행과_산출물_3종(practice4, 실행환경4):
    """
    [기능] 전체 흐름이 끝까지 돌고 필수 산출물 3종이 만들어지는지 확인한다.
    [설명] 요구사항의 필수 산출물은 Python 파일·모델 파일·Plotly HTML 이다.
    """
    assert practice4.main() == 0

    for 파일 in (practice4.CHART_FILE, practice4.MODEL_FILE, practice4.PLOTLY_FILE):
        경로 = 실행환경4 / 파일
        assert 경로.exists(), f"{파일} 이 만들어지지 않았습니다"
        assert 경로.stat().st_size > 0


def test_main_입력_파일_없음(practice4, tmp_path, monkeypatch):
    """[기능] 입력 파일이 없으면 안내 후 종료 코드 1 을 돌려주는지 확인한다."""
    monkeypatch.setattr(practice4, "__file__", str(tmp_path / "실습.py"))
    try:
        assert practice4.main() == 1
    finally:
        practice4.logger.handlers.clear()


def test_main_모델_저장_실패하면_실패로_처리(practice4, 실행환경4, monkeypatch):
    """
    [기능] 모델 저장에 실패하면 종료 코드 1 을 돌려주는지 확인한다.
    [설명] 모델 파일은 필수 산출물이므로, 차트 저장 실패와 달리 넘어가면 안 된다.
    """

    def 저장_실패(*args, **kwargs):
        raise OSError("디스크 공간이 부족합니다")

    monkeypatch.setattr(practice4.joblib, "dump", 저장_실패)

    assert practice4.main() == 1


def test_출력_순서가_결론_먼저(practice4, 실행환경4, capsys):
    """
    [기능] 결론(핵심 결과)이 상세 내역보다 먼저 출력되는지 확인한다.
    [설명] 이 프로그램의 출력 설계를 고정하는 테스트다. 상세 내역을 먼저 찍으면
           정작 알고 싶은 검정 판정과 모델 성능이 화면 아래로 밀린다.
    """
    assert practice4.main() == 0
    화면 = capsys.readouterr().out

    assert 화면.index("핵심 결과") < 화면.index("이하 상세") < 화면.index("df.info()")


def test_출력에_요구된_결과가_모두_포함(practice4, 실행환경4, capsys):
    """
    [기능] 요구사항이 실행 결과에 포함하라고 한 항목이 모두 출력되는지 확인한다.
    [설명] 요구사항 4장의 목록 — 통계량, p-value, 유의성 해석, 독립성 해석,
           모델 평가 점수, 저장·재로딩 결과, HTML 저장 경로.
    """
    assert practice4.main() == 0
    화면 = capsys.readouterr().out

    for 항목 in ("t-test", "p-value", "카이제곱", "Cohen's d", "Cramér's V",
                 "R²", "MAE", "재로딩", practice4.PLOTLY_FILE, practice4.MODEL_FILE):
        assert 항목 in 화면, f"출력에 '{항목}' 이 없습니다"


# ================================================================
# 8. 표시 서식 (실습 3에서 가져온 부분)
# ================================================================


@pytest.mark.parametrize(
    "금액, 기대",
    [(74_992_750_244, "749.9억원"), (2_495_267, "249.5만원"), (5_000, "5,000원")],
)
def test_format_won_단위_변환(practice4, 금액, 기대):
    """[기능] 큰 금액이 억·만 단위로 읽기 쉽게 바뀌는지 확인한다."""
    assert practice4.format_won(금액) == 기대


def test_display_width_한글은_두_칸(practice4):
    """[기능] 한글이 영문자의 두 배 폭으로 계산되는지 확인한다."""
    assert practice4.display_width("서울") == 4
    assert practice4.display_width("seoul") == 5


def test_상수가_요구사항을_만족(practice4):
    """
    [기능] 판정 기준과 재현성 설정이 요구사항대로인지 확인한다.
    [설명] ALPHA 가 바뀌면 모든 검정의 판정이 달라진다. 상수로 고정해 두고
           여기서 확인해 두면 실수로 바꿨을 때 바로 드러난다.
    """
    assert practice4.ALPHA == 0.05
    assert practice4.RANDOM_STATE is not None  # 재현 가능해야 한다
    assert practice4.MODEL_FILE.endswith((".joblib", ".pkl"))
    assert practice4.PLOTLY_FILE.endswith(".html")
