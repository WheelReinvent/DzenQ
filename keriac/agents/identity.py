from typing import Union, List, Any
from keri.app import habbing

from keriac.domain import AID, PublicKey, Signature
from keriac.logbook.entries.event import Event
from keriac.logbook.keys import KeyLog
from keriac.logbook.transactions import TransactionLog
from keriac.documents.credential import Credential

class Identity:
    """
    Identity represents a KERI Autonomous Identifier (AID) entity.
    It manages the underlying Hab (Habitat) and database.
    """

    def __init__(self, name: str, *, salt: str = None, bran: str = None, tier: str = None, base: str = "", temp: bool = True, **kwargs):
        """
        Initialize an Identity environment.
        
        KERI Key Management Note:
        A KERI identity is derived from a secret (seed or passphrase).
        - If 'salt' is provided, it's used as the qb64 salt (seed) for key derivation.
        - If 'bran' is provided, it's used as a Base64 passphrase/salt material.
        - If neither is provided, a random one is generated.
        
        Args:
            name (str): The human-readable alias for this identity.
            salt (str, optional): qb64 salt (seed) for key derivation.
            bran (str, optional): Passphrase/salt material (at least 21 chars).
            tier (str, optional): Security tier (low, med, high).
            base (str, optional): Directory prefix for database isolation.
            temp (bool, optional): Whether to use temporary storage (default True).
            **kwargs: Additional parameters passed to the underlying Hab.
        """
        # We'll use Habery to manage the habitats.
        self._hby = habbing.Habery(name=name, temp=temp, salt=salt, bran=bran, tier=tier, base=base)
        self._hab = self._hby.makeHab(name=name, **kwargs)
        self._aid = None  # Explicit AID override (for Remote identities)

    @property
    def aid(self) -> AID:
        """The Autonomous Identifier (AID) of this entity (qb64)."""
        if self._aid:
            return AID(self._aid)
        return AID(self._hab.pre)

    @property
    def is_controller(self) -> bool:
        """
        Check if this Identity is a Controller (has private keys).
        
        Returns:
            bool: True if we control this Identity, False if Remote/Observer.
        """
        return self._hab is not None

    def create_card(self, role: str = "controller") -> 'Card':
        """
        Create a Card (OOBI) for this Identity.
        
        Args:
            role (str): The role for the OOBI (default: "controller").
            
        Returns:
            Card: A Card instance containing the OOBI URL.
            
        Raises:
            ValueError: If this is a Remote Identity (no keys).
        """
        from keriac.agents.contact import Card
        return Card.issue(self, role=role)


    def anchor(self, data=None, **kwargs) -> Event:
        """
        Anchor data into the Key Event Log (KEL).
        
        This method creates an Interaction Event (ixn) and anchors the provided 
        data into it. It abstracts away the KERI technicalities of seals.

        Args:
            data (any): The data to anchor. 
                        - If it's a string, it will be anchored as {"msg": data}.
                        - If it's a dict, it will be anchored as-is.
                        - If it's a SAD (e.g. ACDC), it will anchor its SAID.
                        - If it's a list, it's used as-is (must be a list of seal dicts).
            **kwargs: Shortcut for anchoring a single dictionary of key-value pairs.
        
        Returns:
            Event: The resulting interaction event.
        """
        
        seals = []
        if data is not None:
            if isinstance(data, str):
                seals.append({"msg": data})
            elif isinstance(data, dict):
                seals.append(data)
            elif isinstance(data, list):
                seals = data
            elif hasattr(data, "said"):  # SAD objects
                seals.append({"d": str(data.said)})
            else:
                raise ValueError(f"Unsupported data type for anchoring: {type(data)}")
        
        if kwargs:
            seals.append(kwargs)
            
        raw = self._hab.interact(data=seals)
        return Event(raw)

    @property
    def key_log(self) -> KeyLog:
        """Access the Key Event Log (KEL) for this identity."""
        return KeyLog(self._hab)
    
    @property
    def kel(self) -> KeyLog:
        """Alias for key_log."""
        return self.key_log
    
    def sign(self, data: bytes) -> 'Signature':
        """
        Sign arbitrary data with this identity's current signing key.
        
        Only available for Controller identities (not Remote).
        
        Args:
            data: The bytes to sign.
            
        Returns:
            Signature: The cryptographic signature.
            
        Raises:
            ValueError: If this is a Remote identity (no keys).
        """
        if not self.is_controller:
            raise ValueError("Cannot sign with Remote Identity (no private keys)")
        
        # Use Hab's sign method which returns a list of Sigers
        sigers = self._hab.sign(ser=data)
        # Return the first signature
        return Signature(sigers[0].qb64)
    
    def verify(self, data: bytes, signature: 'Signature') -> bool:
        """
        Verify that data was signed by this identity's CURRENT authorized key.
        
        This is the fundamental security check in KERI. Even if an old key 
        mathematically verifies a signature, this method will return False 
        if that key has been rotated away.
        
        Works for both Controller and Remote identities.
        
        Args:
            data: The data that was signed.
            signature: The signature to verify.
            
        Returns:
            bool: True if signature is valid and key is current.
        """
        return self.public_key.verify(data, signature)
    
    @property
    def public_key(self) -> 'PublicKey':
        """
        Get the current public key for this identity.
        
        Works for both Controller and Remote identities.
        
        Returns:
            PublicKey: The current verification key.
        """
        # Get the current public key from the KEL
        # For Remote identities, we use kevers; for Controllers, we use kever
        if self.is_controller:
            keri_verfer = self._hab.kever.verfers[0]
        else:
            # Remote identity: look up in kevers
            kever = self._hby.db.kevers.get(str(self.aid))
            if not kever:
                raise ValueError(f"No KEL found for Remote Identity {self.aid}")
            keri_verfer = kever.verfers[0]
        return PublicKey(keri_verfer.qb64)
    
    def delegate(self, name: str, **kwargs) -> 'Identity':
        """
        Create a new delegated identifier anchored to this identity.

        This methods creates a new Identity whose inception is delegated
        by the current Identity. This establishes a hierarchical trust chain.

        The Delegation Process:
        1. A new 'delegate' Identity is created with 'delpre' set to this Identity's AID.
        2. This generates a Delegated Inception Event (dip).
        3. This Identity (delegator) anchors the 'dip' event in its own KEL.
           This step is CRITICAL: without it, the delegate is not valid.

        Args:
            name (str): The alias for the new delegated identity.
            **kwargs: Additional arguments for Identity creation (salt, etc.).

        Returns:
            Identity: The newly created and anchored delegated identity.
        """
        # 1. Create the delegate identity
        # We pass self.aid (qb64) as delpre
        delegate_identity = Identity(name=name, delpre=str(self.aid), **kwargs)

        # 2. Get the delegate's inception event
        # The identity init already created the event in its habitat
        delegate_event = list(delegate_identity.kel)[0]

        # 3. Anchor the delegate's inception in our KEL
        # We need to seal the delegate's inception event digest
        self.anchor(delegate_event)

        return delegate_identity

    def rotate(self, *, 
               data: Union['Seal', List['Seal']] = None, 
               witness_threshold: int = None,
               cuts: List[str] = None,
               adds: List[str] = None,
               current_threshold: Union[int, List[Any]] = None,
               next_threshold: Union[int, List[Any]] = None,
               **kwargs) -> Event:
        """
        Rotate the identity's cryptographic keys.
        
        This is KERI's core security feature - rotating keys while maintaining
        identifier continuity. 
        
        Key Management:
        - Keys are automatically generated from the Identity's seed/passphrase.
        - KERI uses "pre-rotation": you commit to the NEXT keys in the CURRENT event.
        - By default, this method handles the sequence automatically.
        
        Args:
            data: Optional data (Seals) to anchor in the rotation event.
                  Can be a single Seal dict, a list of Seals, or a SAD object.
            witness_threshold: New threshold for witness corroboration (bt).
            cuts: List of witness AIDs to remove.
            adds: List of witness AIDs to add.
            current_threshold: Signing threshold for current keys (kt).
            next_threshold: Signing threshold for next keys (nt).
            **kwargs: Advanced parameters passed to underlying rotate.
            
        Returns:
            Event: The rotation event containing the key change.
        """
        # Prepare seal data
        seals = []
        if data is not None:
            if isinstance(data, str):
                seals.append({"msg": data})
            elif isinstance(data, dict):
                seals.append(data)
            elif isinstance(data, list):
                seals = data
            elif hasattr(data, "said"):  # SAD objects
                seals.append({"d": str(data.said)})
            else:
                raise ValueError(f"Unsupported data type for rotation: {type(data)}")
        
        # KERI Hab.rotate uses specific param names
        # Mapping our user-friendly names to keripy params if needed
        # In keripy, rotate() takes: data, isith, nsith, toad, cuts, adds...
        
        raw = self._hab.rotate(
            data=seals,
            isith=current_threshold,
            nsith=next_threshold,
            toad=witness_threshold,
            cuts=cuts or [],
            adds=adds or [],
            **kwargs
        )
        return Event(raw)

    def create_transaction_log(self, name: str) -> 'TransactionLog':
        """
        Create a new Transaction Log (VDR) anchored to this identity.

        Args:
            name (str): The alias for the new transaction log.

        Returns:
            TransactionLog: The newly created and committed transaction log.
        """
        log = TransactionLog(issuer_aid=self.aid, name=name)

        seal = log.commit()

        # Anchor in Issuer's KEL
        # We seal the registry inception to authorize it
        # Using a SealEvent format: i=reg_k, s=sn, d=digest

        self.anchor(data=seal)
        return log


    def issue_credential(self, data: dict, transaction_log: TransactionLog, schema: Any = None, recipient: Any = None, **kwargs) -> 'Credential':
        """
        Issue a credential using the provided transaction log.

        This process:
        1. Creates a signed ACDC credential.
        2. Generates an issuance event (iss) in the transaction log.
        3. Anchors the issuance in this identity's KEL.

        Args:
            data (dict): The credential attributes.
            transaction_log (TransactionLog): The transaction log to issue against.
            schema (Schema, optional): The schema for the credential.
            recipient (str or AID, optional): The recipient's AID.
            **kwargs: Additional arguments for ACDC creation.

        Returns:
            Credential: The issued and anchored credential.
        """
        # 1. Create the ACDC
        # We pass the log AID as the 'status' field in the credential
        acdc = Credential.create(
            issuer_aid=self.aid,
            schema=schema,
            attributes=data,
            recipient=str(recipient) if recipient else None,
            status=str(transaction_log.log_aid),
            **kwargs
        )

        # 2. Issue against the transaction log (creates and anchors 'iss' event)
        seal = transaction_log.issue(credential=acdc)

        # 2. Anchor in Issuer's KEL
        # Seal the issuance
        self.anchor(data=seal)


        return acdc

    def revoke_credential(self, credential: 'Credential', transaction_log: TransactionLog) -> 'Credential':
        """
        Revoke a credential using its associated transaction log.

        This process:
        1. Generates a revocation event (rev) in the credential's transaction log.
        2. Anchors the revocation in this identity's KEL.

        Args:
            credential (Credential): The credential to revoke (must have transaction_log).

        Returns:
            Credential: The revoked credential (with updated status).
            :param credential:
            :param transaction_log:
        """
        # 1. Revoke in the transaction log (creates and anchors 'rev' event)
        seal = transaction_log.revoke(credential=credential)

        # 2. Anchor in Issuer's KEL
        self.anchor(data=seal)

        # 3. Update credential status for convenience
        credential.status = "revoked"

        return credential

    def close(self):
        """Close the underlying database and resources."""
        self._hby.close()

    def __repr__(self):
        return f"Identity(alias='{self._hab.name}', aid='{self.aid}')"
