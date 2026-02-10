from .const import Fields
from .base import SAD, AID
from .types import EventDict
from keri.core import coring, serdering

class Event(SAD):
    """
    Base class for all KERI events.
    Uses __new__ as a factory to return specific subclasses.
    """

    def __new__(cls, sad_or_raw):
        """
        Factory logic to return the appropriate Event subclass.
        """
        # Unwrap SAD instance if provided
        if isinstance(sad_or_raw, SAD):
            serder = sad_or_raw._sad
        elif isinstance(sad_or_raw, dict):
            serder = serdering.SerderKERI(sad=sad_or_raw)
        elif isinstance(sad_or_raw, (bytes, bytearray, memoryview)):
            serder = serdering.SerderKERI(raw=bytes(sad_or_raw))
        elif hasattr(sad_or_raw, 'sad'): # Likely a Serder
            serder = sad_or_raw
        else:
            raise ValueError(f"Unsupported type for Event initialization: {type(sad_or_raw)}")
            
        # Determine the correct subclass based on ilk
        ilk = serder.ilk
        if ilk in (coring.Ilks.icp, coring.Ilks.dip):
            subclass = InceptionEvent
        elif ilk in (coring.Ilks.rot, coring.Ilks.drt):
            subclass = RotationEvent
        elif ilk == coring.Ilks.ixn:
            subclass = InteractionEvent
        else:
            subclass = Event
            
        instance = super(Event, cls).__new__(subclass)
        return instance

    def __init__(self, sad_or_raw):
        """
        Initialize the event instance.
        """
        # SAD.__init__ handles the heavy lifting of wrapping into _sad
        if isinstance(sad_or_raw, SAD):
            super().__init__(sad_or_raw._sad)
        else:
            super().__init__(sad_or_raw)

    @property
    def data(self) -> EventDict:
        """The internal dictionary representation (SAD) of the object."""
        return super().data

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

class InceptionEvent(Event):
    """Represents an Inception Event (icp) or Delegated Inception Event (dip)."""
    def __repr__(self):
        return f"InceptionEvent(aid='{self.aid}', sequence={self.sequence})"

class RotationEvent(Event):
    """Represents a Rotation Event (rot) or Delegated Rotation Event (drt)."""
    def __repr__(self):
        return f"RotationEvent(aid='{self.aid}', sequence={self.sequence})"

class InteractionEvent(Event):
    """Represents an Interaction Event (ixn)."""
    @property
    def anchors(self) -> list:
        """Return the list of seals (anchors) in this interaction event."""
        return self.data.get(Fields.SEALS, [])

    def __repr__(self):
        return f"InteractionEvent(aid='{self.aid}', sequence={self.sequence})"
