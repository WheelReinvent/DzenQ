
import pytest
from keriac.documents import Credential
from keriac.agents import Identity
from keriac.const import Fields

def test_event_properties(alice):
    """Verify Event properties map correctly to Fields."""
    # Create a real event using anchor
    event = alice.anchor(msg="Hello")
    
    # Check properties
    assert event.version == event.data[Fields.VERSION]
    assert event.event_type == event.data[Fields.TYPE]
    assert str(event.aid) == event.data[Fields.PREFIX]
    assert event.sequence == int(event.data[Fields.SEQUENCE], 16)
    assert event.prior == event.data[Fields.PRIOR]
    
    # Check data access
    assert event.data[Fields.SAID] == str(event.said)

def test_acdc_properties(alice):
    """Verify ACDC properties map correctly to Fields."""
    schema = "EBm9vXQ9y9A9p9v9v9v9v9v9v9v9v9v9v9v9v9v9v9v"
    attributes = {"name": "Alice"}
    
    cred = Credential.create(issuer_aid=alice.aid, schema=schema, attributes=attributes)
    
    # Check properties
    assert cred.issuer == alice.aid
    assert cred.schema == schema
    
    # KERI adds 'd' (SAID) and 'dt' (datetime) to attributes, so check subset
    for k, v in attributes.items():
        assert cred.attributes[k] == v
    
    # Check version property from SAD
    assert cred.version.startswith("ACDC")
    
    # Check underlying data
    assert cred.data[Fields.ISSUER] == alice.aid
    assert cred.data[Fields.SCHEMA] == schema
    # Check attributes subset in data
    for k, v in attributes.items():
        assert cred.data[Fields.ATTRIBUTES][k] == v

@pytest.fixture
def alice():
    ident = Identity(name="alice_prop_test")
    yield ident
    ident.close()
