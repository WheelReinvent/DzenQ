from keriac import Identity, unpack
from keriac.logbook.entries.event import DelegatedInceptionEvent, InteractionEvent, InceptionEvent

def test_successful_delegation():
    # 1. Setup Delegator (Alice)
    alice = Identity(name="alice_del_test", temp=True)
    assert isinstance(list(alice.kel)[0], InceptionEvent)

    # 2. Delegate to Bob
    bob = alice.delegate(name="bob_del_test", temp=True)
    
    # 3. Verify Bob's Inception
    bob_kel = list(bob.kel)
    assert len(bob_kel) == 1
    bob_icp = bob_kel[0]
    
    assert isinstance(bob_icp, DelegatedInceptionEvent)
    assert bob_icp.delegator == alice.aid
    
    # 4. Verify Alice's Anchoring
    alice_kel = list(alice.kel)
    # Alice should have 2 events: Inception + Interaction (Anchor)
    assert len(alice_kel) == 2
    alice_ixn = alice_kel[-1]
    
    assert isinstance(alice_ixn, InteractionEvent)
    # Verify the seal in Alice's event points to Bob's event digest
    # The seal is expected to be a 'd' (Digest) seal matching Bob's SAID
    anchors = alice_ixn.anchors
    assert len(anchors) == 1
    assert anchors[0]['d'] == str(bob_icp.said)

    alice.close()
    bob.close()

def test_delegated_event_parsing():
    # Setup
    alice = Identity(name="alice_parse_test", temp=True)
    bob = alice.delegate(name="bob_parse_test", temp=True)
    
    # Get raw bytes of Bob's inception
    bob_icp = list(bob.kel)[0]
    raw = bob_icp.raw
    
    # Unpack it
    unpacked = unpack(raw)
    assert len(unpacked) == 1
    event = unpacked[0]
    
    assert isinstance(event, DelegatedInceptionEvent)
    assert event.delegator == alice.aid
    assert event == bob_icp
    
    alice.close()
    bob.close()
