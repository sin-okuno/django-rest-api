# md-drf-codegen

Markdown 仕様書から YAML を生成し、その YAML から Django REST Framework の定型コードを生成する CLI ツールです。

**目的:** API 開発の定型作業（Serializer / View 骨格 / URL / 基本テスト）を削減し、開発者が Selector / Service / 業務ロジックに集中できるようにする。

**重要:** 生成処理に AI は使用しません。Parser / Pydantic / Jinja2 による決定論的な変換のみです。

## 対象範囲

- Markdown → YAML（ApiSpec 中間形式）
- YAML → OpenAPI 3.0（Swagger UI / Editor 用）
- YAML → Serializer
- YAML → View 骨格（`NotImplementedError`）
- YAML → URL
- YAML → 基本テスト（Serializer / URL / View）

## 対象外

- Model / Migration
- Service / Selector の業務処理
- ORM / Permission / 認可 / 認証
- ProductAccess 等の業務固有ロジック

## 必須フリーウェア一覧

本ツールの**利用・開発**に必要なソフトウェアです。いずれも無料で入手できます。詳細な手順は [docs/手順書.md](docs/手順書.md) を参照してください。

### ランタイム（必須）

| ソフトウェア | バージョン | 用途 | 入手先 |
| --- | --- | --- | --- |
| [Python](https://www.python.org/downloads/) | 3.12 以上 | CLI 実行・コード生成 | python.org |
| pip | Python 同梱 | パッケージインストール | `python -m pip` |
| venv | Python 同梱 | 仮想環境の作成 | `python -m venv` |

### 本ツールが依存する Python パッケージ（`pip install` で自動取得）

`pip install -e ".[dev]"` 実行時にインストールされます。すべてオープンソース（無料）です。

| パッケージ | ライセンス概要 | 用途 |
| --- | --- | --- |
| [Typer](https://typer.tiangolo.com/) | MIT | CLI（`extract` / `validate` / `generate` / `build`） |
| [Pydantic](https://docs.pydantic.dev/) | MIT | ApiSpec のスキーマ検証 |
| [PyYAML](https://pyyaml.org/) | MIT | YAML の読み書き |
| [Jinja2](https://jinja.palletsprojects.com/) | BSD-3 | Python コード・テンプレート生成 |

### 開発・テスト用（`[dev]` オプション）

| パッケージ | 用途 |
| --- | --- |
| [pytest](https://pytest.org/) | ツール本体・生成コードのテスト |
| [pytest-django](https://pytest-django.readthedocs.io/) | DRF 向けテスト実行 |
| [ruff](https://docs.astral.sh/ruff/) | リンター |
| [mypy](https://mypy-lang.org/) | 型チェック |
| [Django](https://www.djangoproject.com/) | 生成 View / Serializer のテスト実行 |
| [djangorestframework](https://www.django-rest-framework.org/) | 生成コードの import 先 |

### リポジトリ・作業環境（推奨）

| ソフトウェア | 用途 | 入手先 |
| --- | --- | --- |
| [Git](https://git-scm.com/) | ソースの取得・バージョン管理 | git-scm.com |
| PowerShell または bash | コマンド実行 | OS 標準 |
| テキストエディタ（[VS Code](https://code.visualstudio.com/) / [Cursor](https://cursor.com/) 等） | Markdown・生成コードの編集 | 各公式サイト |

### Swagger / API ドキュメント確認用（任意・無料）

| ソフトウェア | 用途 | 入手先 |
| --- | --- | --- |
| [Swagger Editor](https://editor.swagger.io/) | ブラウザで OpenAPI YAML を表示・編集 | 公式 Web（インストール不要） |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | ローカルで Swagger UI を起動する場合 | docker.com |
| Swagger UI イメージ | `docker run swaggerapi/swagger-ui` で OpenAPI 表示 | Docker Hub |

> **メモ:** Markdown のパースは標準ライブラリ中心の独自実装です。別途 Markdown パーサーのインストールは不要です。

## インストール

Python 3.12 以上を用意し、仮想環境を作成してからインストールします。

```bash
cd tools/md-drf-codegen
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
```

## Markdown 仕様

最低限以下のセクションが必要です。

- `## API一覧` — API ID, API名, メソッド, パス, リクエスト型, レスポンス型
- `## 型定義` — 型名, プロパティ, 型, 必須, Nullable, **制約**（任意）

`-` は `null` / 制約なしとして扱います。

### パスパラメータとクエリパラメータ

#### パスパラメータ（GET / POST / PUT 共通）

パス列の `{name}` プレースホルダで指定します。型定義テーブルには**載せません**（URL から自動抽出）。

形式検証（桁数・半角英数字など）は `## パスパラメータ` セクションで定義し、`{prefix}_path_validators.py` と View 冒頭の検証呼び出しを生成します。存在チェック（DB にあるか）は生成対象外です。

```markdown
## パスパラメータ

| パラメータ名 | 型 | 制約 |
| --- | --- | --- |
| productId | string | 半角英数字, 最大20文字 |
```

API パスで使う `{productId}` は、上表に必ず定義してください（`制約` 列は型定義と同じ凡例）。

| 設計書のパス | 生成 URL | 生成 View（例） |
|-------------|----------|----------------|
| `/api/products/{productId}` | `api/products/<str:product_id>` | `def get(self, request, product_id: str)` |
| `/api/products/{productId}` | 同上 | `def put(self, request, product_id: str)` |

`updateProduct` のように **PUT / POST でもパスパラメータは同様にメソッド引数**として生成されます。リクエストボディは `request.data`、パス値は引数で受け取ります。

```python
def put(
    self,
    request: Request,
    product_id: str,
) -> Response:
    product_id = validate_product_id(product_id)
    serializer = ProductUpdateRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    ...
```

#### クエリパラメータ（GET のみ）

GET API で検索条件・ページングなどを渡す場合は、**リクエスト型**にクエリパラメータのフィールドを定義します。

| API ID | メソッド | パス | リクエスト型 | 意味 |
|--------|---------|------|-------------|------|
| listProducts | GET | `/api/products` | `ProductListRequest` | クエリのみ |
| getProduct | GET | `/api/products/{productId}` | `ProductDetailQuery` | パス + クエリ |

生成 View は `request.query_params` で Serializer 検証します。

```python
def get(
    self,
    request: Request,
    product_id: str,
) -> Response:
    serializer = ProductDetailQuerySerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    ...
```

#### 設計書の記載例

```markdown
| API ID | API名 | メソッド | パス | リクエスト型 | レスポンス型 |
| listProducts | 製品一覧取得 | GET | /api/products | ProductListRequest | ProductListResponse |
| getProduct | 製品詳細取得 | GET | /api/products/{productId} | ProductDetailQuery | ProductDetailResponse |
| updateProduct | 製品更新 | PUT | /api/products/{productId} | ProductUpdateRequest | ProductDetailResponse |

| 型名 | プロパティ | 型 | 必須 | Nullable | 制約 |
| ProductListRequest | keyword | string | false | false | 最大50文字 |
| ProductListRequest | page | integer | false | false | 1-100 |
| ProductDetailQuery | includeDeleted | boolean | false | false | - |
```

#### パラメータの対応まとめ

| パラメータ種別 | 指定方法 | 対象メソッド | 生成コード |
|---------------|---------|-------------|-----------|
| パスパラメータ | パス列の `{productId}` + `## パスパラメータ` | GET / POST / PUT | View 引数 + `{prefix}_path_validators.py` |
| クエリパラメータ | リクエスト型のフィールド | GET のみ | `request.query_params` + Serializer |
| リクエストボディ | リクエスト型のフィールド | POST / PUT | `request.data` + Serializer |

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

### エラーメッセージ列（任意）

`エラーメッセージ` 列は**任意**です。列自体がなくても、`-` / 空欄でも問題ありません。
未指定の検証項目は **DRF / 生成器の標準メッセージ**が使われます。

記法: `キー:メッセージ` を `;` / `,` / `、` で区切って複数指定できます。

#### 型定義（Serializer）

| キー | 用途 |
| --- | --- |
| `required` | 必須エラー |
| `blank` | 空文字エラー |
| `null` | null エラー |
| `invalid` | 型不正 |
| `max_length` / `min_length` | 文字列長 |
| `max_value` / `min_value` | 数値範囲 |
| `pattern` | 半角英数字など形式制約（`RegexValidator` の message） |

```markdown
| 型名 | プロパティ | 型 | 必須 | Nullable | 制約 | エラーメッセージ |
| ProductUpdateRequest | productName | string | true | false | 最大50文字 | required:製品名は必須です; max_length:製品名は50文字以内で入力してください |
| ProductUpdateRequest | price | number | true | false | 1-999999 | - |
```

#### パスパラメータ

| キー | 用途 |
| --- | --- |
| `max_length` / `min_length` | 文字列長 |
| `pattern` | 形式制約 |

```markdown
| パラメータ名 | 型 | 制約 | エラーメッセージ |
| productId | string | 半角英数字, 最大20文字 | pattern:製品IDの形式が正しくありません |
```

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
md-drf-codegen generate generated-specs/product-api.yaml --target openapi
md-drf-codegen generate generated-specs/product-api.yaml --target serializer
md-drf-codegen generate generated-specs/product-api.yaml --target all
md-drf-codegen build examples/product.md --target all
```

### OpenAPI / Swagger

`--target openapi` で **OpenAPI 3.0.3** YAML を生成します（ApiSpec YAML とは別形式）。

```bash
md-drf-codegen generate generated-specs/product-api.yaml --target openapi
# → generated-specs/product-api.openapi.yaml（入力 YAML と同じディレクトリ）

md-drf-codegen build examples/product.md --target openapi
```

`--target all` では `generated/<stem>/openapi.yaml` も同時に出力されます。

**Swagger UI で表示する例:**

1. [Swagger Editor](https://editor.swagger.io/) で `product-api.openapi.yaml` を開く
2. または Docker: `docker run -p 8080:8080 -e SWAGGER_JSON=/foo/openapi.yaml -v $(pwd):/foo swaggerapi/swagger-ui`

マッピング概要:

| ApiSpec | OpenAPI |
|---------|---------|
| `apis[].path` + `method` | `paths` |
| GET の `requestType` | `parameters`（`in: query`） |
| PUT/POST の `requestType` | `requestBody` |
| `responseType` | `responses.200.content` |
| `pathParameters` | `parameters`（`in: path`） |
| `types` | `components/schemas` |

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
- `{prefix}_path_validators.py`（パスパラメータ定義がある場合）
- `{prefix}_views.py`
- `urls.py`
- `openapi.yaml`
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

## 開発

```bash
pytest
ruff check .
```
