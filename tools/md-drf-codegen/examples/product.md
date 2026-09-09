# 製品 API 仕様書

## API一覧

| API ID | API名 | メソッド | パス | リクエスト型 | レスポンス型 | 備考 |
| --- | --- | --- | --- | --- | --- | --- |
| listProducts | 製品一覧取得 | GET | /api/products | ProductListRequest | ProductListResponse | キーワード検索・ページング |
| getProduct | 製品詳細取得 | GET | /api/products/{productId} | ProductDetailQuery | ProductDetailResponse | - |
| updateProduct | 製品更新 | PUT | /api/products/{productId} | ProductUpdateRequest | ProductDetailResponse | 楽観ロック（revision） |

## パスパラメータ

| パラメータ名 | 型 | 制約 | エラーメッセージ | 備考 |
| --- | --- | --- | --- | --- |
| productId | string | 半角英数字, 最大20文字 | pattern:製品IDの形式が正しくありません; max_length:製品IDは20文字以内で入力してください | URL 上の製品 ID |

## 定数定義一覧

| ファイルパス | クラス名 | 備考 |
| --- | --- | --- |
| common/util/Consts.py | Status | 製品ステータス（1:Low / 2:Middle / 3:High）。既存プロジェクトの Choices を参照 |

## 型定義

| 型名 | プロパティ | 型 | 必須 | Nullable | 制約 | エラーメッセージ | 備考 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ProductListRequest | keyword | string | false | false | 最大50文字 | - | 部分一致検索 |
| ProductListRequest | page | integer | false | false | 1-100 | - | - |
| ProductListResponse | items | ProductSummary[] | true | false | - | - | - |
| ProductSummary | productId | string | true | false | 半角英数字, 最大20文字 | - | - |
| ProductSummary | productName | string | true | false | 最大50文字 | - | - |
| ProductDetailQuery | includeDeleted | boolean | false | false | - | - | 論理削除済みも含める場合 true |
| ProductDetailResponse | productId | string | true | false | 半角英数字, 最大20文字 | - | - |
| ProductDetailResponse | productName | string | true | false | 最大50文字 | - | - |
| ProductDetailResponse | description | string | false | true | 最大200文字 | - | - |
| ProductDetailResponse | price | number | true | false | 1-999999 | - | - |
| ProductDetailResponse | revision | integer | true | false | 1-50 | - | 楽観ロック用 |
| ProductDetailResponse | status | integer | true | false | enum:1:Low、2:Middle、3:High | - | Status Enum 参照 |
| ProductDetailResponse | updatedDate | date | true | false | - | - | 最終更新日 |
| ProductUpdateRequest | productName | string | true | false | 最大50文字 | required:製品名は必須です; max_length:製品名は50文字以内で入力してください | - |
| ProductUpdateRequest | price | number | true | false | 1-999999 | - | - |
| ProductUpdateRequest | revision | integer | true | false | 1-50 | - | 楽観ロック用 |
| ProductUpdateRequest | status | integer | true | false | enum:1:Low、2:Middle、3:High | invalid_choice:ステータスの値が正しくありません | Status Enum 参照 |
