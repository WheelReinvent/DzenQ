import pytest
from keriac import SAD, SAID, Event, ACDC, pack, unpack, Identity
from keriac.event import InceptionEvent, InteractionEvent

def test_said_serialization():
    # Use a valid KERI SAID (Blake3-256 is 'E')
    original = SAID("ENvO1234567890123456789012345678901234567890")
    raw = original.serialize()
    assert isinstance(raw, bytes)
    assert len(raw) == original.size
    
    unpacked = SAID.deserialize(raw)
    assert unpacked == original
    assert isinstance(unpacked, SAID)

def test_sad_serialization():
    data = {"v": "KERI10JSON000050_", "d": "ENvO1234567890123456789012345678901234567890", "foo": "bar"}
    sad = SAD(data)
    raw = sad.serialize()
    assert raw == sad.raw
    assert len(raw) == sad.size
    
    unpacked = SAD.deserialize(raw)
    assert unpacked.data == sad.data
    assert unpacked.said == sad.said

def test_batch_serialization():
    # Setup some objects with valid SAIDs
    said1 = SAID("ENvO1234567890123456789012345678901234567890")
    said2 = SAID("EAvO1234567890123456789012345678901234567890")
    
    # Pack SAIDs
    stream = pack([said1, said2])
    assert len(stream) == said1.size + said2.size
    
    # Unpack SAIDs
    unpacked = unpack(stream, SAID)
    assert len(unpacked) == 2
    assert unpacked[0] == said1
    assert unpacked[1] == said2

def test_event_batch_serialization():
    ident = Identity(name="alice")
    # Create two events
    cred_said = "ENvO1234567890123456789012345678901234567890"
    ident.anchor(cred_said)
    ident.anchor(cred_said) # Another one
    
    kel = list(ident.kel)
    assert len(kel) >= 3 # Inception + 2 Interaction
    
    # Pack the last two events
    events_to_pack = kel[-2:]
    stream = pack(events_to_pack)
    assert len(stream) == events_to_pack[0].size + events_to_pack[1].size
    
    # Unpack events
    unpacked = unpack(stream, Event)
    assert len(unpacked) == 2
    assert isinstance(unpacked[0], InteractionEvent)
    assert isinstance(unpacked[1], InteractionEvent)
    assert unpacked[0].said == events_to_pack[0].said
    assert unpacked[1].said == events_to_pack[1].said
    
    ident.close()

def test_mixed_unsupported():
    # Unpacking requires all objects of the same class in our simple implementation
    # unless we create a more complex poly-unpacker.
    pass
