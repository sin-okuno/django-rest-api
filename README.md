# django-rest-api

Django ホストプロジェクト。コード生成ツールは `tools/md-drf-codegen` に置く。

アプリケーション本体のコードは変更せず、生成サンプルは
`tools/md-drf-codegen/generated/` へ出力する。

## ツール

詳細は [tools/md-drf-codegen/README.md](tools/md-drf-codegen/README.md) を参照。

```bash
cd tools/md-drf-codegen
pip install -e ".[dev]"
md-drf-codegen build examples/product.md --target all
```
