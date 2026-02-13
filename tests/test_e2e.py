"""
End-to-End Test: Alice Sends a ThankYou Certificate to Bob
===========================================================

This test tells a complete story of the KERI ecosystem:

    Alice, a team lead, wants to issue a "ThankYou" certificate to Bob
    for his outstanding contribution. She creates a verifiable credential,
    signs it, and makes her identity discoverable via OOBI. Bob, who has
    never interacted with Alice before, resolves her identity using a Card,
    verifies the credential's authenticity, and presents it selectively
    to a third-party auditor. Later, Alice revokes the credential,
    and the auditor can detect the revocation.

Concepts demonstrated:
    - Identity creation (Inception Event)
    - Key Event Log (KEL) inspection
    - Transaction Event Log (TEL) — Registry lifecycle
    - Credential issuance (ACDC) with recipient binding
    - Digital signatures (sign / verify)
    - Out-of-Band Introduction (OOBI) via Card
    - Selective disclosure (Presentation)
    - Credential verification & revocation
"""

import pytest
import requests_mock

from keriac.agents import Identity
from keriac.documents import Credential, Presentation
from keriac.logbook.transactions import TransactionLog


def _export_kel_messages(identity):
    """
    Export the full messagized KEL (all events + attached signatures).
    Simulates what an OOBI endpoint would serve over HTTP.
    """
    from keri.core.counting import Counter, Codens
    from keri.db.dbing import dgKey, snKey

    pre = identity._hab.pre
    msg = bytearray()

    sn = 0
    while True:
        dig = identity._hab.db.getKeLast(key=snKey(pre=pre, sn=sn))
        if dig is None:
            break

        key = dgKey(pre=pre, dig=bytes(dig))
        evt_bytes = bytes(identity._hab.db.getEvt(key=key))
        sig_bytes_list = identity._hab.db.getSigs(key=key)

        counter = Counter(code=Codens.ControllerIdxSigs, count=len(sig_bytes_list))

        msg.extend(evt_bytes)
        msg.extend(counter.qb64b)
        for sig in sig_bytes_list:
            msg.extend(sig)

        sn += 1

    return bytes(msg)


class TestAliceSendsThankYouToBob:
    """
    A single cohesive user story covering the full keriac lifecycle.
    """

    def test_full_story(self):
        """
        The complete story of Alice issuing a ThankYou certificate to Bob,
        Bob verifying it via OOBI, presenting it selectively, and Alice
        eventually revoking it.
        """

        # ================================================================
        # ACT 1: Genesis — Identity Creation
        # ================================================================
        #
        # Both Alice and Bob create their KERI identities.
        # Each identity has a unique AID, a keypair, and a Key Event Log.
        #

        alice = Identity(name="alice_e2e", temp=True)
        bob = Identity(name="bob_e2e", temp=True)

        # Each identity has a unique Autonomous Identifier (AID)
        assert alice.aid != bob.aid
        assert str(alice.aid).startswith("B") or str(alice.aid).startswith("D") or str(alice.aid).startswith("E")

        # Every new identity starts with an Inception Event in its KEL
        alice_kel = list(alice.kel)
        assert len(alice_kel) == 1
        assert alice_kel[0].event_type == "icp"  # inception

        # Both are controllers (they own private keys)
        assert alice.is_controller is True
        assert bob.is_controller is True

        # ================================================================
        # ACT 2: Trust Infrastructure — Registry & Schema
        # ================================================================
        #
        # Alice creates a Verifiable Data Registry (VDR) to track the
        # lifecycle of her credentials. This anchors a TEL inception
        # event into her KEL, establishing a verifiable trust chain.
        #

        log = alice.create_transaction_log(name="alice_thankyou_log")

        # The log has been anchored in Alice's KEL
        assert isinstance(log, TransactionLog)
        assert log.log_aid is not None

        alice_kel = list(alice.kel)
        assert len(alice_kel) == 2  # icp + ixn (registry anchor)
        assert alice_kel[-1].event_type == "ixn"

        # The anchor seal references the log
        anchor = alice_kel[-1].anchors[0]
        assert anchor["i"] == log.log_aid

        # ================================================================
        # ACT 3: Credential Issuance — The ThankYou Certificate
        # ================================================================
        #
        # Alice issues a ThankYou ACDC credential to Bob.
        # The credential is:
        #   - Bound to Bob as recipient
        #   - Anchored in Alice's KEL via an interaction event
        #   - Tracked in Alice's Registry (TEL)
        #

        thank_you_data = {
            "message": "Thank you for your outstanding contribution to the team!",
            "project": "KERI Wrapper Library",
            "category": "Technical Excellence",
            "date": "2026-02-11",
        }

        credential = alice.issue_credential(
            data=thank_you_data,
            transaction_log=log,
            recipient=bob.aid,
            schema="EThankYouSchema_v1",
        )

        # The credential is a proper ACDC
        assert isinstance(credential, Credential)
        assert credential.issuer == alice.aid
        assert credential.recipient == bob.aid
        assert log.status(credential) != "Revoked"

        # Verify the attributes are embedded
        attrs = credential.attributes
        assert attrs["message"] == "Thank you for your outstanding contribution to the team!"
        assert attrs["project"] == "KERI Wrapper Library"

        # The issuance event is anchored in Alice's KEL
        alice_kel = list(alice.kel)
        assert len(alice_kel) == 3  # icp + log + issuance

        # ================================================================
        # ACT 4: Digital Signature — Alice Signs a Message for Bob
        # ================================================================
        #
        # Alice signs a personal message for Bob. This demonstrates
        # the fundamental asymmetric cryptography of KERI.
        #

        personal_note = b"Congratulations Bob! You've been awesome."
        signature = alice.sign(personal_note)

        # Alice can verify her own signature
        assert alice.verify(personal_note, signature) is True

        # Tampering is detected
        assert alice.verify(b"Tampered message", signature) is False

        # Bob cannot verify it yet — he doesn't know Alice's public key
        # He needs to discover Alice via OOBI first...

        # ================================================================
        # ACT 5: Discovery — Bob Resolves Alice via OOBI Card
        # ================================================================
        #
        # Bob has never interacted with Alice before. He receives a Card
        # (OOBI URL) that points to Alice's KEL. By resolving the Card,
        # Bob obtains a Remote view of Alice's identity — enough to
        # verify signatures and credentials, but no private keys.
        #

        # Alice publishes her Card (Out-of-Band Introduction)
        alice_card = alice.create_card()
        assert "oobi" in alice_card.url
        assert str(alice.aid) in alice_card.url

        # Export Alice's full KEL (all events + signatures)
        # In production, this would be served by Alice's OOBI endpoint
        alice_kel_stream = _export_kel_messages(alice)

        # Bob resolves the Card (simulated via HTTP mock)
        with requests_mock.Mocker() as m:
            m.get(
                alice_card.url,
                content=alice_kel_stream,
                headers={"Content-Type": "application/json+cesr"},
            )

            # Bob discovers Alice
            alice_from_bob = alice_card.resolve(name="alice_discovered_by_bob")

        # Bob now has a Remote view of Alice
        assert alice_from_bob.aid == alice.aid
        assert alice_from_bob.is_controller is False  # Remote — no private keys

        # Remote identities cannot sign (security invariant)
        with pytest.raises(ValueError, match="Cannot sign with Remote Identity"):
            alice_from_bob.sign(b"attempt")

        # Remote identities cannot create cards (security invariant)
        with pytest.raises(ValueError, match="Cannot issue Card for Remote Identity"):
            alice_from_bob.create_card()

        # ================================================================
        # ACT 6: Verification — Bob Verifies Alice's Signature
        # ================================================================
        #
        # Now that Bob has Alice's public key (via OOBI resolution),
        # he can verify that the personal note truly came from Alice.
        #

        # Bob verifies the signature using his resolved view of Alice
        assert alice_from_bob.verify(personal_note, signature) is True

        # Tampering is still detected
        assert alice_from_bob.verify(b"Tampered message", signature) is False

        # ================================================================
        # ACT 7: Presentation — Bob Presents the Certificate
        # ================================================================
        #
        # Bob wants to show his ThankYou certificate to an auditor,
        # but he only wants to disclose specific fields (selective
        # disclosure). He creates a Presentation that reveals the
        # message and category, but hides the project name.
        #

        # Full presentation (all fields visible)
        full_presentation = Presentation(credential, transaction_log=log)
        assert "message" in full_presentation.attributes
        assert "project" in full_presentation.attributes
        assert "category" in full_presentation.attributes
        assert "date" in full_presentation.attributes

        # Selective disclosure — hide the project
        selective_presentation = Presentation(credential, transaction_log=log, disclose_fields=["message", "category"])
        assert "message" in selective_presentation.attributes
        assert "category" in selective_presentation.attributes
        assert "project" not in selective_presentation.attributes
        assert "date" not in selective_presentation.attributes
        assert len(selective_presentation.disclosed_fields) == 2

        # The presentation can be serialized for transmission
        import json
        presentation_json = selective_presentation.to_json()
        parsed = json.loads(presentation_json)
        assert parsed["disclosed_fields"] == ["message", "category"]

        # ================================================================
        # ACT 8: Credential Verification — Auditor Checks Validity
        # ================================================================
        #
        # The auditor (using Alice's identity) verifies the presentation.
        # This checks cryptographic integrity (SAID) and revocation status.
        #

        # Full presentation verification passes
        assert full_presentation.verify() is True

        # ================================================================
        # ACT 9: Revocation — Alice Withdraws the Certificate
        # ================================================================
        #
        # Circumstances change. Alice revokes the ThankYou credential.
        # The revocation is anchored in her KEL and tracked in the TEL.
        #

        alice.revoke_credential(credential, transaction_log=log)

        # The credential is now revoked
        assert log.status(credential) == "Revoked"

        # Revocation is anchored in Alice's KEL
        alice_kel = list(alice.kel)
        assert len(alice_kel) == 4  # icp + log + issuance + revocation
        assert alice_kel[-1].event_type == "ixn"

        # Verification now fails due to revocation
        assert full_presentation.verify() is False

        # ================================================================
        # EPILOGUE: Cleanup
        # ================================================================

        alice_from_bob.close()
        alice.close()
        bob.close()

    def test_portability_and_anchoring(self):
        """
        ACT 10: Portability — Shipping the Trust Chain in a File
        ========================================================
        
        Alice wants to send her 'credentials package' to Charlie 
        as a single .cesr file. Charlie will read the file from disk,
        unpack it, verify everything, and anchor the ACDC.
        """
        import os
        from keriac.transport import pack, unpack
        from keriac.domain import Signature, PublicKey

        alice = Identity(name="alice_portability", temp=True)
        charlie = Identity(name="charlie_portability", temp=True)
        
        # 1. Alice creates trust infrastructure
        log = alice.create_transaction_log(name="charity_log")
        
        # 2. Alice issues ACDC for Charlie
        award_data = {"score": "A+", "subject": "KERI Portability"}
        acdc = alice.issue_credential(
            data=award_data,
            transaction_log=log,
            recipient=charlie.aid,
            schema="EAwardSchema"
        )
        
        # 3. Alice signs the ACDC directly
        # This provides a "direct proof" in addition to the "chained proof" (KEL anchor)
        sig = acdc.sign(alice)

        # 4. Alice bundles everything for Charlie
        # We pack: KEL (inception), TEL (inception + issuance), ACDC, and its Signature
        kel_events = list(alice.kel) 
        tel_events = list(log.tel)
        
        bundle = pack([
            *kel_events,     # Alice's KEL
            *tel_events,     # Registry TEL
            acdc,            # The ACDC
            sig              # The ACDC's direct signature
        ])
        
        # 5. Save to file system
        file_path = "alice_to_charlie.cesr"
        with open(file_path, "wb") as f:
            f.write(bundle)
            
        try:
            # 6. Charlie reads the file
            assert os.path.exists(file_path)
            with open(file_path, "rb") as f:
                received_bundle = f.read()
                
            # 7. Charlie unpacks the stream
            objects = unpack(received_bundle)
            
            # 8. Charlie verifies the pieces
            # Verify ACDC integrity (SAID check)
            received_acdc = next(obj for obj in objects if isinstance(obj, Credential))
            assert received_acdc.said == acdc.said
            assert received_acdc.verify() is True

            # Verify the direct signature on the ACDC
            # Charlie finds the signature in the objects list
            received_sig = next(obj for obj in objects if isinstance(obj, Signature))
            
            # Charlie uses Alice's public key (resolved from KEL) to verify the signature
            alice_pub = alice.public_key 
            assert received_acdc.verify_signature(received_sig, alice_pub) is True
            
            # 9. Charlie anchors the ACDC in his own KEL to acknowledge receipt
            charlie.anchor(received_acdc)
            assert charlie.kel.is_anchored(received_acdc.said) is True
            
        finally:
            alice.close()
            charlie.close()

    def test_cbor_portability(self):
        """
        ACT 11: Binary Efficiency — Shipping the Trust Chain in CBOR
        ============================================================
        
        Same as ACT 10, but everything is encoded in CBOR to save space.
        This demonstrates keriac's ability to handle mixed binary streams.
        """
        import os
        from keriac.transport import pack, unpack
        from keriac.domain import Signature
        from keriac.documents.credential import Credential

        # 1. Alice creates identity with CBOR default
        alice = Identity(name="alice_cbor", temp=True, kind="CBOR")
        charlie = Identity(name="charlie_cbor", temp=True)
        
        # 2. Alice creates trust infrastructure using CBOR
        log = alice.create_transaction_log(name="charity_log_cbor", kind="CBOR")
        
        # 3. Alice issues ACDC for Charlie in CBOR
        award_data = {"score": "A+", "subject": "CBOR KERI"}
        acdc = alice.issue_credential(
            data=award_data,
            transaction_log=log,
            recipient=charlie.aid,
            schema="EAwardSchema",
            kind="CBOR"
        )
        
        # 4. Alice signs the ACDC
        sig = acdc.sign(alice)

        # 5. Alice bundles everything (All CBOR)
        kel_events = list(alice.kel) 
        tel_events = list(log.tel)
        
        bundle = pack([
            *kel_events,     # Alice's KEL (CBOR)
            *tel_events,     # Registry TEL (CBOR)
            acdc,            # The ACDC (CBOR)
            sig              # The Signature
        ])
        
        # Verify the bundle contains mixed content
        assert b"CBOR" in bundle
        assert b"JSON" in bundle  # Alice's KEL is still JSON by keripy default
        
        # 6. Save to file
        file_path = "alice_cbor.cesr"
        with open(file_path, "wb") as f:
            f.write(bundle)
            
        try:
            # 7. Charlie reads and unpacks
            with open(file_path, "rb") as f:
                received_bundle = f.read()
                
            objects = unpack(received_bundle)
            
            # 8. Charlie verifies
            received_acdc = next(obj for obj in objects if isinstance(obj, Credential))
            assert received_acdc.said == acdc.said
            # The ACDC should internally use CBOR
            assert received_acdc.data["v"].startswith("ACDC10CBOR")
            
            # Verify signature using Alice's key
            received_sig = next(obj for obj in objects if isinstance(obj, Signature))
            assert received_acdc.verify_signature(received_sig, alice.public_key) is True
            
        finally:
            # if os.path.exists(file_path):
            #     os.remove(file_path)
            alice.close()
            charlie.close()
