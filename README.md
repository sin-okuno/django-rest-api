# django-rest-api

Django ホストプロジェクト。コード生成ツールは `tools/md-drf-codegen` に置く。

アプリケーション本体のコードは変更せず、生成サンプルは
`tools/md-drf-codegen/generated/` へ出力する。

## ツール（md-drf-codegen）

Markdown 仕様書 → ApiSpec YAML → DRF 定型コード / OpenAPI を、AI なしで決定論的に生成します。

| ドキュメント | 内容 |
| --- | --- |
| [tools/md-drf-codegen/README.md](tools/md-drf-codegen/README.md) | 機能概要・制約凡例・**Enum の使い方**・CLI |
| [tools/md-drf-codegen/docs/手順書.md](tools/md-drf-codegen/docs/手順書.md) | セットアップ〜再生成の手順 |
| [tools/md-drf-codegen/examples/product.md](tools/md-drf-codegen/examples/product.md) | 入力サンプル |

```bash
cd tools/md-drf-codegen
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
md-drf-codegen build examples/product.md --target all --force
```

主な出力:

```text
generated-specs/product-api.yaml
generated/product/   # serializers / views / urls / openapi.yaml / tests
```
