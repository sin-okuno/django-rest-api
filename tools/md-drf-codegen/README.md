# md-drf-codegen

Markdown 仕様書から YAML を生成し、その YAML から Django REST Framework の定型コードを生成する CLI ツールです。

**目的:** API 開発の定型作業（Serializer / View 骨格 / URL / 基本テスト）を削減し、開発者が Selector / Service / 業務ロジックに集中できるようにする。

**重要:** 生成処理に AI は使用しません。Parser / Pydantic / Jinja2 による決定論的な変換のみです。

## 対象範囲

- Markdown → YAML
- YAML → Serializer
- YAML → View 骨格（`NotImplementedError`）
- YAML → URL
- YAML → 基本テスト（Serializer / URL / View）

## 対象外

- Model / Migration
- Service / Selector の業務処理
- ORM / Permission / 認可 / 認証
- ProductAccess 等の業務固有ロジック

## インストール

```bash
cd tools/md-drf-codegen
pip install -e ".[dev]"
```

## Markdown 仕様

最低限以下のセクションが必要です。

- `## API一覧` — API ID, API名, メソッド, パス, リクエスト型, レスポンス型
- `## 型定義` — 型名, プロパティ, 型, 必須, Nullable, **制約**（任意）

`-` は `null` / 制約なしとして扱います。

### 制約列の凡例

`制約` 列は任意です。制約を付けない場合は `-` / `なし` / `null` / `制約なし` のいずれかを記載します。

複数の制約は `,` / `;` / `、` で区切って指定できます。

#### 制約なし

| 記載値 | 意味 |
|--------|------|
| `-` | 制約なし |
| `なし` | 制約なし |
| `null` | 制約なし |
| `制約なし` | 制約なし |

#### 数値型（`integer` / `number`）向け

| 記載値 | 意味 | 生成コード例 |
|--------|------|--------------|
| `1-50` | 1 以上 50 以下 | `min_value=1`, `max_value=50` |
| `1〜50` | 1 以上 50 以下（全角チルダ可） | 同上 |
| `1~50` | 1 以上 50 以下（半角チルダ可） | 同上 |
| `min:1` | 下限 1 | `min_value=1` |
| `max:50` | 上限 50 | `max_value=50` |
| `1以上` | 下限 1 | `min_value=1` |
| `50以下` | 上限 50 | `max_value=50` |
| `>=1` | 下限 1 | `min_value=1` |
| `<=50` | 上限 50 | `max_value=50` |
| `1-999999` | 大きな範囲指定 | `min_value=1`, `max_value=999999` |
| `0.1-99.9` | 小数を含む範囲（`number` 型） | `min_value=0.1`, `max_value=99.9` |

**凡例（型定義テーブル）**

```markdown
| 型名 | プロパティ | 型 | 必須 | Nullable | 制約 |
| --- | --- | --- | --- | --- | --- |
| ProductUpdateRequest | revision | integer | true | false | 1-50 |
| ProductUpdateRequest | price | number | true | false | 1-999999 |
| ProductUpdateRequest | discountRate | number | true | false | min:0, max:1 |
```

#### 文字列型（`string`）向け — 文字数

| 記載値 | 意味 | 生成コード例 |
|--------|------|--------------|
| `最大50文字` | 最大 50 文字 | `max_length=50` |
| `最大50文字以内` | 最大 50 文字 | `max_length=50` |
| `最大50文字まで` | 最大 50 文字 | `max_length=50` |
| `maxLength:50` | 最大 50 文字 | `max_length=50` |
| `最大:50` | 最大 50 文字 | `max_length=50` |
| `最小1文字` | 最小 1 文字 | `min_length=1` |
| `minLength:1` | 最小 1 文字 | `min_length=1` |
| `1文字以上` | 最小 1 文字 | `min_length=1` |

**凡例（型定義テーブル）**

```markdown
| 型名 | プロパティ | 型 | 必須 | Nullable | 制約 |
| --- | --- | --- | --- | --- | --- |
| ProductSummary | productName | string | true | false | 最大50文字 |
| ProductDetailResponse | description | string | false | true | 最大200文字 |
```

#### 文字列型（`string`）向け — 形式

| 記載値 | 意味 | 生成コード例 |
|--------|------|--------------|
| `半角英数字` | `[A-Za-z0-9]+` のみ許可 | `RegexValidator(regex='^[A-Za-z0-9]+$')` |
| `alphanumeric` | 半角英数字（英語表記） | 同上 |
| `ascii-alphanumeric` | 半角英数字（別名） | 同上 |
| `halfwidth-alphanumeric` | 半角英数字（YAML 形式名） | 同上 |
| `pattern:^[A-Z]+$` | 任意の正規表現 | `RegexValidator(regex='^[A-Z]+$')` |
| `pattern:^[0-9]{3}-[0-9]{4}$` | 電話番号形式など | カスタム `RegexValidator` |

**凡例（型定義テーブル）**

```markdown
| 型名 | プロパティ | 型 | 必須 | Nullable | 制約 |
| --- | --- | --- | --- | --- | --- |
| ProductSummary | productId | string | true | false | 半角英数字, 最大20文字 |
| ProductSummary | productCode | string | true | false | pattern:^[A-Z]{2}[0-9]{4}$ |
```

#### 複合指定の凡例

| 記載値 | 適用先 | 説明 |
|--------|--------|------|
| `半角英数字, 最大20文字` | `string` | 形式 + 最大文字数 |
| `最小1文字, 最大50文字` | `string` | 最小・最大文字数 |
| `min:1, max:50` | `integer` / `number` | 下限・上限を個別指定 |

#### 対応外（Validation Error）

| 例 | 理由 |
|----|------|
| `1-50` を `string` 型に指定 | 数値範囲は `integer` / `number` のみ |
| `最大50文字` を `integer` 型に指定 | 文字数制約は `string` のみ |
| `半角英数字` を `integer` 型に指定 | 形式制約は `string` のみ |
| `1-50` と `最大20文字` を同時指定 | 数値制約と文字列制約の混在は不可 |

#### YAML で直接指定する場合

Markdown の `制約` 列は、以下の YAML 構造に変換されます。

```yaml
revision:
  type: integer
  required: true
  nullable: false
  constraints:
    min: 1
    max: 50

productId:
  type: string
  required: true
  nullable: false
  constraints:
    format: halfwidth-alphanumeric   # alphanumeric も可
    maxLength: 20
    minLength: 1                     # 任意

productCode:
  type: string
  required: true
  nullable: false
  constraints:
    pattern: "^[A-Z]{2}[0-9]{4}$"
```

| YAML キー | 型 | 説明 |
|-----------|-----|------|
| `min` | number | 数値の下限（以上） |
| `max` | number | 数値の上限（以下） |
| `minLength` | integer | 文字列の最小文字数 |
| `maxLength` | integer | 文字列の最大文字数 |
| `format` | string | `alphanumeric` / `halfwidth-alphanumeric` |
| `pattern` | string | 正規表現（`format` より優先） |

## YAML 仕様

```yaml
version: 1
apis:
  - id: getProduct
    name: 製品詳細取得
    method: GET
    path: /api/products/{productId}
    requestType: null
    responseType: ProductDetailResponse
types:
  ProductDetailResponse:
    fields:
      productId:
        type: string
        required: true
        nullable: false
        constraints:
          format: halfwidth-alphanumeric
          maxLength: 20
      revision:
        type: integer
        required: true
        nullable: false
        constraints:
          min: 1
          max: 50
```

## CLI

```bash
md-drf-codegen extract specs/product.md --output generated-specs/product-api.yaml
md-drf-codegen validate generated-specs/product-api.yaml
md-drf-codegen generate generated-specs/product-api.yaml --target serializer
md-drf-codegen generate generated-specs/product-api.yaml --target all
md-drf-codegen build examples/product.md --target all
```

### Phase 1: YAML のみ

```bash
md-drf-codegen build examples/product.md --target yaml
```

### Phase 2: Serializer まで

```bash
md-drf-codegen build examples/product.md --target serializer
```

### Phase 3: すべて

```bash
md-drf-codegen build examples/product.md --target all
```

### `--force`

既存ファイルがある場合、通常はエラーになります。上書きするには `--force` を指定します。

### `--check`

ファイルを書き換えず、生成結果と既存ファイルの差分を検証します（CI 向け）。差分がある場合は非 0 終了します。

## 生成ファイル一覧

`--target all` 時:

- `{prefix}_serializers.py`
- `{prefix}_views.py`
- `urls.py`
- `test_serializers.py`
- `test_urls.py`
- `test_views.py`
- `conftest.py`
- `__init__.py`

## 既存 DRF プロジェクトへの組み込み

```bash
md-drf-codegen generate product-api.yaml \
  --target all \
  --output ./existing_project/products/generated/
```

生成された `urls.py` をプロジェクトの URLConf から `include` してください。

## 設計判断

- `number` 型は初期実装では `FloatField` を使用します（YAML に Decimal 精度情報がないため）。
- View は業務ロジックを持たず `NotImplementedError` を raise します。
- 同一パスに複数 HTTP メソッドがある場合、1 つの `APIView` にまとめます（Django URL ルーティングの制約）。

## 注意事項

**生成された View に業務ロジックを直接大量に追記すると、再生成が難しくなります。**

業務ロジックは Service / Selector 層に実装し、View は薄い委譲層として保つことを推奨します。

## 制約事項

- 対応 HTTP メソッド: GET, POST, PUT（PATCH / DELETE は将来拡張）
- 未知の型は Validation Error

## 今後の拡張候補

- PATCH / DELETE 対応
- `DecimalField` の精度指定
- OpenAPI 出力

## 開発

```bash
pytest
ruff check .
```
