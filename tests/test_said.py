import pytest
from keriac.agents import Identity
from keriac.documents import Credential
from keriac.domain import SAID, SAD, DataRecord

@pytest.fixture
def alice():
    ident = Identity(name="alice")
    yield ident
    ident.close()

def test_said_calculate_dict():
    """Test SAID calculation for a raw dictionary."""
    data = {"name": "Alice", "d": ""}
    # Create DataRecord to calculate SAID
    sad = DataRecord(data)
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
    
    cred = Credential.create(issuer_aid=alice.aid, schema=schema_said, attributes=attributes)
    
    # Calculate SAID for the object
    original_said = cred.said
    
    assert isinstance(original_said, SAID)
    assert cred.verify()

def test_said_verify_invalid():
    """Test SAID verification with invalid data."""
    data = {"name": "Bob", "d": "E_invalid_said_here"}
    sad = DataRecord(data)
    assert not sad.verify()

def test_acdc_inheritance(alice):
    """Verify that ACDC correctly inherits from SAD and has SAID type."""
    schema_said = "EM9M_xyz_dummy_schema_said_1234567890" 
    attributes = {"name": "Alice Credential"}
    cred = Credential.create(issuer_aid=alice.aid, schema=schema_said, attributes=attributes)
    
    assert isinstance(cred, Credential)
    assert isinstance(cred, SAD)
    assert isinstance(cred.said, SAID)
    assert cred.said.startswith("E")
    assert cred.json.startswith('{"v":')

def test_use_case(alice):
    """
    Complete use case:
    1. Alice (Issuer) creates ACDC birthday greeting for Ivan.
    2. Alice signs/anchors the ACDC in her KEL.
    3. Ivan (Recipient) verifies the ACDC against Alice's KEL.
    """
    ivan = Identity(name="ivan")
    
    # 1. Alice creates ACDC
    schema_said = "EM9M_xyz_dummy_schema_said_1234567890" 
    attributes = {"message": "Congrat Ivan with Birthday", "award": "Best Developer"}
    
    # Passing ivan.aid as recipient
    cred = Credential.create(issuer_aid=alice.aid, schema=schema_said, attributes=attributes, recipient=ivan.aid)
    
    # 2. Alice anchors the ACDC in her KEL
    alice.anchor(cred)
    
    # 3. Ivan verifies the ACDC
    # Ivan has the cred object and Alice's KEL
    assert cred.verify() is True
    assert alice.kel.is_anchored(cred.said) is True
    
    # Verification with wrong KEL should fail
    assert ivan.kel.is_anchored(cred.said) is False
    
    ivan.close()
