# md-drf-codegen

Markdown 形式の画面／API 仕様書から、Django REST Framework 向けコードを生成するツールです。

**実装済み**

- Markdown Parser / YAML 抽出・検証
- Serializer / APIView / URL / Handler クラス生成
- 生成コード向け pytest 生成（業務ロジック以外）
- pytest / Ruff / mypy

入力サンプルは `examples/specs/product-structure.md` のみです。  
生成物は必ず `examples/generated/<yaml-stem>/` へ出力します（例: `product-structure/`）。

詳細な手順は [docs/手順書.md](docs/手順書.md) を参照してください。

## セットアップ

```powershell
cd tools\md-drf-codegen
python -m venv .venv
.\.venv\Scripts\activate
pip install -e ".[dev]"
```

## 最短フロー（Markdown → YAML → コード）

```powershell
md-drf-codegen extract examples\specs\product-structure.md
md-drf-codegen validate examples\generated\product-structure.yaml
md-drf-codegen generate examples\generated\product-structure.yaml
```

出力:

- `examples/generated/product-structure.yaml`
- `examples/generated/product-structure/` 配下
  - `product_structure_serializers.py` / `product_structure_views.py` / `urls.py` / `product_structure_handlers.py`
  - `conftest.py` / `test_generated_api.py` / `__init__.py`

View は Handler を直接生成します。

```python
handler = LoadDetailHandler()
result = handler.handle(request=request, product_id=product_id)
```

## 開発コマンド

```powershell
pytest
ruff check src tests
mypy
python -m compileall -q src examples\generated
```
