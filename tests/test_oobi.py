import pytest
import requests_mock
from keriac.agents import Identity
from keriac.agents.contact import Card


def _export_kel_message(identity):
    """
    Export the full messagized KEL (event + attached signatures) for an Identity.
    This simulates what an OOBI endpoint would serve.
    """
    from keri.db.dbing import dgKey, snKey
    
    pre = identity._hab.pre
    
    # Get the inception event digest
    icp_dig = identity._hab.db.getKeLast(key=snKey(pre=pre, sn=0))
    
    # Build the dgKey for the event
    key = dgKey(pre=pre, dig=bytes(icp_dig))
    
    # Get the raw event bytes
    evt_bytes = bytes(identity._hab.db.getEvt(key=key))
    
    # Get the raw signature bytes
    sig_bytes_list = identity._hab.db.getSigs(key=key)
    
    # Build the messagized event: event bytes + counter + signatures
    from keri.core.counting import Counter, Codens
    
    # Create the counter for indexed controller signatures
    counter = Counter(code=Codens.ControllerIdxSigs, count=len(sig_bytes_list))
    
    # Concatenate: event + counter + sigs
    msg = bytearray(evt_bytes)
    msg.extend(counter.qb64b)
    for sig in sig_bytes_list:
        msg.extend(sig)
    
    return bytes(msg)


def test_card_creation():
    """Test creating a Card from an Identity."""
    alice = Identity(name="alice", temp=True)
    
    # Alice creates a card
    card = alice.create_card()
    
    # Verify card has URL
    assert card.url is not None
    assert "oobi" in card.url
    assert str(alice.aid) in card.url
    
    alice.close()


def test_card_issue_static():
    """Test Card.issue static method."""
    alice = Identity(name="alice", temp=True)
    
    # Issue a card
    card = Card.issue(alice, role="controller")
    
    assert isinstance(card, Card)
    assert str(alice.aid) in card.url
    
    alice.close()


def test_card_resolution_mock():
    """Test resolving a Card with mocked HTTP response."""
    # 1. Create Alice (the identity to be discovered)
    alice = Identity(name="alice", temp=True)
    
    # 2. Export Alice's full messagized KEL 
    kel_msg = _export_kel_message(alice)
    
    # 3. Create a Card for Alice
    card = alice.create_card()
    
    # 4. Mock the HTTP GET request
    with requests_mock.Mocker() as m:
        m.get(
            card.url,
            content=kel_msg,
            headers={'Content-Type': 'application/json+cesr'}
        )
        
        # 5. Bob resolves the card
        bob_view_of_alice = card.resolve(name="alice_remote")
        
        # 6. Verify Bob got Alice's identity
        assert bob_view_of_alice.aid == alice.aid
        assert not bob_view_of_alice.is_controller  # Remote identity
        
        # 7. Verify Bob can verify Alice's signature
        message = b"Hello from Alice"
        signature = alice.sign(message)
        
        assert bob_view_of_alice.verify(message, signature) is True
        
        bob_view_of_alice.close()
    
    alice.close()


def test_remote_identity_cannot_sign():
    """Test that Remote identities cannot sign (no keys)."""
    alice = Identity(name="alice", temp=True)
    card = alice.create_card()
    
    kel_msg = _export_kel_message(alice)
    with requests_mock.Mocker() as m:
        m.get(
            card.url,
            content=kel_msg,
            headers={'Content-Type': 'application/json+cesr'}
        )
        
        remote_alice = card.resolve(name="alice_remote")
        
        # Remote identity should not be able to sign
        assert not remote_alice.is_controller
        
        # Attempting to sign should fail
        with pytest.raises(ValueError, match="Cannot sign with Remote Identity"):
            remote_alice.sign(b"test")
        
        remote_alice.close()
    
    alice.close()


def test_remote_identity_cannot_create_card():
    """Test that Remote identities cannot create cards."""
    alice = Identity(name="alice", temp=True)
    card = alice.create_card()
    
    kel_msg = _export_kel_message(alice)
    with requests_mock.Mocker() as m:
        m.get(
            card.url,
            content=kel_msg,
            headers={'Content-Type': 'application/json+cesr'}
        )
        
        remote_alice = card.resolve(name="alice_remote")
        
        # Remote identity should not be able to create cards
        with pytest.raises(ValueError, match="Cannot issue Card for Remote Identity"):
            remote_alice.create_card()
        
        remote_alice.close()
    
    alice.close()
