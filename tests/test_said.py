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
    # Create SAD to calculate SAID
    sad = SAD(data)
    said = sad.said
    
    assert isinstance(said, SAID)
    assert isinstance(said, str)
    assert said.startswith("E")
    
    # Verify the SAID matches
    assert sad.verify()

def test_said_calculate_object(alice):
    """Test SAID calculation for a SAD object (ACDC)."""
    schema_said = "EM9M_xyz_dummy_schema_said_1234567890" 
    attributes = {"name": "Alice Credential"}
    
    cred = ACDC.create(issuer=alice, schema=schema_said, attributes=attributes)
    
    # Calculate SAID for the object
    original_said = cred.said
    
    assert isinstance(original_said, SAID)
    assert cred.verify()

def test_said_verify_invalid():
    """Test SAID verification with invalid data."""
    data = {"name": "Bob", "d": "E_invalid_said_here"}
    sad = SAD(data)
    assert not sad.verify()

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
