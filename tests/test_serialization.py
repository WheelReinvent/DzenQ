import pytest
from keriac import SAID, Event, pack, unpack, Identity, PublicKey, Signature, DataRecord
from keriac.logbook.entries.event import InteractionEvent

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
    sad = DataRecord(data)
    raw = sad.serialize()
    assert raw == sad.raw
    assert len(raw) == sad.size
    
    from keriac import SAD
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

def test_polymorphic_unpacking():
    ident = Identity(name="alice")
    cred_said = "ENvO1234567890123456789012345678901234567890"
    ident.anchor(cred_said)
    
    # Let's pack: SAID, an Event (last interaction), and another SAID
    said1 = SAID("ENvO1234567890123456789012345678901234567890")
    event = list(ident.kel)[-1]
    said2 = SAID("EAvO1234567890123456789012345678901234567890")
    
    stream = pack([said1, event, said2])
    
    # Unpack polymorphicly (no cls argument)
    unpacked = unpack(stream)
    
    assert len(unpacked) == 3
    assert isinstance(unpacked[0], SAID)
    assert isinstance(unpacked[1], InteractionEvent)
    assert isinstance(unpacked[2], SAID)
    
    assert unpacked[0] == said1
    assert unpacked[1].said == event.said
    assert unpacked[2] == said2
    
    ident.close()

@pytest.mark.parametrize("cls, qb64", [
    (SAID, "EGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRk"),  # Blake3-256
    (SAID, "FGVlZWVlZWVlZWVlZWVlZWVlZWVlZWVlZWVlZWVlZWVl"),  # Blake2b-256
    (SAID, "IGZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZm"),  # SHA2-256
    (PublicKey, "DGFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFh"),  # Ed25519
    (PublicKey, "BGJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJi"),  # Ed25519 Non-trans
    (PublicKey, "1AAAY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2Nj"),  # ECDSA SECP256K1
    (Signature, "AABnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dn"), # Ed25519 Sig ('A')
    (Signature, "CABoaGhoaGhoaGhoaGhoaGhoaGhoaGhoaGhoaGhoaGhoaGhoaGhoaGhoaGhoaGhoaGhoaGhoaGhoaGhoaGhoaGho"), # ECDSA Sig ('C')
])
def test_various_prefixes_serialization(cls, qb64):
    """
    Test that various KERI primitive types with different prefixes can be serialized/deserialized.

    Prefix Explanations:
    - 'E': Blake3-256 digest (SAID). Used for self-addressing identifiers.
    - 'F': Blake2b-256 digest (SAID). Another supported hash algorithm.
    - 'I': SHA2-256 digest (SAID). Standard SHA-2 digest.
    - 'D': Ed25519 public key (Transferable). The default signing key type in KERI.
    - 'B': Ed25519 public key (Non-transferable). Used for one-time rotation keys or witness identifiers.
    - '1AAA': ECDSA SECP256K1 public key. Supports Bitcoin/Ethereum curve keys.
    - 'A': Ed25519 signature. Standard signature for Ed25519 keys.
    - 'C': ECDSA SECP256K1 signature. Standard signature for SECP256K1 keys.
    """
    original = cls(qb64)
    raw = original.serialize()
    
    # 1. Test explicit deserialization
    unpacked = cls.deserialize(raw)
    assert unpacked == original
    assert isinstance(unpacked, cls)
    
    # 2. Test polymorphic unpacking
    results = unpack(raw)
    assert len(results) == 1
    assert results[0] == original
    assert isinstance(results[0], cls)

def test_mixed_type_stream_serialization():
    """Test polymorphic unpacking of a complex stream containing various types."""
    objs = [
        SAID("EGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRk"),
        PublicKey("DGFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFh"),
        Signature("AABnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dn"),
        SAID("FGVlZWVlZWVlZWVlZWVlZWVlZWVlZWVlZWVlZWVlZWVl"),
        PublicKey("1AAAY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2Nj")
    ]
    
    stream = pack(objs)
    unpacked = unpack(stream)
    
    assert len(unpacked) == len(objs)
    for i, obj in enumerate(objs):
        assert unpacked[i] == obj
        assert isinstance(unpacked[i], obj.__class__)


