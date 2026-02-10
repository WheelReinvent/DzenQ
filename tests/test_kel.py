import pytest
from keriac import Identity, KEL, InceptionEvent, InteractionEvent

@pytest.fixture
def alice():
    ident = Identity(name="alice")
    yield ident
    ident.close()

def test_kel_iteration(alice):
    """Verify KEL iteration and event types."""
    # Create some events
    alice.anchor(msg="First interaction")
    alice.anchor(msg="Second interaction")
    
    kel = alice.kel
    assert isinstance(kel, KEL)
    assert len(kel) == 3  # Inception + 2 Interaction events
    
    events = list(kel)
    assert len(events) == 3
    
    assert isinstance(events[0], InceptionEvent)
    assert events[0].sequence == 0
    
    assert isinstance(events[1], InteractionEvent)
    assert events[1].sequence == 1
    
    assert isinstance(events[2], InteractionEvent)
    assert events[2].sequence == 2

def test_kel_representation(alice):
    """Verify KEL string representation."""
    kel = alice.kel
    assert "KEL" in repr(kel)
    assert "length=1" in repr(kel)
