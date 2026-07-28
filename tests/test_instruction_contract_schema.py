"""The instruction-contract schema is well-formed and rules correctly on a real contract."""

import json
from importlib import resources
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError
from referencing import Registry, Resource

CONTRACT_SCHEMA = "instruction_contract.schema.json"
PARAMETER_MAP_SCHEMA = "parameter_map.schema.json"
FIXTURES = Path(__file__).parent / "fixtures"


def load_schema(name):
    """Read a schema as the library will at runtime — from the installed package.

    Anchored on chipset.core: schemas/ holds only data files, so it is not a package.
    """
    source = resources.files("chipset.core") / "schemas" / name
    return json.loads(source.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def contract_schema():
    return load_schema(CONTRACT_SCHEMA)


@pytest.fixture(scope="module")
def validator(contract_schema):
    # The contract $refs the parameter map by absolute URN, which resolves only
    # against a registry holding both schemas keyed by their $id.
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema))
        for schema in (contract_schema, load_schema(PARAMETER_MAP_SCHEMA))
    )
    return Draft202012Validator(contract_schema, registry=registry)


@pytest.fixture(scope="module")
def reference_contract():
    source = FIXTURES / "string_upper.contract.json"
    return json.loads(source.read_text(encoding="utf-8"))


def test_schema_self_validates_against_the_meta_schema(contract_schema):
    Draft202012Validator.check_schema(contract_schema)


def test_reference_contract_validates(validator, reference_contract):
    validator.validate(reference_contract)


def test_unknown_top_level_property_is_rejected(validator, reference_contract):
    with pytest.raises(ValidationError):
        validator.validate({**reference_contract, "on_cancel": "chipset.string:undo"})
