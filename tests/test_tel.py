import pytest
from keriac import Identity, unpack, Event
from keriac.logbook.transactions import TransactionLog

def test_registry_lifecycle():
    """
    Verify the lifecycle of a Registry:
    1. Creation (Inception)
    2. Anchoring in Issuer's KEL
    """
    # 1. Setup Issuer (Alice)
    alice = Identity(name="alice_tel_lifecycle", temp=True)
    
    # 2. Create Transaction Log
    log = alice.create_transaction_log(name="test_log")
    assert isinstance(log, TransactionLog)
    assert log.reg_k is not None
    
    # 3. Verify Anchoring in Alice's KEL
    alice_kel = list(alice.kel)
    # Expected: 1. Inception (icp) 2. Registry Anchor (ixn)
    assert len(alice_kel) >= 2
    anchor_event = alice_kel[-1]
    assert anchor_event.event_type == "ixn"
    
    # Check seal
    anchors = anchor_event.anchors
    assert len(anchors) == 1
    seal = anchors[0]
    # The seal for a registry inception is usually: {i: reg_k, s: 0, d: said}
    assert seal['i'] == log.reg_k
    assert seal['s'] == '0'

    alice.close()

def test_credential_issuance_flow():
    """
    Verify the flow of issuing a credential against a transaction log:
    1. Transaction log creation
    2. Credential issuance (anchored in KEL)
    3. ACDC structure verification
    """
    alice = Identity(name="alice_tel_issuance", temp=True)
    log = alice.create_transaction_log(name="iss_log")
    
    data = {"name": "Alice Corp Employee"}
    
    # ACDC schema SAID (mock)
    # in a real scenario, this would be a valid schema SAID
    schema_said = "EMQWE..." 
    
    try:
        # Issue Credential
        credential = alice.issue_credential(
            data=data,
            transaction_log=log,
            schema=schema_said
        )
        
        # Verify Credential Properties
        assert credential.issuer == alice.aid
        assert credential.transaction_log.reg_k == log.reg_k
        assert credential.is_revoked() is False
        
        # Verify Issuance Anchor in KEL
        alice_kel = list(alice.kel)
        # Expected: 1. Inception, 2. Registry Anchor, 3. Issuance Anchor
        assert len(alice_kel) >= 3
        iss_anchor = alice_kel[-1]
        assert iss_anchor.event_type == "ixn"
        
        # Check seal
        anchors = iss_anchor.anchors
        assert len(anchors) == 1
        seal = anchors[0]
        assert seal['i'] == log.reg_k
        # issuance sn might depend on registry events, checked loosely here
        assert 's' in seal
        assert 'd' in seal
        
    except Exception as e:
        pytest.fail(f"Issuance failed with error: {e}")
    
    alice.close()

def test_revocation_flow():
    """
    Verify the revocation flow:
    1. Issue credential
    2. Revoke credential
    3. Verify revocation anchor in KEL
    """
    alice = Identity(name="alice_tel_revocation", temp=True)
    log = alice.create_transaction_log(name="rev_log")
    
    data = {"license": "123"}
    credential = alice.issue_credential(
        data=data,
        transaction_log=log,
        schema="EMQWE..."
    )
    
    # Revoke
    credential.revoke()
    
    # Verify Revocation Anchor in KEL
    alice_kel = list(alice.kel)
    # Expected: 1. Inception, 2. Reg Anchor, 3. Iss Anchor, 4. Rev Anchor
    assert len(alice_kel) >= 4
    rev_anchor = alice_kel[-1]
    assert rev_anchor.event_type == "ixn"
    
    # Validates that the revocation mock/logic ran without error
    
    alice.close()
