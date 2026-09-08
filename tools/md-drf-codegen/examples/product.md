# 製品 API 仕様書

## API一覧

| API ID | API名 | メソッド | パス | リクエスト型 | レスポンス型 |
| --- | --- | --- | --- | --- | --- |
| listProducts | 製品一覧取得 | GET | /api/products | ProductListRequest | ProductListResponse |
| getProduct | 製品詳細取得 | GET | /api/products/{productId} | ProductDetailQuery | ProductDetailResponse |
| updateProduct | 製品更新 | PUT | /api/products/{productId} | ProductUpdateRequest | ProductDetailResponse |

## パスパラメータ

| パラメータ名 | 型 | 制約 | エラーメッセージ |
| --- | --- | --- | --- |
| productId | string | 半角英数字, 最大20文字 | pattern:製品IDの形式が正しくありません; max_length:製品IDは20文字以内で入力してください |

## 型定義

| 型名 | プロパティ | 型 | 必須 | Nullable | 制約 | エラーメッセージ |
| --- | --- | --- | --- | --- | --- | --- |
| ProductListRequest | keyword | string | false | false | 最大50文字 | - |
| ProductListRequest | page | integer | false | false | 1-100 | - |
| ProductListResponse | items | ProductSummary[] | true | false | - | - |
| ProductSummary | productId | string | true | false | 半角英数字, 最大20文字 | - |
| ProductSummary | productName | string | true | false | 最大50文字 | - |
| ProductDetailQuery | includeDeleted | boolean | false | false | - | - |
| ProductDetailResponse | productId | string | true | false | 半角英数字, 最大20文字 | - |
| ProductDetailResponse | productName | string | true | false | 最大50文字 | - |
| ProductDetailResponse | description | string | false | true | 最大200文字 | - |
| ProductDetailResponse | price | number | true | false | 1-999999 | - |
| ProductDetailResponse | revision | integer | true | false | 1-50 | - |
| ProductUpdateRequest | productName | string | true | false | 最大50文字 | required:製品名は必須です; max_length:製品名は50文字以内で入力してください |
| ProductUpdateRequest | price | number | true | false | 1-999999 | - |
| ProductUpdateRequest | revision | integer | true | false | 1-50 | - |
