import pytest
from keriac import Identity, ACDC

@pytest.fixture
def alice():
    """Fixture to provide a test Identity."""
    ident = Identity(name="alice")
    yield ident
    ident.close()

def test_acdc_creation(alice):
    """Test standard ACDC creation with academic terms."""
    schema_said = "EM9M_xyz_dummy_schema_said_1234567890" 
    attributes = {
        "name": "Alice Doe",
        "role": "Software Engineer",
        "dt": "2023-10-27T12:00:00Z"
    }
    
    # Create ACDC
    cred = ACDC.create(
        issuer=alice,
        schema=schema_said,
        attributes=attributes
    )
    
    # Assertions
    assert cred.said.startswith("E")
    assert len(cred.qb64) > 0
    assert cred.raw.startswith(b'{"v":')
    
    # Verify content in qb64 (json decode)
    import json
    parsed = json.loads(cred.qb64)
    assert parsed['i'] == alice.aid
    assert parsed['s'] == schema_said
    assert parsed['a']['name'] == "Alice Doe"

def test_acdc_with_recipient(alice):
    """Test ACDC creation with a recipient AID."""
    schema_said = "EM9M_xyz_dummy_schema_said_1234567890" 
    recipient_aid = "BBE-SomeRecipientAID"
    attributes = {
        "name": "Alice Doe",
        "dt": "2023-10-27T12:00:00Z"
    }
    
    cred = ACDC.create(
        issuer=alice,
        schema=schema_said,
        attributes=attributes,
        recipient=recipient_aid
    )
    
    import json
    parsed = json.loads(cred.qb64)
    assert parsed['a']['i'] == recipient_aid

def test_acdc_json_representation(alice):
    """Test JSON representation properties of ACDC."""
    schema_said = "EM9M_xyz_dummy_schema_said_1234567890" 
    attributes = {"name": "Alice"}
    
    cred = ACDC.create(issuer=alice, schema=schema_said, attributes=attributes)
    
    # Test .json property
    json_str = cred.json
    print(json_str)
    assert '"i":' in json_str
    assert '"s":' in json_str
    
    # Test .to_json() with indent
    json_pretty = cred.to_json(indent=4)
    assert "\n    " in json_pretty
    
    # Verify validity
    import json
    parsed = json.loads(json_str)
    assert parsed['s'] == schema_said
