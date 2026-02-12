import pytest
from keriac import Identity, KeyLog, InceptionEvent, InteractionEvent

@pytest.fixture
def alice():
    ident = Identity(name="alice")
    yield ident
    ident.close()

def test_kel_iteration(alice):
    """Verify KeyLog iteration and event types."""
    # Create some events
    alice.anchor(msg="First interaction")
    alice.anchor(msg="Second interaction")
    
    log = alice.key_log
    assert isinstance(log, KeyLog)
    assert len(log) == 3  # Inception + 2 Interaction events
    
    events = list(log)
    assert len(events) == 3
    
    assert isinstance(events[0], InceptionEvent)
    assert events[0].sequence == 0
    
    assert isinstance(events[1], InteractionEvent)
    assert events[1].sequence == 1
    
    assert isinstance(events[2], InteractionEvent)
    assert events[2].sequence == 2

def test_kel_representation(alice):
    """Verify KeyLog string representation."""
    log = alice.key_log
    assert "KeyLog" in repr(log)
    assert "length=1" in repr(log)
