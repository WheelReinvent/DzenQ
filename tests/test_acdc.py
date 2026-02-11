import pytest
from keriac import Identity, ACDC

@pytest.fixture
def alice():
    """Fixture to provide a test Identity."""
    ident = Identity(name="alice")
    yield ident
    ident.close()

def test_acdc_creation(alice):
    """Test standard ACDC creation with direct constructor."""
    schema_said = "EM9M_xyz_dummy_schema_said_1234567890" 
    attributes = {
        "name": "Alice Doe",
        "role": "Software Engineer",
        "dt": "2023-10-27T12:00:00Z"
    }
    
    # Create ACDC directly
    cred = ACDC.create(
        issuer=alice,
        schema=schema_said,
        attributes=attributes
    )
    
    # Assertions
    assert cred.said.startswith("E")
    assert len(cred.qb64) > 0
    assert cred.raw.startswith(b'{"v":')
    
    # Verify content
    assert cred.data['i'] == alice.aid
    assert cred.data['s'] == schema_said
    assert cred.data['a']['name'] == "Alice Doe"

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
    
    assert cred.data['a']['i'] == recipient_aid

def test_acdc_wrapping_style(alice):
    """Verify wrapping an existing dict (SAD) into ACDC."""
    schema = "EBm9vXQ9y9A9p9v9v9v9v9v9v9v9v9v9v9v9v9v9v9v"
    attributes = {"name": "John Doe"}
    
    # First create one to get valid SAD data
    orig = ACDC.create(issuer=alice, schema=schema, attributes=attributes)
    sad_data = orig.data
    orig_said = orig.said
    
    # Wrapping Style
    wrapped = ACDC(sad_data)
    
    assert isinstance(wrapped, ACDC)
    assert str(wrapped.said) == str(orig_said)
    assert wrapped.data == sad_data
    assert wrapped.data == orig.data

def test_acdc_wrapping_sad_instance(alice):
    """Verify wrapping a SAD instance into ACDC."""
    schema = "EBm9vXQ9y9A9p9v9v9v9v9v9v9v9v9v9v9v9v9v9v9v"
    orig = ACDC.create(issuer=alice, schema=schema, attributes={"n": 1})
    
    # Wrapping another SAD instance
    new_acdc = ACDC(orig)
    
    assert isinstance(new_acdc, ACDC)
    assert new_acdc.said == orig.said
    assert new_acdc._sad is orig._sad

def test_acdc_json_representation(alice):
    """Test JSON representation properties of ACDC."""
    schema_said = "EM9M_xyz_dummy_schema_said_1234567890" 
    attributes = {"name": "Alice"}
    
    cred = ACDC.create(issuer=alice, schema=schema_said, attributes=attributes)
    
    # Test .json property
    json_str = cred.json
    assert '"i":' in json_str
    assert '"s":' in json_str
    
    # Test .to_json() with indent
    json_pretty = cred.to_json(indent=4)
    assert "\n    " in json_pretty
    
    # Verify validity
    import json
    parsed = json.loads(json_str)
    assert parsed['s'] == schema_said
