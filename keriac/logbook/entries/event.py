from keriac.const import Fields
from keriac.domain import SAD, AID, SAID, EventDict, PublicKey
from keri.core import coring, serdering

class Event(SAD):
    """
    Academic wrapper for all KERI events.
    Uses __new__ as a factory to return specific subclasses (icp, ixn, rot, etc.).
    """

    def __new__(cls, sad_or_raw):
        """
        Factory logic to return the appropriate Event subclass.
        """
        if isinstance(sad_or_raw, Event):
            serder = sad_or_raw._serder
        elif isinstance(sad_or_raw, dict):
            serder = serdering.SerderKERI(sad=sad_or_raw)
        elif isinstance(sad_or_raw, (bytes, bytearray, memoryview)):
            serder = serdering.SerderKERI(raw=bytes(sad_or_raw))
        elif hasattr(sad_or_raw, 'sad'): # Likely a keri Serder
            serder = sad_or_raw
        else:
            raise ValueError(f"Unsupported type for Event initialization: {type(sad_or_raw)}")
            
        # Determine the correct subclass based on ilk
        ilk = serder.ilk
        if ilk == coring.Ilks.icp:
            subclass = InceptionEvent
        elif ilk == coring.Ilks.dip:
            subclass = DelegatedInceptionEvent
        elif ilk in (coring.Ilks.rot, coring.Ilks.drt):
            subclass = RotationEvent
        elif ilk == coring.Ilks.ixn:
            subclass = InteractionEvent
        else:
            subclass = Event
            
        instance = super(Event, cls).__new__(subclass)
        instance._serder = serder
        return instance

    def __init__(self, sad_or_raw):
        """
        Initialize the event instance. 
        Note: __new__ already handles _serder assignment.
        """
        pass

    @classmethod
    def deserialize(cls, raw: bytes) -> "Event":
        """Reconstruct the event from bytes using factory logic."""
        return cls(raw)

    @property
    def data(self) -> EventDict:
        """The internal dictionary representation (SAD) of the event."""
        return self._serder.sad

    @property
    def said(self) -> SAID:
        """The Self-Addressing Identifier (SAID) of the event."""
        return SAID(self._serder.said)

    @property
    def raw(self) -> bytes:
        """The raw bytes serialization of the event (CESR)."""
        return self._serder.raw

    @property
    def aid(self) -> AID:
        """The Autonomous Identifier (AID) associated with this event."""
        return AID(self.data[Fields.PREFIX])

    @property
    def sequence(self) -> int:
        """The sequence number of the event."""
        return int(self.data[Fields.SEQUENCE], 16)

    @property
    def event_type(self) -> str:
        """The message type (ilk) of the event."""
        return self.data[Fields.TYPE]

    @property
    def prior(self) -> str:
        """The digest of the prior event."""
        return self.data[Fields.PRIOR]

    @property
    def anchors(self) -> list:
        """Return the list of seals (anchors) in this event if any."""
        return self.data.get(Fields.SEALS, [])

class InceptionEvent(Event):
    """Represents an Inception Event (icp) or Delegated Inception Event (dip)."""
    def __repr__(self):
        return f"InceptionEvent(aid='{self.aid}', sequence={self.sequence})"

class DelegatedInceptionEvent(InceptionEvent):
    """
    Represents a Delegated Inception Event (dip).
    
    A delegated identifier owes its existence to a delegator identifier.
    The inception event of the delegate is anchored in the KEL of the delegator.
    """
    
    @property
    def delegator(self) -> AID:
        """
        The AID of the delegator.
        
        Returns:
            AID: The delegator's identifier.
        """
        return AID(self.data.get('di'))

    def __repr__(self):
        return f"DelegatedInceptionEvent(aid='{self.aid}', delegator='{self.delegator}', sequence={self.sequence})"


class RotationEvent(Event):
    """
    Key Rotation Event - represents a cryptographic key rotation.
    
    In KERI, rotation events allow changing keys while maintaining
    identifier continuity. The previous keys are rotated away from,
    and new keys become current.
    """
    
    @property
    def public_keys(self):
        """
        Get the public keys established by this rotation.
        
        These are the keys that become current after this rotation event
        is accepted into the KEL.
        
        Returns:
            List[PublicKey]: The new current public keys.
        """
        # KERI stores the new current keys in the rotation event's verfers
        verfers = self._serder.verfers
        return [PublicKey(v.qb64) for v in verfers]
    
    @property
    def next_key_commitments(self):
        """
        Get the next key commitments (pre-rotation digests).
        
        These are cryptographic commitments (hashes) to the keys that
        will be used in the NEXT rotation. This is KERI's pre-rotation
        security mechanism - even if current keys are compromised, an
        attacker cannot rotate without knowing the pre-committed next keys.
        
        Returns:
            List[str]: qb64 digests of next keys.
        """
        # In KERI, 'n' is the field for next key digests
        return self._serder.sad.get('n', [])
    
    def __repr__(self):
        return f"RotationEvent(aid='{self.aid}', sequence={self.sequence})"

class InteractionEvent(Event):
    """Represents an Interaction Event (ixn)."""
    @classmethod
    def deserialize(cls, raw: bytes) -> "Event":
        """Reconstruct the event from bytes using factory logic."""
        return cls(raw)

    def __repr__(self):
        return f"InteractionEvent(aid='{self.aid}', sequence={self.sequence})"
