"""Error message parsing and generation tests."""

from __future__ import annotations

from pathlib import Path

from md_drf_codegen.extract import extract_from_markdown
from md_drf_codegen.generator import GenerateTarget, generate_code_files
from md_drf_codegen.parser.error_messages_parser import (
    SERIALIZER_ERROR_MESSAGE_KEYS,
    parse_error_messages_cell,
)
from md_drf_codegen.schema import (
    ApiEndpoint,
    ApiSpec,
    FieldDefinition,
    HttpMethod,
    PathParameterDefinition,
    TypeDefinition,
)
from md_drf_codegen.schema.constraints import FieldConstraints


def test_parse_error_messages_cell() -> None:
    result = parse_error_messages_cell(
        "required:必須です; max_length:50文字以内",
        allowed_keys=SERIALIZER_ERROR_MESSAGE_KEYS,
        section="型定義",
    )
    assert result == {"required": "必須です", "max_length": "50文字以内"}


def test_parse_error_messages_empty_returns_none() -> None:
    assert (
        parse_error_messages_cell(
            "-",
            allowed_keys=SERIALIZER_ERROR_MESSAGE_KEYS,
            section="型定義",
        )
        is None
    )


def test_serializer_emits_custom_error_messages() -> None:
    spec = ApiSpec(
        version=1,
        apis=[],
        types={
            "SampleRequest": TypeDefinition(
                fields={
                    "name": FieldDefinition(
                        type="string",
                        required=True,
                        nullable=False,
                        constraints=FieldConstraints(max_length=50),
                        error_messages={
                            "required": "名前は必須です",
                            "max_length": "50文字以内",
                        },
                    ),
                }
            ),
        },
    )
    files = generate_code_files(spec, target=GenerateTarget.SERIALIZER, package_name="sample")
    content = files["sample_serializers.py"]
    assert "error_messages=" in content
    assert "名前は必須です" in content
    assert "50文字以内" in content


def test_serializer_without_custom_messages_omits_error_messages_kwarg() -> None:
    spec = ApiSpec(
        version=1,
        apis=[],
        types={
            "SampleRequest": TypeDefinition(
                fields={
                    "name": FieldDefinition(
                        type="string",
                        required=True,
                        nullable=False,
                    ),
                }
            ),
        },
    )
    files = generate_code_files(spec, target=GenerateTarget.SERIALIZER, package_name="sample")
    content = files["sample_serializers.py"]
    assert "error_messages=" not in content


def test_path_validator_uses_custom_messages() -> None:
    spec = ApiSpec(
        version=1,
        apis=[
            ApiEndpoint(
                id="getItem",
                name="詳細",
                method=HttpMethod.GET,
                path="/api/items/{itemId}",
                requestType=None,
                responseType="SampleResponse",
            ),
        ],
        types={
            "SampleResponse": TypeDefinition(
                fields={"itemId": FieldDefinition(type="string", required=True, nullable=False)}
            ),
        },
        path_parameters={
            "itemId": PathParameterDefinition(
                type="string",
                constraints=FieldConstraints(max_length=10, format="halfwidth-alphanumeric"),
                error_messages={
                    "max_length": "IDは10文字以内です",
                    "pattern": "IDの形式が不正です",
                },
            ),
        },
    )
    files = generate_code_files(spec, target=GenerateTarget.ALL, package_name="sample")
    validators = files["sample_path_validators.py"]
    assert "IDは10文字以内です" in validators
    assert "IDの形式が不正です" in validators


def test_product_markdown_extracts_optional_error_messages() -> None:
    product_md = Path(__file__).resolve().parents[1] / "examples" / "product.md"
    spec = extract_from_markdown(product_md)
    product_name = spec.types["ProductUpdateRequest"].fields["productName"]
    assert product_name.error_messages is not None
    assert product_name.error_messages["required"] == "製品名は必須です"
    path = spec.path_parameters["productId"]
    assert path.error_messages is not None
    assert path.error_messages["pattern"] == "製品IDの形式が正しくありません"
