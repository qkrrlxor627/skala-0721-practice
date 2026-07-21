# [실습 3] Pandas EDA · Polars Lazy · DuckDB SQL 비교하는 것이 핵심
결과를 깔끔하게 내자. 

## 실습 파일

`sales_100k.csv`

---

## 1) Pandas EDA - 기초 탐색 + 이상치 처리

- `sales_100k.csv`를 로딩하고 기본 EDA를 수행한 뒤 IQR 방법으로 이상치를 제거
- `between(Q1-1.5*IQR, Q3+1.5*IQR)`은 IQR 기준 정상 범위를 의미합니다.

## 2) Pandas groupby - named aggregation

- `region·category`별 총매출·평균·건수를 named aggregation으로 계산하고 총매출 내림차순으로 정렬
- named aggregation: `total=('amount','sum')` 형태로 결과 컬럼명을 직접 지정

## 3) Polars Lazy API로 동일 집계 작성

- 2번 실습과 동일한 집계를 Polars Lazy API로 작성
- `scan_csv → filter → group_by → agg → sort → collect`

## 4) DuckDB SQL + 세 도구 성능 비교

- DuckDB로 동일 집계를 SQL로 작성하고, `timeit`으로 세 도구의 실행 시간을 비교

---

# Checkpoint

- `df.info()`, `isnull().sum()` 출력 후 IQR 방법으로 이상치 제거, 제거 전·후 행 수 출력
- `region·category`별 `total·mean·count`를 named aggregation으로 계산, 총매출 내림차순 정렬
- `scan_csv → filter → group_by → agg → sort → collect` 체인 완성 및 결과 출력
- 동일 집계를 SQL `GROUP BY`로 작성, 결과를 DataFrame으로 출력
- `timeit` 3번 이상으로 세 도구 실행 시간 측정, 동일 반복 횟수로 결과 출력

---

# 감점 대상(감점 점수)

## IQR 공식 오류: -20점

- `Q1 - 1.5*IQR / Q3 + 1.5*IQR` 범위를 잘못 적용한 경우

## named aggregation 미사용: -20점

- `agg({'amount': 'sum'})` 방식으로 결과 컬럼명이 지정되지 않은 경우

## Polars Eager 사용: -20점

- `scan_csv` 대신 `read_csv`를 사용하여 Lazy API를 적용하지 않은 경우

## `collect()` 누락: -20점

- Polars 체인 끝에 `collect()` 없이 LazyFrame 상태로 제출한 경우

## `timeit` 반복 횟수 미통일: -20점

- 세 도구의 `number` 값이 달라 공정한 비교가 불가능한 경우

---

# 평가 기준

> `캠퍼스명_반_이름.py`로 제출 / Practice Rule (총점 100점)

## 이해관계자들의 이해를 위한 주석 필요

## 핵심적인 부분에서 다음 사항 점검이 필요함.
예외 처리	
프로그램·함수 설명	
코드 간결성	필수	
로깅	
pytest	
커버리지 80%	
timeit 동일 반복 횟수 필수

## Code의 Comm. (20점)

- Python Code를 통한 이해관계자와의 Communication
- 프로그램 전체 설명 및 변경 내역(머리말)
- 함수·기능 설명(중간)

## 코드 간결성 (35점)

- 불필요한 반복 지양

## 오류·예외 처리 (35점)

- 예외·오류에 대한 코드 반영 여부
- 간단한 코드라도 오류·예외 처리 연습 목적