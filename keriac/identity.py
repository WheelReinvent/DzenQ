from typing import Union, List, Any
from keri.app import habbing

from .base import AID
from .event import Event
from .event_log import KEL
from .crypto import PublicKey, PrivateKey, Signature


class Identity:
    """
    Identity represents a KERI Autonomous Identifier (AID) entity.
    It manages the underlying Hab (Habitat) and database.
    """

    def __init__(self, name: str, *, salt: str = None, bran: str = None, tier: str = None, base: str = "", **kwargs):
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
            **kwargs: Additional parameters passed to the underlying Hab.
        """
        # We'll use Habery to manage the habitats.
        self._hby = habbing.Habery(name=name, temp=True, salt=salt, bran=bran, tier=tier, base=base)
        self._hab = self._hby.makeHab(name=name, **kwargs)

    @property
    def aid(self) -> AID:
        """The Autonomous Identifier (AID) of this entity (qb64)."""
        return AID(self._hab.pre)


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
    def kel(self) -> KEL:
        """Access the Key Event Log (KEL) for this identity."""
        return KEL(self._hab)
    
    def sign(self, data: bytes) -> Signature:
        """
        Sign arbitrary data with this identity's current signing key.
        
        Args:
            data: The bytes to sign.
            
        Returns:
            Signature: The cryptographic signature.
        """
        from .crypto import Signature
        # Use Hab's sign method which returns a list of Sigers
        sigers = self._hab.sign(ser=data)
        # Return the first signature
        return Signature(sigers[0].qb64)
    
    def verify(self, data: bytes, signature: Signature) -> bool:
        """
        Verify that data was signed by this identity's CURRENT authorized key.
        
        This is the fundamental security check in KERI. Even if an old key 
        mathematically verifies a signature, this method will return False 
        if that key has been rotated away.
        
        Args:
            data: The data that was signed.
            signature: The signature to verify.
            
        Returns:
            bool: True if signature is valid and key is current.
        """
        return self.public_key.verify(data, signature)
    
    @property
    def public_key(self) -> PublicKey:
        """
        Get the current public key for this identity.
        
        Returns:
            PublicKey: The current verification key.
        """
        # Get the current public key from the KEL
        keri_verfer = self._hab.kever.verfers[0]
        return PublicKey(keri_verfer.qb64)
    
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
        from .types import Seal
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

    def close(self):
        """Close the underlying database and resources."""
        self._hby.close()

    def __repr__(self):
        return f"Identity(alias='{self._hab.name}', aid='{self.aid}')"
