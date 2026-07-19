"""Tests for DRF serializer generation."""

from __future__ import annotations

import ast
from pathlib import Path

from md_drf_codegen.generator import generate_serializers_code, generate_serializers_from_yaml
from md_drf_codegen.generator.context import build_serializers_context, serializer_class_name
from md_drf_codegen.models import ApiSpec, ApiTypeDefinition, TypeProperty
from md_drf_codegen.yaml_io import parse_api_spec_yaml


def _spec_with_all_field_kinds() -> ApiSpec:
    raw = """
version: 1
title: Field Kinds
source: test
apis: []
types:
  - name: Address
    category: api
    properties:
      - name: city
        type: string
        nullable: false
        optional: false
        description: city
  - name: Node
    category: api
    properties:
      - name: label
        type: string
        nullable: false
        optional: false
        description: label
      - name: children
        type: Node[]
        nullable: false
        optional: false
        description: recursive children
  - name: Payload
    category: api
    properties:
      - name: name
        type: string
        nullable: false
        optional: false
        description: name
      - name: count
        type: integer
        nullable: false
        optional: false
        description: count
      - name: ratio
        type: number
        nullable: false
        optional: false
        description: ratio
      - name: amount
        type: decimal
        nullable: false
        optional: false
        description: amount
      - name: active
        type: boolean
        nullable: false
        optional: false
        description: active
      - name: nickname
        type: string
        nullable: true
        optional: true
        description: nullable optional
      - name: address
        type: Address
        nullable: false
        optional: false
        description: nested
      - name: nodes
        type: Node[]
        nullable: false
        optional: false
        description: custom array
"""
    return parse_api_spec_yaml(raw)


def test_context_maps_primitives_nullable_required_nested_array_recursive() -> None:
    context = build_serializers_context(_spec_with_all_field_kinds())
    by_name = {item.type_name: item for item in context.serializers}

    assert set(by_name) == {"Address", "Node", "Payload"}
    # Dependencies first
    names = [item.type_name for item in context.serializers]
    assert names.index("Address") < names.index("Payload")
    assert names.index("Node") < names.index("Payload")

    payload = by_name["Payload"]
    fields = {field.name: field for field in payload.fields}
    assert "serializers.CharField" in fields["name"].expression
    assert "serializers.IntegerField" in fields["count"].expression
    assert "serializers.FloatField" in fields["ratio"].expression
    assert "serializers.DecimalField" in fields["amount"].expression
    assert "max_digits=20" in fields["amount"].expression
    assert "serializers.BooleanField" in fields["active"].expression
    assert "required=False" in fields["nickname"].expression
    assert "allow_null=True" in fields["nickname"].expression
    assert "AddressSerializer(" in fields["address"].expression
    assert "NodeSerializer(many=True" in fields["nodes"].expression

    node = by_name["Node"]
    assert node.deferred_fields
    deferred = {field.name: field for field in node.deferred_fields}
    assert "children" in deferred
    assert "NodeSerializer(many=True" in deferred["children"].expression


def test_generate_serializers_ast_parseable() -> None:
    code = generate_serializers_code(_spec_with_all_field_kinds())
    tree = ast.parse(code)
    class_names = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
    assert class_names == [
        "AddressSerializer",
        "NodeSerializer",
        "PayloadSerializer",
    ]


def test_generate_from_product_yaml_ast_parseable(product_structure_yaml: Path) -> None:
    code = generate_serializers_from_yaml(product_structure_yaml)
    ast.parse(code)
    assert "ProductTreeNodeDtoSerializer" in code
    assert "_declared_fields" in code  # recursive children
    assert "DecimalField" in code
    assert "max_length=100" in code
    assert "max_digits=12" in code
    assert "decimal_places=2" in code
    assert "ProductDetailApiResponseSerializer" in code
    assert "ProductUpdateApiRequestSerializer" in code


def test_digit_constraints_on_string_integer_number() -> None:
    spec = ApiSpec(
        version=1,
        title="Digits",
        source="x",
        types=[
            ApiTypeDefinition(
                name="Item",
                properties=[
                    TypeProperty(name="code", type="string", max_length=10),
                    TypeProperty(name="qty", type="integer", max_digits=3),
                    TypeProperty(name="price", type="number", max_digits=12, decimal_places=2),
                ],
            )
        ],
    )
    context = build_serializers_context(spec)
    fields = {field.name: field for field in context.serializers[0].fields}
    assert "max_length=10" in fields["code"].expression
    assert "max_value=999" in fields["qty"].expression
    assert "DecimalField" in fields["price"].expression
    assert "max_digits=12" in fields["price"].expression
    assert "decimal_places=2" in fields["price"].expression



def test_serializer_class_name() -> None:
    assert serializer_class_name("FooBar") == "FooBarSerializer"


def test_empty_type_emits_pass() -> None:
    spec = ApiSpec(
        version=1,
        title="Empty",
        source="x",
        apis=[],
        types=[ApiTypeDefinition(name="EmptyDto", properties=[])],
    )
    code = generate_serializers_code(spec)
    ast.parse(code)
    assert "class EmptyDtoSerializer" in code
    assert "pass" in code


def test_type_property_description_preserved() -> None:
    spec = ApiSpec(
        version=1,
        title="Desc",
        source="x",
        types=[
            ApiTypeDefinition(
                name="Item",
                properties=[
                    TypeProperty(
                        name="id",
                        type="string",
                        description="identifier",
                    )
                ],
            )
        ],
    )
    context = build_serializers_context(spec)
    assert context.serializers[0].fields[0].description == "identifier"
