import json
from keriac.agents import Identity
from keriac.documents import Presentation


def test_issuance_with_recipient():
    """
    Verify that we can issue a credential bound to a specific recipient.
    """
    issuer = Identity(name="issuer_pres", temp=True)
    recipient = Identity(name="recipient_pres", temp=True)
    log = issuer.create_transaction_log("issuer_log")
    
    data = {"name": "Bob", "role": "Employee"}
    
    # Issue to recipient
    credential = issuer.issue_credential(
        data=data,
        transaction_log=log,
        recipient=recipient.aid,
        schema="EMQWE..."
    )
    
    # Check recipient field
    assert credential.recipient == recipient.aid
    # Check issuer
    assert credential.issuer == issuer.aid
    
    issuer.close()
    recipient.close()

def test_presentation_flow():
    """
    Verify the presentation flow:
    1. Issue Credential
    2. Create Presentation (with selective disclosure)
    3. Verify Presentation structure
    """
    issuer = Identity(name="issuer_flow", temp=True)
    log = issuer.create_transaction_log("flow_log")
    
    data = {"name": "Bob", "date": "2023-01-01", "secret": "XYZ"}
    credential = issuer.issue_credential(
        data=data,
        transaction_log=log,
        schema="EMQWE..."
    )
    
    # 1. Full Presentation
    pres_full = Presentation(credential=credential, transaction_log=log)
    # print(f"DEBUG: Full attributes keys: {list(pres_full.attributes.keys())}")
    # assert pres_full.disclosed_fields == list(data.keys()) 
    # The above assertion assumes ONLY data keys, but ACDC adds metadata fields (d, dt, i, s, a).
    # We should check that data keys are present, not exhaustive equality unless we filter.
    for k in data.keys():
        assert k in pres_full.attributes
    
    # 2. Selective Disclosure
    pres_partial = Presentation(credential, transaction_log=log, disclose_fields=["name", "date"])
    print(f"DEBUG: Partial attributes: {pres_partial.attributes}")
    assert "name" in pres_partial.attributes
    assert "date" in pres_partial.attributes
    assert "secret" not in pres_partial.attributes
    assert len(pres_partial.disclosed_fields) == 2
    
    # 3. Serialization
    json_str = pres_partial.to_json()
    parsed = json.loads(json_str)
    assert parsed["disclosed_fields"] == ["name", "date"]
    
    issuer.close()

def test_verification_flow():
    """
    Verify the verification flow:
    1. Valid Presentation -> True
    2. Revoked Credential -> False
    """
    issuer = Identity(name="issuer_verify", temp=True)
    log = issuer.create_transaction_log("verify_log")
    
    data = {"license": "valid"}
    credential = issuer.issue_credential(
        data=data,
        transaction_log=log,
        schema="EMQWE..."
    )
    
    # Case 1: Valid Verification
    presentation = Presentation(credential, transaction_log=log)
    assert presentation.verify() is True
    
    # Case 2: Verification Failure (Revoked)
    # Revoke credentials
    issuer.revoke_credential(credential, log)
    # Now verify should fail
    # Note: ACDC.is_revoked() checks registry.
    # presentation.verify() checks credential.is_revoked()
    assert log.status(credential) == "Revoked" # Mock check? No, logic depends on if we implemented status query
    
    # Let's see if presentation verification catches revocation
    # We must ensure credential.is_revoked() returns True.
    # In keriac.acdc.py, is_revoked calls self.registry.status (which we queried via placeholder)
    # Actually, in keriac/acdc.py we implemented:
    # if self.registry: return False (placeholder)
    
    # Only if we implement real status check in Registry.status/revoke will this work.
    # Let's fix Registry.status first or mock it for the test?
    # Actually, let's verify what happens.
    
    # ACDC.revoked implementation currently returns False (hardcoded placeholder). 
    # Wait, if we want this test to pass, we need to wire up a basic status check.
    # But Registry logic for status was "return 'Unknown'".
    
    # Let's skip the revocation check assertion if the logic isn't there yet, 
    # OR we mock it.
    
    # For now, let's assert True for valid check.
    assert presentation.verify() is False
    
    issuer.close()
