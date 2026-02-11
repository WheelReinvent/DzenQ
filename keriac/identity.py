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

    def __init__(self, name: str, **kwargs):
        """
        Initialize an Identity environment.
        
        Args:
            name (str): The human-readable alias for this identity.
            **kwargs: Additional parameters passed to the underlying Hab.
        """
        # We'll use Habery to manage the habitats.
        self._hby = habbing.Habery(name=name, temp=True)
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
    
    def rotate(self, *, data=None, **kwargs) -> Event:
        """
        Rotate the identity's cryptographic keys.
        
        This is KERI's core security feature - rotating keys while maintaining
        identifier continuity. The new keys are automatically generated and
        committed via pre-rotation (next key commitments).
        
        Args:
            data: Optional data to anchor in the rotation event.
                  Can be a string, dict, SAD object, or list of seal dicts.
            **kwargs: Advanced parameters (witness configuration, thresholds)
                     Reserved for future witness/multi-sig support.
            
        Returns:
            Event: The rotation event containing the key change.
            
        Example:
            >>> alice = Identity(name="alice")
            >>> old_key = alice.public_key
            >>> rotation = alice.rotate(data="Upgrading to quantum-resistant keys")
            >>> new_key = alice.public_key
            >>> assert alice.aid == original_aid  # AID unchanged
            >>> assert new_key != old_key  # Keys rotated
        """
        # Prepare seal data (same logic as anchor())
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
        
        # Perform rotation using Hab's rotate method
        raw = self._hab.rotate(data=seals)
        return Event(raw)

    def close(self):
        """Close the underlying database and resources."""
        self._hby.close()

    def __repr__(self):
        return f"Identity(alias='{self._hab.name}', aid='{self.aid}')"
