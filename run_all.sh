#!/bin/bash
# ================================================================
# [스크립트명] 실습 3·4 전체 실행
# ================================================================
#
# 목적 : 테스트 → 실습 3 → 실습 4 를 한 번에 돌리고 산출물을 확인한다.
#        여러 줄 명령을 터미널에 붙여넣으면 따옴표가 잘려 셸이 멈추는 일이 잦아,
#        파일로 만들어 한 줄로 실행할 수 있게 했다.
#
# 사용법 : bash run_all.sh          (전체 실행)
#          bash run_all.sh open     (전체 실행 후 차트·보고서까지 열기)
#
# 작성자 : 박기택
# ================================================================

# 이 스크립트가 있는 폴더로 이동한다.
# 어느 위치에서 실행하든 항상 프로젝트 폴더를 기준으로 삼기 위해서다.
cd "$(dirname "$0")" || exit 1

# 가상환경의 파이썬을 직접 지정한다.
# activate 를 거치지 않으므로, 가상환경을 켜뒀는지 여부와 무관하게 동작한다.
PYTHON=".venv/bin/python"

if [ ! -x "$PYTHON" ]; then
    echo "[오류] 가상환경을 찾을 수 없습니다: $PYTHON"
    echo "       아래 명령으로 먼저 만들어 주세요."
    echo "       python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi

if [ ! -f "sales_100k.csv" ]; then
    echo "[오류] 입력 파일이 없습니다: sales_100k.csv"
    echo "       실습 자료에서 내려받아 이 폴더에 두고 다시 실행해 주세요."
    exit 1
fi

# 어느 단계에서 실패했는지 마지막에 알려주려고 기록해 둔다
FAILED=""

echo ""
echo "=============== 1) 테스트 + 커버리지 ==============="
"$PYTHON" -m pytest -q || FAILED="$FAILED 테스트"

echo ""
echo "=============== 2) 실습 3 실행 ==============="
"$PYTHON" 광주_1반_박기택.py | tee 실행결과.txt
# tee 를 거치면 $? 는 tee 의 결과가 되므로, 파이썬의 종료 코드를 따로 꺼낸다
[ "${PIPESTATUS[0]}" -eq 0 ] || FAILED="$FAILED 실습3"

echo ""
echo "=============== 3) 실습 4 실행 ==============="
"$PYTHON" 실습4/광주_1반_박기택.py | tee 실습4/실행결과.txt
[ "${PIPESTATUS[0]}" -eq 0 ] || FAILED="$FAILED 실습4"

echo ""
echo "=============== 4) 산출물 확인 ==============="
for f in \
    "Docs/result.md" \
    "실습4/eda_2x2.png" \
    "실습4/sales_model.joblib" \
    "실습4/sales_by_region_category.html"
do
    if [ -f "$f" ]; then
        SIZE=$(du -h "$f" | cut -f1)
        echo "  있음   $f  ($SIZE)"
    else
        echo "  없음   $f   <-- 만들어지지 않았습니다"
        FAILED="$FAILED 산출물"
    fi
done

echo ""
if [ -n "$FAILED" ]; then
    echo "=============== 실패한 단계:$FAILED ==============="
    echo "위 출력에서 [오류] 로 시작하는 줄을 확인해 주세요."
    exit 1
fi

echo "=============== 전체 정상 완료 ==============="

# 'open' 을 인자로 준 경우에만 파일을 연다.
# 항상 열면 창이 여러 개 떠서, 결과만 보려는 경우에 방해가 된다.
if [ "$1" = "open" ]; then
    echo ""
    echo "차트와 보고서를 엽니다..."
    open 실습4/eda_2x2.png
    open 실습4/sales_by_region_category.html
    open Docs/result.md
else
    echo ""
    echo "결과를 보려면:"
    echo "  open 실습4/eda_2x2.png                      # 2x2 차트 4종"
    echo "  open 실습4/sales_by_region_category.html    # Plotly 차트"
    echo "  open Docs/result.md                         # 실습 3 보고서"
    echo ""
    echo "또는 다음에 이렇게 실행하면 자동으로 열립니다:  bash run_all.sh open"
fi
