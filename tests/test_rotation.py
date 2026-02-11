"""
Test key rotation functionality.
"""
import pytest
from keriac import Identity, Event
from keriac.event import RotationEvent
from keriac.types import DigestSeal, EventSeal


@pytest.fixture
def alice():
    """Create a test identity."""
    identity = Identity(name="test_alice")
    yield identity
    identity.close()


def test_basic_rotation(alice):
    """Test basic key rotation."""
    # Get initial key
    initial_key = alice.public_key
    initial_aid = alice.aid
    
    # Rotate
    rotation_event = alice.rotate()
    
    # Verify new key is different
    new_key = alice.public_key
    assert new_key.qb64 != initial_key.qb64, "Key should change after rotation"
    
    # Verify AID remains the same (identifier continuity)
    assert str(alice.aid) == str(initial_aid), "AID should not change after rotation"
    
    # Verify rotation event
    assert isinstance(rotation_event, Event), "Should return an Event"
    assert rotation_event.event_type == "rot", "Event type should be 'rot'"


def test_rotation_with_data(alice):
    """Test rotation with anchored data."""
    rotation_event = alice.rotate(data="Upgrading to quantum-resistant keys")
    
    # Verify rotation succeeded
    assert isinstance(rotation_event, Event)
    assert rotation_event.event_type == "rot"
    
    # Verify data is anchored
    anchors = rotation_event.anchors
    assert len(anchors) > 0, "Should have anchored data"
    assert anchors[0].get("msg") == "Upgrading to quantum-resistant keys"


def test_rotation_with_dict_data(alice):
    """Test rotation with dictionary data."""
    data = {"reason": "security upgrade", "timestamp": "2026-02-11"}
    rotation_event = alice.rotate(data=data)
    
    assert isinstance(rotation_event, Event)
    anchors = rotation_event.anchors
    assert len(anchors) > 0
    assert anchors[0] == data


def test_key_continuity(alice):
    """Test that AID remains constant across multiple rotations."""
    original_aid = alice.aid
    
    # Rotate multiple times
    alice.rotate()
    alice.rotate()
    alice.rotate()
    
    # AID should not change
    assert str(alice.aid) == str(original_aid), "AID must remain constant across rotations"


def test_rotation_history(alice):
    """Test accessing rotation history from KEL."""
    # Perform rotations
    alice.rotate(data="First rotation")
    alice.rotate(data="Second rotation")
    
    # Get all events from KEL
    events = list(alice.kel)
    
    # Filter rotation events
    rotations = [e for e in events if e.event_type == "rot"]
    assert len(rotations) == 2, "Should have 2 rotation events"


def test_rotation_event_properties(alice):
    """Test RotationEvent-specific properties."""
    initial_key = alice.public_key
    
    # Rotate
    rotation = alice.rotate()
    
    # Verify it's a RotationEvent
    assert isinstance(rotation, RotationEvent), f"Expected RotationEvent, got {type(rotation)}"
    
    # Verify public keys
    new_public_keys = rotation.public_keys
    assert len(new_public_keys) > 0, "Should have public keys"
    assert new_public_keys[0].qb64 != initial_key.qb64, "New public key should be different from initial key"
    assert new_public_keys[0].qb64 == alice.public_key.qb64, "Rotation event key should match identity's public key"
    
    # Verify next key commitments
    commitments = rotation.next_key_commitments
    assert len(commitments) > 0, "Should have next key commitments (pre-rotation)"


def test_rotation_sequence_numbers(alice):
    """Test that sequence numbers increment correctly."""
    # Get inception sequence
    inception_seq = list(alice.kel)[0].sequence
    assert inception_seq == 0, "Inception should be sequence 0"
    
    # First rotation
    rot1 = alice.rotate()
    assert rot1.sequence == 1, "First rotation should be sequence 1"
    
    # Second rotation
    rot2 = alice.rotate()
    assert rot2.sequence == 2, "Second rotation should be sequence 2"


def test_rotation_invalid_data_type(alice):
    """Test that invalid data types raise errors."""
    with pytest.raises(ValueError, match="Unsupported data type"):
        alice.rotate(data=12345)  # Invalid type


def test_multiple_identities_rotation(alice):
    """Test that rotations are identity-specific."""
    bob = Identity(name="test_bob")
    
    try:
        alice_aid = alice.aid
        bob_id = bob.aid
        
        # Rotate Alice
        alice.rotate()
        
        # Bob's AID should be unchanged
        assert str(bob.aid) == str(bob_id), "Bob's AID should not change when Alice rotates"
        assert str(alice.aid) == str(alice_aid), "Alice's AID should remain constant"
        
    finally:
        bob.close()


def test_rotate_with_thresholds():
    """Test rotation with explicit thresholds."""
    alice = Identity(name="alice")
    try:
        # Rotation with explicit signing threshold
        rotation = alice.rotate(current_threshold=1, next_threshold=1)
        assert isinstance(rotation, RotationEvent)
        assert rotation.event_type == "rot"
    finally:
        alice.close()


def test_rotate_with_seals():
    """Test rotation with structured KERI seals."""
    alice = Identity(name="alice")
    try:
        # Create a DigestSeal (pointing to some SAD digest)
        sad_digest = "EO7G-984_hpx0x6p7x6p7x6p7x6p7x6p7x6p7x6p7"
        seal: DigestSeal = {"d": sad_digest}
        
        rotation = alice.rotate(data=seal)
        assert isinstance(rotation, Event)
        assert len(rotation.anchors) == 1
        assert rotation.anchors[0]["d"] == sad_digest
    finally:
        alice.close()


def test_key_invalidation_after_rotation(alice):
    """
    Demonstrate that signatures from old keys are invalid 
    against the IDENTITY after rotation.
    """
    data = b"Alice's authentic message"
    
    # 1. Sign with initial key
    old_key = alice.public_key
    old_sig = alice.sign(data)
    
    # Verify it works initially (against both)
    assert old_key.verify(data, old_sig) is True
    assert alice.verify(data, old_sig) is True
    
    # 2. Rotate
    alice.rotate()
    new_key = alice.public_key
    assert new_key.qb64 != old_key.qb64, "Key MUST change"
    
    # 3. VERIFICATION AGAINST IDENTITY FAILS
    # This is what protects you! Verifiers should check against the Identity/KEL,
    # not just raw public keys.
    assert alice.verify(data, old_sig) is False, "Identity should REJECT old signature"
    
    # 4. Raw public key still verifies (mathematical property)
    # This is normal for crypto: keys don't 'explode', they just lose authorization.
    assert old_key.verify(data, old_sig) is True
    
    # 5. New signature works against Identity
    new_sig = alice.sign(data)
    assert alice.verify(data, new_sig) is True
