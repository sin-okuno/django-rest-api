"""Shared fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from md_drf_codegen.extract import extract_from_markdown
from md_drf_codegen.yaml_io import write_api_spec_yaml

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PRODUCT_MD = PACKAGE_ROOT / "examples" / "product.md"


@pytest.fixture(scope="session")
def product_spec_yaml(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("spec") / "product-api.yaml"
    write_api_spec_yaml(extract_from_markdown(PRODUCT_MD), out)
    return out
