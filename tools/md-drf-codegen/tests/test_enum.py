"""Enum constraint generation tests."""

from __future__ import annotations

from pathlib import Path

from md_drf_codegen.extract import extract_from_markdown
from md_drf_codegen.generator import GenerateTarget, generate_code_files
from md_drf_codegen.generator.openapi_generator import build_openapi_document
from md_drf_codegen.schema import (
    ApiSpec,
    FieldDefinition,
    TypeDefinition,
)
from md_drf_codegen.schema.constant import ConstantDefinition
from md_drf_codegen.schema.constraints import EnumMember, FieldConstraints

_CHOICES_STATUS = "choices=[(m.value, m.name) for m in Status]"
_CHOICES_PRIORITY = "choices=[(m.value, m.name) for m in Priority]"


def test_choice_field_generated_for_enum() -> None:
    spec = ApiSpec(
        version=1,
        apis=[],
        types={
            "Sample": TypeDefinition(
                fields={
                    "status": FieldDefinition(
                        type="integer",
                        required=True,
                        nullable=False,
                        constraints=FieldConstraints(
                            enum=[
                                EnumMember(value=1, label="Low"),
                                EnumMember(value=2, label="Middle"),
                                EnumMember(value=3, label="High"),
                            ]
                        ),
                    ),
                }
            ),
        },
    )
    files = generate_code_files(spec, target=GenerateTarget.SERIALIZER, package_name="sample")
    content = files["sample_serializers.py"]
    assert "from enum import Enum" in content
    assert "class Status(Enum):" in content
    assert "LOW = 1" in content
    assert "MIDDLE = 2" in content
    assert "HIGH = 3" in content
    assert _CHOICES_STATUS in content
    assert "Status.choices" not in content
    assert "from django.db import models" not in content


def test_shared_enum_is_defined_once() -> None:
    enum = FieldConstraints(
        enum=[
            EnumMember(value=1, label="Low"),
            EnumMember(value=2, label="Middle"),
            EnumMember(value=3, label="High"),
        ]
    )
    spec = ApiSpec(
        version=1,
        apis=[],
        types={
            "A": TypeDefinition(
                fields={
                    "status": FieldDefinition(
                        type="integer", required=True, nullable=False, constraints=enum
                    ),
                }
            ),
            "B": TypeDefinition(
                fields={
                    "status": FieldDefinition(
                        type="integer", required=True, nullable=False, constraints=enum
                    ),
                }
            ),
        },
    )
    files = generate_code_files(spec, target=GenerateTarget.SERIALIZER, package_name="sample")
    content = files["sample_serializers.py"]
    assert content.count("class Status(Enum):") == 1
    assert content.count(_CHOICES_STATUS) == 2


def test_openapi_includes_enum_values() -> None:
    spec = ApiSpec(
        version=1,
        apis=[],
        types={
            "Sample": TypeDefinition(
                fields={
                    "status": FieldDefinition(
                        type="integer",
                        required=True,
                        nullable=False,
                        constraints=FieldConstraints(
                            enum=[
                                EnumMember(value=1, label="Low"),
                                EnumMember(value=2, label="Middle"),
                                EnumMember(value=3, label="High"),
                            ]
                        ),
                    ),
                }
            ),
        },
    )
    doc = build_openapi_document(spec, title="Sample")
    status = doc["components"]["schemas"]["Sample"]["properties"]["status"]
    assert status["enum"] == [1, 2, 3]
    assert "1=Low" in status["description"]


def test_external_constant_is_imported() -> None:
    spec = ApiSpec(
        version=1,
        apis=[],
        constants=[
            ConstantDefinition(
                path="common/util/Consts.py",
                className="Status",
                remarks="製品ステータス",
            )
        ],
        types={
            "Sample": TypeDefinition(
                fields={
                    "status": FieldDefinition(
                        type="integer",
                        required=True,
                        nullable=False,
                        constraints=FieldConstraints(
                            enum=[
                                EnumMember(value=1, label="Low"),
                                EnumMember(value=2, label="Middle"),
                                EnumMember(value=3, label="High"),
                            ]
                        ),
                    ),
                }
            ),
        },
    )
    files = generate_code_files(spec, target=GenerateTarget.SERIALIZER, package_name="sample")
    content = files["sample_serializers.py"]
    assert "from common.util.Consts import Status" in content
    assert "class Status(Enum):" not in content
    assert _CHOICES_STATUS in content
    assert "from enum import Enum" not in content


def test_ref_only_requires_constants_list() -> None:
    spec = ApiSpec(
        version=1,
        apis=[],
        constants=[
            ConstantDefinition(path="common/util/Consts.py", className="Priority"),
        ],
        types={
            "Sample": TypeDefinition(
                fields={
                    "level": FieldDefinition(
                        type="integer",
                        required=True,
                        nullable=False,
                        constraints=FieldConstraints(enum_ref="Priority"),
                    ),
                }
            ),
        },
    )
    files = generate_code_files(spec, target=GenerateTarget.SERIALIZER, package_name="sample")
    content = files["sample_serializers.py"]
    assert "from common.util.Consts import Priority" in content
    assert _CHOICES_PRIORITY in content


def test_product_markdown_parses_status_enum() -> None:
    product_md = Path(__file__).resolve().parents[1] / "examples" / "product.md"
    spec = extract_from_markdown(product_md)
    assert len(spec.constants) == 1
    assert spec.constants[0].class_name == "Status"
    assert spec.constants[0].path == "common/util/Consts.py"
    assert spec.constants[0].import_module() == "common.util.Consts"

    status = spec.types["ProductUpdateRequest"].fields["status"]
    assert status.constraints is not None
    assert status.constraints.enum is not None
    assert [m.value for m in status.constraints.enum] == [1, 2, 3]
    assert [m.label for m in status.constraints.enum] == ["Low", "Middle", "High"]

    files = generate_code_files(spec, target=GenerateTarget.SERIALIZER, package_name="product")
    content = files["product_serializers.py"]
    assert "from common.util.Consts import Status" in content
    assert "class Status(Enum):" not in content
    assert _CHOICES_STATUS in content
    assert "ステータスの値が正しくありません" in content
