import pytest
from keriac import Identifier, ACDC, SAID, SAD

@pytest.fixture
def alice():
    ident = Identifier(name="alice")
    yield ident
    ident.close()

def test_said_calculate_dict():
    """Test SAID calculation for a raw dictionary."""
    data = {"name": "Bob", "d": ""}
    said = SAID.calculate(data)
    
    assert said.startswith("E")
    # SAID.calculate does not modify the dict in place
    assert data["d"] == ""
    
    # Verify it matches
    assert SAID.verify(data, said)

def test_said_calculate_object(alice):
    """Test SAID calculation for a SAD object (ACDC)."""
    schema_said = "EM9M_xyz_dummy_schema_said_1234567890" 
    attributes = {"name": "Alice"}
    
    cred = ACDC.create(issuer=alice, schema=schema_said, attributes=attributes)
    
    # Calculate SAID for the object
    # In KERI, ACDC already has a SAID, but we can verify our utility works on it
    original_said = cred.said
    calculated_said = SAID.calculate(cred)
    
    print(f"\nDEBUG: original   = {original_said}")
    print(f"DEBUG: calculated = {calculated_said}")
    assert calculated_said == original_said
    assert SAID.verify(cred, calculated_said)

def test_said_verify_invalid():
    """Test SAID verification with invalid data."""
    data = {"name": "Bob", "d": "E_invalid_said_here"}
    assert not SAID.verify(data, data["d"])

def test_sad_inheritance(alice):
    """Verify that ACDC correctly inherits from SAD."""
    schema_said = "EM9M_xyz_dummy_schema_said_1234567890" 
    attributes = {"name": "Alice"}
    cred = ACDC.create(issuer=alice, schema=schema_said, attributes=attributes)
    
    assert isinstance(cred, SAD)
    assert cred.said is not None
    assert cred.json.startswith('{"v":')
