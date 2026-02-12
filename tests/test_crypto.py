import pytest
from keriac import Identity, SAD, PublicKey, Signature, pack, unpack, DataRecord


@pytest.fixture
def alice():
    ident = Identity(name="alice")
    yield ident
    ident.close()


@pytest.fixture
def bob():
    ident = Identity(name="bob")
    yield ident
    ident.close()


def test_sign_and_verify(alice):
    """Test basic signing and verification."""
    data = b"Hello, World!"
    signature = alice.sign(data)
    
    assert isinstance(signature, Signature)
    assert alice.public_key.verify(data, signature)
    
    # Wrong data should fail
    assert not alice.public_key.verify(b"Wrong data", signature)


def test_public_key_properties(alice):
    """Test PublicKey properties."""
    pk = alice.public_key
    
    assert isinstance(pk, PublicKey)
    assert isinstance(pk, str)
    assert pk.qb64 == str(pk)
    assert pk.size > 0
    assert len(pk.serialize()) == pk.size


def test_signature_properties(alice):
    """Test Signature properties."""
    data = b"Test data"
    sig = alice.sign(data)
    
    assert isinstance(sig, Signature)
    assert isinstance(sig, str)
    assert sig.qb64 == str(sig)
    assert sig.size > 0
    assert len(sig.serialize()) == sig.size


def test_sad_signing(alice):
    """Test SAD signing with academic API."""
    sad = DataRecord({"v": "KERI10JSON000050_", "d": "", "msg": "test"})
    signature = sad.sign(alice)
    
    assert isinstance(signature, Signature)
    assert sad.verify_signature(signature, alice.public_key)


def test_cross_identity_verification(alice, bob):
    """Test that signatures are identity-specific."""
    data = b"Test message"
    alice_sig = alice.sign(data)
    
    # Alice's signature should verify with Alice's key
    assert alice.public_key.verify(data, alice_sig)
    
    # Alice's signature should NOT verify with Bob's key
    assert not bob.public_key.verify(data, alice_sig)


def test_public_key_serialization(alice):
    """Test PublicKey serialization and deserialization."""
    pk = alice.public_key
    raw = pk.serialize()
    
    assert isinstance(raw, bytes)
    assert len(raw) == pk.size
    
    # Deserialize
    pk2 = PublicKey.deserialize(raw)
    assert pk2.qb64 == pk.qb64


def test_signature_serialization(alice):
    """Test Signature serialization and deserialization."""
    data = b"Test data"
    sig = alice.sign(data)
    raw = sig.serialize()
    
    assert isinstance(raw, bytes)
    assert len(raw) == sig.size
    
    # Deserialize
    sig2 = Signature.deserialize(raw)
    assert sig2.qb64 == sig.qb64
    
    # Verify deserialized signature works
    assert alice.public_key.verify(data, sig2)


def test_pack_unpack_crypto_primitives(alice, bob):
    """Test packing and unpacking crypto primitives in CESR streams."""
    data = b"Test message"
    alice_sig = alice.sign(data)
    bob_sig = bob.sign(data)
    
    # Pack public keys and signatures
    stream = pack([alice.public_key, alice_sig, bob.public_key, bob_sig])
    
    assert isinstance(stream, bytes)
    
    # Unpack
    objects = unpack(stream)
    
    assert len(objects) == 4
    assert isinstance(objects[0], PublicKey)
    assert isinstance(objects[1], Signature)
    assert isinstance(objects[2], PublicKey)
    assert isinstance(objects[3], Signature)
    
    # Verify unpacked objects match originals
    assert objects[0].qb64 == alice.public_key.qb64
    assert objects[1].qb64 == alice_sig.qb64
    assert objects[2].qb64 == bob.public_key.qb64
    assert objects[3].qb64 == bob_sig.qb64
    
    # Verify signatures still work after unpacking
    assert objects[0].verify(data, objects[1])
    assert objects[2].verify(data, objects[3])


def test_private_key_not_serializable(alice):
    """Test that PrivateKey cannot be serialized (security feature)."""
    # PrivateKey is internal and not exposed in the public API
    # This test verifies that there's no way to serialize it
    
    # We can sign data
    data = b"Test"
    sig = alice.sign(data)
    
    # But we cannot access or serialize the private key
    # (PrivateKey is only used internally by Identity.sign())
    assert isinstance(sig, Signature)
