import pytest
import json
from keriac import Schema, registry, ACDC, Identity, Schemas, SAID

@pytest.fixture
def alice():
    ident = Identity(name="alice")
    yield ident
    ident.close()

def test_schema_basic():
    """Test raw schema SAIDification and validation."""
    raw_schema = {
        "$id": "",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Test Schema",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        },
        "required": ["name"]
    }
    
    schema = Schema(raw_schema)
    assert schema.said.startswith("E")
    
    # Valid data
    assert schema.verify_dict({"name": "Alice", "age": 30}) is True
    # Invalid data (missing required)
    assert schema.verify_dict({"age": 30}) is False
    # Invalid data (wrong type)
    assert schema.verify_dict({"name": "Alice", "age": "thirty"}) is False

def test_registry_lookup():
    """Test vLEI alias lookup in registry."""
    qvi_said = registry.resolve_said("qvi")
    assert qvi_said == Schemas.QVI
    
    le_said = registry.resolve_said("Legal_Entity")
    assert le_said == Schemas.LE

def test_acdc_with_schema_instance(alice):
    """Test creating ACDC with a Schema object."""
    raw_schema = {
        "$id": "",
        "type": "object",
        "properties": {
            "msg": {"type": "string"}
        }
    }
    test_schema = Schema(raw_schema)
    
    # Register it so ACDC can find it for verify_schema
    registry.register(test_schema, "test_msg")
    
    cred = ACDC(
        issuer=alice,
        schema=test_schema,
        attributes={"msg": "hello schema"}
    )
    
    assert cred.schema == test_schema.said
    assert cred.verify_schema() is True

def test_acdc_with_alias(alice):
    """Test creating ACDC with a registry alias."""
    # Create and register a custom schema
    raw_schema = {
        "$id": "",
        "type": "object",
        "properties": {
            "code": {"type": "integer"}
        }
    }
    custom_schema = Schema(raw_schema)
    registry.register(custom_schema, "status_code")
    
    cred = ACDC(
        issuer=alice,
        schema="status_code",
        attributes={"code": 200}
    )
    
    assert cred.schema == custom_schema.said
    assert cred.verify_schema() is True
    
    # Negative test
    bad_cred = ACDC(
        issuer=alice,
        schema="status_code",
        attributes={"code": "broken"} # Should be integer
    )
    assert bad_cred.verify_schema() is False

def test_vlei_alias_creation(alice):
    """Test that standard vLEI aliases work for creation."""
    # We use QVI alias
    cred = ACDC(
        issuer=alice,
        schema="vlei_issuer",
        attributes={"dt": "2023-10-27T12:00:00Z", "extra": "data"}
    )
    
    assert cred.schema == Schemas.QVI

def test_schema_as_sad():
    """Test that Schema inherits SAD functionality."""
    raw_schema = {
        "$id": "",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "SAD Schema",
        "type": "object"
    }
    schema = Schema(raw_schema)
    
    # SAD properties
    assert schema.said is not None
    assert schema.json is not None
    assert schema.qb64 is not None
    assert isinstance(schema.said, SAID)
    
    # Verify method
    assert schema.verify() is True
    # verify_schema will be False because the Registry only has stubs (empty schemas)
    # for these well-known SAIDs unless we populate them with real JSON content.
    # But the alias resolution works!
