# 분석 데이터

Microsoft AdventureWorks OLTP는 가상 자전거 회사의 주문 및 상품 정보를 담은 교육용 데이터베이스다. 이 프로젝트는 온라인 주문 고객의 재구매와 구매액을 분석한다. 금액은 원본 판매액 단위로 보고하며, 실제 시장에 일반화하려면 별도의 검증이 필요하다. [공식 데이터 설명](https://github.com/microsoft/sql-server-samples/tree/master/samples/databases/adventure-works) · [사용한 원본 ZIP](https://github.com/Microsoft/sql-server-samples/releases/download/adventureworks/AdventureWorks-oltp-install-script.zip) · [Microsoft MIT 라이선스](data-license.txt)

## 표본과 결합 기준

1. `SalesOrderHeader.OnlineOrderFlag = 1`인 주문을 모두 선택했다. 대상 기간은 2022-05-30부터 2025-06-29까지다. 고객 18,484명이 주문 27,659건을 생성했다.
2. 주문번호로 `SalesOrderDetail`을 연결했다. CSV 한 행은 주문 한 건의 상품 항목이다. 같은 주문번호가 여러 번 나타날 수 있다. CSV에는 60,398행, 11열이 있다.
3. 상품 ID로 `Product`의 이름을 연결하고 소분류 ID → `ProductSubcategory` → `ProductCategory`를 따라 대분류를 가져왔다. 액세서리 36,092행, 자전거 15,205행, 의류 9,101행이다.
4. `ProductProductPhoto`로 연결된 `ProductPhoto.LargePhoto`를 원본 GIF로 복원했다. ‘사진 없음’ 대체 그림은 제외했다. 온라인에서 구매된 상품 130종 중 95종에 고유 사진 22장이 연결되며, 나머지 35종은 상품 사진이 없다. 여러 상품이 같은 사진을 공유한다. 사진이 있는 거래는 31,966행, 사진이 없는 거래는 28,432행이다. RFM에는 모든 거래를 포함한다.

## 입력 열

| 열 | 의미 |
| --- | --- |
| `customer_id`, `order_id` | 고객과 주문 식별자. 구매 빈도는 고객별 고유 주문 수 |
| `order_date` | 주문일. 가입일은 제공되지 않음 |
| `product_id`, `product_name`, `product_category` | 상품 식별자, 원본 상품명, 원본 상품 대분류 |
| `quantity`, `unit_price`, `discount_rate` | 주문 항목의 수량, 단가, 할인율. 이 온라인 표본에서는 수량 1, 할인율 0 |
| `line_amount` | 할인 적용 후 상품 금액. 세금·배송비 제외. 전체 합계 29,358,677.2207 |
| `image_path` | `data/` 기준 GIF 상대 경로. 원본 상품 사진이 없으면 빈 값 |

과제 입력은 `data/transactions.csv`와 `data/images/`에 압축 해제한 상태로 보관한다. 원본 위치와 추출 범위는 [데이터 출처 메모](../data/source.txt)에서도 확인할 수 있다.
