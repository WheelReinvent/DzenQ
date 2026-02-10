import pytest
from keriac import Identity, AID, SAID, Event, InceptionEvent, RotationEvent, InteractionEvent
from keri.core import coring

@pytest.fixture
def alice():
    ident = Identity(name="alice")
    yield ident
    ident.close()

def test_aid_inheritance():
    """Verify AID inherits from SAID and str."""
    aid_str = "EEn07h17_jxyS8nbeJFFgcZVK2Qf2Dq3VKBednWPqG2U"
    aid = AID(aid_str)
    
    assert isinstance(aid, AID)
    assert isinstance(aid, SAID)
    assert isinstance(aid, str)
    assert str(aid) == aid_str

def test_identity_returns_aid(alice):
    """Verify Identity.aid returns an AID instance."""
    assert isinstance(alice.aid, AID)
    assert len(alice.aid) > 0

def test_event_hierarchy(alice):
    """Verify Event hierarchy and factory creation."""
    # Alice's inception event
    hab = alice.habitat
    icp_raw = hab.makeOwnInception()
    
    event = Event(icp_raw)
    
    assert isinstance(event, InceptionEvent)
    assert isinstance(event, Event)
    assert event.event_type == coring.Ilks.icp
    assert event.sequence == 0
    assert event.aid == alice.aid
    assert isinstance(event.said, SAID)

def test_interaction_event(alice):
    """Verify InteractionEvent creation."""
    hab = alice.habitat
    ixn_raw = hab.interact(data=[])
    
    event = Event(ixn_raw)
    
    assert isinstance(event, InteractionEvent)
    assert event.event_type == coring.Ilks.ixn
    assert event.sequence == 1
    assert event.aid == alice.aid
