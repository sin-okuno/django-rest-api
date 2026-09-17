# md-drf-codegen

Markdown 仕様書から YAML を生成し、その YAML から Django REST Framework の定型コードを生成する CLI ツールです。

**目的:** API 開発の定型作業（Serializer / View 骨格 / URL / 基本テスト）を削減し、開発者が Selector / Service / 業務ロジックに集中できるようにする。

**重要:** 生成処理に AI は使用しません。Parser / Pydantic / Jinja2 による決定論的な変換のみです。

## 対象範囲

- Markdown → YAML（ApiSpec 中間形式）
- YAML → OpenAPI 3.0（Swagger UI / Editor 用）
- YAML → Serializer
- YAML → View 骨格（Handler 関数へ委譲・デモレスポンス）
- YAML → Handler 関数（デモデータ。業務実装の差し替え先）
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

### セクション一覧

| セクション | 必須 | 内容 |
| --- | --- | --- |
| `## API一覧` | 必須 | API ID, API名, メソッド, パス, リクエスト型, レスポンス型, **備考**（任意） |
| `## 型定義` | 必須 | 型名, プロパティ, 型, 必須, Nullable, **制約** / **エラーメッセージ** / **備考**（いずれも任意） |
| `## パスパラメータ` | パスに `{name}` があるとき必須 | パラメータ名, 型, 制約, **エラーメッセージ** / **備考**（任意） |
| `## 定数定義一覧` | Enum を既存クラスから使うとき | ファイルパス, クラス名, **備考**（任意） |

`-` は `null` / 制約なし / 備考なしとして扱います。`備考` は ApiSpec YAML に保存され、OpenAPI の `description` にも反映されます。

サンプル: [examples/product.md](examples/product.md)

### パスパラメータとクエリパラメータ

#### パスパラメータ（GET / POST / PUT / DELETE 共通）

パス列の `{name}` プレースホルダで指定します。型定義テーブルには**載せません**（URL から自動抽出）。

形式検証（桁数・半角英数字など）は `## パスパラメータ` セクションで定義し、`{prefix}_path_validators.py` と View 冒頭の検証呼び出しを生成します。存在チェック（DB にあるか）は生成対象外です。

```markdown
## パスパラメータ

| パラメータ名 | 型 | 制約 | エラーメッセージ | 備考 |
| --- | --- | --- | --- | --- |
| productId | string | 半角英数字, 最大20文字 | - | URL 上の製品 ID |
```

API パスで使う `{productId}` は、上表に必ず定義してください（`制約` 列は型定義と同じ凡例。`備考` は任意）。

| 設計書のパス | 生成 URL | 生成 View（例） |
|-------------|----------|----------------|
| `/api/products/{productId}` | `api/products/<str:product_id>` | `def get(self, request, product_id: str)` |
| `/api/products/{productId}` | 同上 | `def put(self, request, product_id: str)` |

`updateProduct` のように **PUT / POST でもパスパラメータは同様にメソッド引数**として生成されます。リクエストボディは `request.data`、パス値は引数で受け取ります。

```python
def put(...) -> Response:
    try:
        ...
        with transaction.atomic():
            payload = handle_update_product(...)
        return Response(ProductDetailResponseSerializer(instance=payload).data)
    except (APIException, Http404, PermissionDenied):
        raise
    except Exception as exc:
        logger.exception(...)
        raise InternalServerError() from exc  # DRF exception handler へ委譲
```

POST / PUT / DELETE の `transaction.atomic()` は **Handler 呼び出しのみ**を囲みます（パス検証・リクエスト Serializer 検証・レスポンス整形は外）。  
POST でレスポンス型がある場合は `201 Created` を返します。
レスポンスは入力検証（`data=` + `is_valid`）せず、`Serializer(instance=payload).data` で整形します。  
予期しない例外はログに残し、固定メッセージの `APIException` サブクラスを再送出して **DRF の exception handler** に処理させます（View 内で 500 Response を自作しません）。

#### クエリパラメータ（GET / DELETE）

GET / DELETE で検索条件・オプションなどを渡す場合は、**リクエスト型**にクエリパラメータのフィールドを定義します。  
DELETE でリクエスト型が不要な場合は `-` にします。

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
| API ID | API名 | メソッド | パス | リクエスト型 | レスポンス型 | 備考 |
| listProducts | 製品一覧取得 | GET | /api/products | ProductListRequest | ProductListResponse | キーワード検索 |
| createProduct | 製品作成 | POST | /api/products | ProductCreateRequest | ProductDetailResponse | 新規登録 |
| getProduct | 製品詳細取得 | GET | /api/products/{productId} | ProductDetailQuery | ProductDetailResponse | - |
| updateProduct | 製品更新 | PUT | /api/products/{productId} | ProductUpdateRequest | ProductDetailResponse | 楽観ロック |
| deleteProduct | 製品削除 | DELETE | /api/products/{productId} | - | - | レスポンス型なし → 204 |

| 型名 | プロパティ | 型 | 必須 | Nullable | 制約 | 備考 |
| ProductListRequest | keyword | string | false | false | 最大50文字 | 部分一致 |
| ProductListRequest | cweId | string | false | false | pattern:^CWE-[0-9]+$, 最大20文字 | 例: CWE-12345 |
| ProductListRequest | page | integer | false | false | 1-100 | - |
| ProductListRequest | statuses | integer[] | false | false | enum:1:Low、2:Middle、3:High, ref:Status | クエリはカンマ区切り |
| ProductListRequest | tags | string[] | false | false | - | クエリはカンマ区切り |
| ProductDetailQuery | includeDeleted | boolean | false | false | - | - |
| ProductCreateRequest | tags | string[] | false | false | - | ボディは JSON 配列 |
| ProductUpdateRequest | tags | string[] | false | false | - | ボディは JSON 配列 |
```

#### パラメータの対応まとめ

| パラメータ種別 | 指定方法 | 対象メソッド | 生成コード |
|---------------|---------|-------------|-----------|
| パスパラメータ | パス列の `{productId}` + `## パスパラメータ` | GET / POST / PUT / DELETE | View 引数 + `{prefix}_path_validators.py` |
| クエリパラメータ | リクエスト型のフィールド | GET / DELETE | `request.query_params` + Serializer |
| リクエストボディ | リクエスト型のフィールド | POST / PUT | `request.data` + Serializer |

<a id="arrays"></a>

#### 配列（クエリとリクエストボディ）

Markdown 上の型はどちらも同じ `string[]` / `integer[]`（Enum 付きも可）です。  
**記載の仕方は共通**で、**呼び出し側の渡し方と生成フィールド**が GET（クエリ）と POST/PUT（ボディ）で異なります。

| 用途 | API メソッド | 生成フィールド | クライアントの渡し方 | 例 |
|------|-------------|----------------|---------------------|----|
| クエリ配列 | GET / DELETE | `CommaSeparatedListField` | **カンマ区切り 1 パラメータ** | `?tags=a,b,c` |
| ボディ配列 | POST / PUT | `serializers.ListField` | **JSON 配列** | `{"tags": ["a", "b"]}` |
| レスポンス配列 | - | `ListField`（`read_only`） | JSON 配列 | `{"items": [...]}` |

```markdown
# 同じ型表記（string[] / integer[]）
| ProductListRequest | tags | string[] | false | false | - | - | GET クエリ用 |
| ProductListRequest | statuses | integer[] | false | false | enum:1:Low、2:Middle、3:High, ref:Status | - | GET クエリ + Enum |
| ProductUpdateRequest | tags | string[] | false | false | - | - | PUT ボディ用 |
```

**クエリ（GET）の例**

```http
GET /api/products?tags=alpha,beta&statuses=1,3
```

検証後: `tags == ["alpha", "beta"]`, `statuses == [1, 3]`

OpenAPI ではクエリ配列を `style: form` / `explode: false`（カンマ区切り）で出力します。  
`?tags=a&tags=b` のような繰り返しパラメータ（explode）には対応しません。

**リクエストボディ（POST / PUT）の例**

```json
{
  "productName": "Sample",
  "price": 100,
  "revision": 1,
  "status": 1,
  "tags": ["alpha", "beta"]
}
```

| Markdown 型 | クエリ例 | ボディ JSON 例 | 検証後の値 |
|-------------|---------|----------------|------------|
| `string[]` | `?tags=a,b,c` | `{"tags": ["a", "b", "c"]}` | `["a", "b", "c"]` |
| `integer[]` | `?ids=1,2,3` | `{"ids": [1, 2, 3]}` | `[1, 2, 3]` |
| `integer[]` + `enum:…` | `?statuses=1,3` | `{"statuses": [1, 3]}` | `[1, 3]`（ChoiceField で検証） |

オブジェクト配列（例: `ProductSummary[]`）はレスポンス用のネスト Serializer 配列です。クエリのカンマ区切りにはしません。

> **よくある質問:** クエリとボディで配列の書き方を分ける必要はありますか？  
> → Markdown / YAML の型は同じ `string[]` 等で構いません。GET ならクエリ（カンマ区切り）、POST/PUT なら JSON 配列、と **HTTP 上の表現だけ**が違います。

### Nullable 列（null / 空文字）

`string` 型では Nullable 列で **null** と **空文字 (`""`)** を分けて指定できます（制約列ではありません）。

| 記載値 | `allow_null` | `allow_blank` | 意味 |
|--------|--------------|---------------|------|
| `false` | False | False | null も空文字も不可 |
| `true` | True | False | null 可、空文字は不可 |
| `blank` / `空文字` | False | True | 空文字可、null は不可 |
| `true,blank` / `true/空文字` | True | True | null も空文字も可 |

```markdown
| ProductDetailResponse | description | string | false | true,blank | 最大200文字 | - | null または空文字可 |
```

生成例: `CharField(..., allow_null=True, allow_blank=True)`

> DRF では `allow_null=True` だけでは `""` は弾かれます。レスポンスや入力で空文字を許す項目には `blank` を付けてください。  
> `blank` は `string` / `string[]` の要素にのみ有効です。

### 制約列の凡例

`制約` 列は任意です。制約を付けない場合は `-` / `なし` / `null` / `制約なし` のいずれかを記載します。

複数の制約は `,` / `;` / `、` で区切って指定できます。

#### 対応型（プリミティブ）

| Markdown 型 | 生成フィールド | OpenAPI | 入力例 |
|-------------|----------------|---------|--------|
| `string` | `CharField` | `string` | `"ABC"` |
| `integer` | `IntegerField` | `integer` | `1` |
| `number` | `DecimalField`（既定 `max_digits=20`, `decimal_places=6`） | `number` | `1.5` |
| `boolean` | `BooleanField` | `boolean` | `true` |
| `date` | `DateField` | `string` + `format: date` | `"2024-01-15"` |
| `datetime` | `DateTimeField` | `string` + `format: date-time` | `"2024-01-15T12:00:00Z"` |
| `object` | `JSONField` | `object` | `{...}` |

`date` / `datetime` には制約列を付けません（`-`）。形式は ISO 8601（日付は `YYYY-MM-DD`）です。

```markdown
| ProductDetailResponse | updatedDate | date | true | false | - |
| ProductDetailResponse | updatedAt | datetime | false | true | - |
```

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

#### Enum（列挙値）の使い方

許可値を持つフィールドは、制約列に `enum:`（および任意で `ref:`）を書きます。  
生成結果は常に DRF の `ChoiceField` で、choices は**標準ライブラリ `Enum` 互換**の次の形です。

```python
choices=[(m.value, m.name) for m in Status]
```

メンバー区切りは `|` / `｜` / `、` / `,` です。ラベルは任意（`値:ラベル`）。  
**Markdown 表では `|` が列区切りと衝突するため、`、` 区切りを推奨**します。

| 記載値 | 意味 |
|--------|------|
| `enum:1:Low、2:Middle、3:High` | 整数値 + ラベル（OpenAPI / ローカル生成用） |
| `enum:1\|2\|3` | 整数値のみ |
| `enum:Low\|Middle\|High` | 文字列 enum（フィールド型は `string`） |
| `ref:Status` | 既存クラス名を明示参照（`定数定義一覧` 必須） |

Enum は他の値制約（`1-50` / `半角英数字` など）と併用できません。適用可能な型は `integer` / `number` / `string` です。

##### 1. 既存プロジェクトの Enum を使う（推奨）

既存が次のような標準 `Enum` でもそのまま使えます。

```python
# common/util/Consts.py
from enum import Enum

class Status(Enum):
    HIGH = 1
    MIDDLE = 2
    LOW = 3

class Priority(Enum):
    IM = 1
    SH = 2
    NO = 3
```

Markdown では `## 定数定義一覧` にクラスを登録し、型定義の制約に `enum:` を書きます。

```markdown
## 定数定義一覧

| ファイルパス | クラス名 | 備考 |
| --- | --- | --- |
| common/util/Consts.py | Status | 1:Low / 2:Middle / 3:High |
| common/util/Consts.py | Priority | 1:IM / 2:SH / 3:NO |

## 型定義

| 型名 | プロパティ | 型 | 必須 | Nullable | 制約 | エラーメッセージ | 備考 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ProductUpdateRequest | status | integer | true | false | enum:1:Low、2:Middle、3:High | invalid_choice:ステータスの値が正しくありません | Status 参照 |
| ProductUpdateRequest | priority | integer | true | false | enum:1:IM、2:SH、3:NO | - | Priority 参照 |
```

生成例:

```python
from common.util.Consts import Priority, Status

status = serializers.ChoiceField(
    choices=[(m.value, m.name) for m in Status],
    required=True,
    allow_null=False,
    error_messages={'invalid_choice': 'ステータスの値が正しくありません'},
)
priority = serializers.ChoiceField(
    choices=[(m.value, m.name) for m in Priority],
    required=True,
    allow_null=False,
)
```

##### 2. フィールドと Enum クラスの紐づけ

codegen は既存 Python ファイルを読みません。次のルールでクラス名を決めます。

| 優先度 | ルール | 例 |
|--------|--------|-----|
| 1 | 制約に `ref:ClassName` がある | `ref:Priority` → `Priority` |
| 2 | プロパティ名を PascalCase 化した名前 | `status` → `Status`、`priority` → `Priority` |
| 3 | その名前が `定数定義一覧` にある | → **import**（ローカル Enum は作らない） |
| 4 | 一覧に無い | → 同モジュール内に `class Status(Enum): ...` を生成 |

プロパティ名とクラス名が一致しない場合は必ず `ref:` を付けます。

```markdown
| ProductUpdateRequest | level | integer | true | false | enum:1:IM、2:SH、3:NO, ref:Priority | - | - |
```

##### 3. ローカルに Enum を生成する場合

`定数定義一覧` が無い（または一致するクラスが無い）ときは、Serializer ファイル先頭に標準 `Enum` を生成します。

```python
from enum import Enum

class Status(Enum):
    LOW = 1
    MIDDLE = 2
    HIGH = 3
```

メンバー名はラベル（あれば）または値から `SCREAMING_SNAKE` 化します（例: ラベル `Low` → `LOW`）。

##### 4. OpenAPI との関係

- `enum:` の値一覧 → OpenAPI `enum` と説明（`1=Low` など）
- `備考` → property / operation の `description`
- 既存 Enum の実体と `enum:` の値が食い違っていても生成時は検知しません（実行時の ChoiceField 検証で判明）

##### 5. YAML 表現例

```yaml
constants:
  - path: common/util/Consts.py
    className: Status
    remarks: 製品ステータス
  - path: common/util/Consts.py
    className: Priority
    remarks: 優先度（1:IM / 2:SH / 3:NO）
# ...
status:
  type: integer
  required: true
  nullable: false
  remarks: Status 参照
  constraints:
    enum:
      - value: 1
        label: Low
      - value: 2
        label: Middle
      - value: 3
        label: High
  errorMessages:
    invalid_choice: ステータスの値が正しくありません
```

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
| `invalid_choice` | Enum（ChoiceField）の不正値 |
| `max_length` / `min_length` | 文字列長 |
| `max_value` / `min_value` | 数値範囲 |
| `pattern` | 半角英数字など形式制約（`RegexValidator` の message） |

```markdown
| 型名 | プロパティ | 型 | 必須 | Nullable | 制約 | エラーメッセージ | 備考 |
| ProductUpdateRequest | productName | string | true | false | 最大50文字 | required:製品名は必須です; max_length:製品名は50文字以内で入力してください | - |
| ProductUpdateRequest | price | number | true | false | 1-999999 | - | - |
| ProductUpdateRequest | status | integer | true | false | enum:1:Low、2:Middle、3:High | invalid_choice:ステータスの値が正しくありません | Status 参照 |
```

#### パスパラメータ

| キー | 用途 |
| --- | --- |
| `max_length` / `min_length` | 文字列長 |
| `pattern` | 形式制約 |

```markdown
| パラメータ名 | 型 | 制約 | エラーメッセージ | 備考 |
| productId | string | 半角英数字, 最大20文字 | pattern:製品IDの形式が正しくありません | URL 上の製品 ID |
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
| `pattern:^CWE-[0-9]+$` | CWE-ID（例: `CWE-12345`） | カスタム `RegexValidator` |

**凡例（型定義テーブル）**

```markdown
| 型名 | プロパティ | 型 | 必須 | Nullable | 制約 |
| --- | --- | --- | --- | --- | --- |
| ProductSummary | productId | string | true | false | 半角英数字, 最大20文字 |
| ProductSummary | productCode | string | true | false | pattern:^[A-Z]{2}[0-9]{4}$ |
| ProductListRequest | cweId | string | false | false | pattern:^CWE-[0-9]+$, 最大20文字 |
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
    requestType: ProductDetailQuery
    responseType: ProductDetailResponse
    remarks: 単一取得
pathParameters:
  productId:
    type: string
    remarks: URL 上の製品 ID
    constraints:
      format: halfwidth-alphanumeric
      maxLength: 20
constants:
  - path: common/util/Consts.py
    className: Status
    remarks: 製品ステータス
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
      status:
        type: integer
        required: true
        nullable: false
        remarks: Status Enum 参照
        constraints:
          enum:
            - value: 1
              label: Low
            - value: 2
              label: Middle
            - value: 3
              label: High
      updatedDate:
        type: date
        required: true
        nullable: false
        remarks: 最終更新日
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
| `apis[].name` | `summary` |
| `apis[].remarks` | operation `description` |
| GET の `requestType` | `parameters`（`in: query`） |
| PUT/POST の `requestType` | `requestBody` |
| `responseType` | `responses.200.content` |
| `pathParameters` | `parameters`（`in: path`） |
| `pathParameters.*.remarks` / フィールド `remarks` | `description` |
| `types` | `components/schemas` |
| `constraints.enum` | schema `enum` |
| `date` / `datetime` | `string` + `format: date` / `date-time` |
| `constants` | （OpenAPI には出さない。Serializer import 用） |

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

ただし `{prefix}_handlers.py` は業務実装の差し替え先のため、**`--force` だけでは全置換しません**。  
不足している handler 関数だけ追記します。スタブを作り直すときだけ `--force-handlers` を併用してください。

### `--check`

ファイルを書き換えず、生成結果と既存ファイルの差分を検証します（CI 向け）。差分がある場合は非 0 終了します。  
既存の `{prefix}_handlers.py` は内容の完全一致は見ず、**生成側にある関数名が揃っているか**を確認します。

## 生成ファイル一覧

`--target all` 時:

- `{prefix}_serializers.py`
- `{prefix}_handlers.py`（初回生成 + 不足関数の追記。デモ応答の差し替え先）
- `{prefix}_path_validators.py`（パスパラメータ定義がある場合）
- `{prefix}_views.py`
- `exceptions.py`（`InternalServerError` など View 共通例外）
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

- `number` 型は `DecimalField`（既定 `max_digits=20`, `decimal_places=6`）を生成します。金額・数量の float 精度リスクを避けるためです。
- API一覧で **レスポンス型にのみ** 使われる型（およびそのネスト）のフィールドは `read_only=True` になり、入力向け制約（`max_length` / Regex / `min_value` など）は付けません。
- 配列は用途でフィールドが分かれます。クエリ専用型は `CommaSeparatedListField`、ボディ専用型とレスポンスは `ListField` です。
- OpenAPI の `info.title` は Markdown の H1（ApiSpec `title`）を使います。無い場合のみ先頭 API 名にフォールバックします。
- Enum の ChoiceField は標準 `Enum` 向け（`[(m.value, m.name) for m in X]`）。Django `IntegerChoices` も動作しますが、既存定数は標準 `Enum` を想定しています。
- View は薄い委譲層とし、業務処理は `{prefix}_handlers.py` の関数に切り出します（初期実装はデモデータを返します）。
- Handler の戻り値はレスポンス型 Serializer の `instance=` で整形してから `Response` に載せます（入力用 `is_valid` は使いません）。
- View は `APIException` / `Http404` / `PermissionDenied` を再送出し、予期しない例外はログ後に `InternalServerError`（固定 detail）へ変換して DRF の exception handler に委譲します。
- POST / PUT / DELETE は Handler 呼び出しを `with transaction.atomic():` で囲みます（パス検証・入力 Serializer・レスポンス整形は外。GET は対象外）。
- POST でレスポンス型がある場合は **201 Created** を返します。
- `{prefix}_handlers.py` は既存実装を残しつつ、**不足関数だけ追記**します。全置換は `--force-handlers` のみです。
- 同一パスに複数 HTTP メソッドがある場合、1 つの `APIView` にまとめます。クラス名 / URL name はパス由来（例: `ApiProductsProductIdAPIView` / `api-products-product-id`）。
- DELETE でレスポンス型が無い場合は **204 No Content** を返します。

## 注意事項

**生成された Handler に業務ロジックを直接大量に追記すると、再生成が難しくなります。**

業務ロジックは Service / Selector 層に実装し、Handler は薄い委譲層として保つことを推奨します。

既存 Enum を参照する場合、実行時に `common.util.Consts` などが import 可能である必要があります（PYTHONPATH / プロジェクト構成）。

## 制約事項

- 対応 HTTP メソッド: GET, POST, PUT, DELETE（PATCH は将来拡張）
- 対応プリミティブ型: `string` / `integer` / `number` / `boolean` / `date` / `datetime` / `object`
- 未知の型は Validation Error
- `date` / `datetime` / `boolean` / `object` には制約列を付けない（`-`）

## 今後の拡張候補

- PATCH 対応
- Markdown からの `DecimalField` 精度（`max_digits` / `decimal_places`）明示指定
- 日付範囲制約

## 開発

```bash
pytest
ruff check .
```

詳細手順は [docs/手順書.md](docs/手順書.md) を参照してください。
