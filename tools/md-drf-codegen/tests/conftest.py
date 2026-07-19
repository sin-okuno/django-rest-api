"""Shared fixtures: product-structure.md から一時 YAML を抽出する。"""

from __future__ import annotations

from pathlib import Path

import pytest

from md_drf_codegen.extract import extract_from_markdown
from md_drf_codegen.yaml_io import write_api_spec_yaml

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SPEC_MD = PACKAGE_ROOT / "examples" / "specs" / "product-structure.md"


@pytest.fixture(scope="session")
def product_structure_yaml(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """examples/specs/product-structure.md を extract した YAML パス。"""
    out = tmp_path_factory.mktemp("spec") / "product-structure.yaml"
    write_api_spec_yaml(extract_from_markdown(SPEC_MD), out)
    return out
