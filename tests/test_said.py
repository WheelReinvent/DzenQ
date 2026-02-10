import pytest
from keriac import Identity, ACDC, SAID, SAD

@pytest.fixture
def alice():
    ident = Identity(name="alice")
    yield ident
    ident.close()

def test_said_calculate_dict():
    """Test SAID calculation for a raw dictionary."""
    data = {"name": "Alice", "d": ""}
    said = SAID.from_data(data)
    
    assert isinstance(said, SAID)
    assert isinstance(said, str)
    assert said.startswith("E")
    
    # Verify the SAID matches
    assert said.verify(data)

def test_said_calculate_object(alice):
    """Test SAID calculation for a SAD object (ACDC)."""
    schema_said = "EM9M_xyz_dummy_schema_said_1234567890" 
    attributes = {"name": "Alice Credential"}
    
    cred = ACDC.create(issuer=alice, schema=schema_said, attributes=attributes)
    
    # Calculate SAID for the object
    original_said = cred.said
    calculated_said = SAID.from_data(cred.data)
    
    assert isinstance(original_said, SAID)
    assert calculated_said == original_said
    assert calculated_said.verify(cred.data)

def test_said_verify_invalid():
    """Test SAID verification with invalid data."""
    data = {"name": "Bob", "d": "E_invalid_said_here"}
    said = SAID(data["d"])
    assert not said.verify(data)

def test_acdc_inheritance(alice):
    """Verify that ACDC correctly inherits from SAD and has SAID type."""
    schema_said = "EM9M_xyz_dummy_schema_said_1234567890" 
    attributes = {"name": "Alice Credential"}
    cred = ACDC.create(issuer=alice, schema=schema_said, attributes=attributes)
    
    assert isinstance(cred, ACDC)
    assert isinstance(cred, SAD)
    assert isinstance(cred.said, SAID)
    assert cred.said.startswith("E")
    assert cred.json.startswith('{"v":')
