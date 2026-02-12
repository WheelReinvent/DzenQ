from keri.vdr import eventing

from .. import AID, Seal
from ..documents.credential import Credential

class TransactionLog:
    """
    Verifiable Data Registry (VDR) implementation.
    
    Manages the Transaction Event Log (TEL) for credentials.
    Adheres to KERI's VDR event structure:
    - vcp: Inception (Registry Creation)
    - iss: Issuance (Credential Issued)
    - rev: Revocation (Credential Revoked)
    
    This class abstracts the complex KERI VDR logic into a simple API.
    """

    def __init__(self, issuer_aid: AID, name: str):
        """
        Initialize a TransactionLog wrapper.

        Args:
            issuer (Identity): The Identity that controls this registry.
            name (str): Human-readable alias for this registry.
        """
        self.issuer_aid = issuer_aid
        self.name = name
        self.log_aid = None # Assigned after commit()
        self._revoked_credentials = set() # In-memory mock DB

    def commit(self) -> Seal:
        """
        Create the Registry Inception Event (vcp) and anchor it.
        
        This establishes the registry on the ledger (KEL).
        
        Returns:
            str: The Registry AID (reg_k).
        """
        # 1. Generate vcp event
        # 'pre' is the issuer's identifier prefix
        # We assume a default configuration for now (no backers logic exposed yet)
        serder = eventing.incept(pre=self.issuer_aid)
        
        self.log_aid = serder.pre

        return {
            "i": self.log_aid,
            "s": "{:x}".format(0),  # Inception is always sn 0
            "d": serder.said
        }


    def issue(self, credential: Credential) -> Seal:
        """
        Issue a credential against this registry.
        
        Generates an Issuance (iss) event and anchors it.

        Args:
            credential (Credential): The credential to issue.

        Returns:
            str: The said of the issuance event.
        """
        if not self.log_aid:
            raise ValueError("Registry not committed. Call commit() first.")

        # 1. Generate iss event
        # vcdig is the SAID of the credential
        serder = eventing.issue(
            vcdig=str(credential.said),
            regk=self.log_aid
        )

        return {
            "i": self.log_aid,
            "s": serder.sn,  # hex string
            "d": serder.said
        }


    # TODO disallow direct call. Only via Identity.revoke_credential() to ensure proper checks and flow
    def revoke(self, credential: Credential) -> Seal:
        """
        Revoke a credential.
        
        Generates a Revocation (rev) event and anchors it.
        
        Args:
            credential (Credential): The credential to revoke.
            
        Returns:
            str: The said of the revocation event.
        """
        if not self.log_aid:
            raise ValueError("Registry not committed. Call commit() first.")

        # For revocation, we need the *previous* event digest in the TEL usually.
        # However, vdr.eventing.revoke takes 'dig' which is "digest of previous event qb64".
        # In a simplified flow, if we treat each TEL event as anchored in KEL, 
        # tracking the strict TEL chain might be complex without a database.
        # 
        # CRITICAL: keri.vdr.eventing.revoke requires 'dig' (previous event in TEL).
        # For a simple 'iss' -> 'rev' flow, the previous event is the 'iss' event.
        # We need to regenerate the 'iss' event to get its digest, OR store checking logic.
        # 
        # SIMPLIFICATION: We will re-generate the issuance serder to get its digest.
        # This assumes the credential hasn't been revoked/rotated multiple times.
        # ideally we would query the database.
        
        # Re-derive issue event to get its digest
        iss_serder = eventing.issue(vcdig=str(credential.said), regk=self.log_aid)
        prev_dig = iss_serder.said

        # 1. Generate rev event
        serder = eventing.revoke(
            vcdig=str(credential.said),
            regk=self.log_aid,
            dig=prev_dig
        )

        # Mark as revoked in memory
        self._revoked_credentials.add(str(credential.said))

        credential.status = "revoked"
        
        return {
            "i": self.log_aid,
            "s": serder.sn,
            "d": serder.said
        }

    def status(self, credential: Credential) -> str:
        """
        Check the status of a credential.
        
        Note: Without a persistent database query, this is a mock/logical check 
        based on available info. In a real system, this would query the DB.
        
        Returns:
            str: 'Issued' or 'Revoked' (Simulated)
        """
        if str(credential.said) in self._revoked_credentials:
            return "Revoked"
        return "Issued"
