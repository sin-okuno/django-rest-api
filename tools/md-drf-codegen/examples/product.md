# 製品 API 仕様書

## API一覧

| API ID | API名 | メソッド | パス | リクエスト型 | レスポンス型 |
| --- | --- | --- | --- | --- | --- |
| listProducts | 製品一覧取得 | GET | /api/products | - | ProductListResponse |
| getProduct | 製品詳細取得 | GET | /api/products/{productId} | - | ProductDetailResponse |
| updateProduct | 製品更新 | PUT | /api/products/{productId} | ProductUpdateRequest | ProductDetailResponse |

## 型定義

| 型名 | プロパティ | 型 | 必須 | Nullable |
| --- | --- | --- | --- | --- |
| ProductListResponse | items | ProductSummary[] | true | false |
| ProductSummary | productId | string | true | false |
| ProductSummary | productName | string | true | false |
| ProductDetailResponse | productId | string | true | false |
| ProductDetailResponse | productName | string | true | false |
| ProductDetailResponse | description | string | false | true |
| ProductDetailResponse | price | number | true | false |
| ProductDetailResponse | revision | integer | true | false |
| ProductUpdateRequest | productName | string | true | false |
| ProductUpdateRequest | price | number | true | false |
| ProductUpdateRequest | revision | integer | true | false |
