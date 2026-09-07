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
- `## 型定義` — 型名, プロパティ, 型, 必須, Nullable

`-` は `null` として扱います。

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
