from .base import SAD
from .aid import AID
from keri.core import coring, serdering

class Event(SAD):
    """
    Base class for all KERI events.
    Uses __new__ as a factory to return specific subclasses.
    """

    def __new__(cls, serder_or_raw):
        """
        Factory logic to return the appropriate Event subclass.
        """
        if isinstance(serder_or_raw, (bytes, bytearray, memoryview)):
            serder = serdering.SerderKERI(raw=bytes(serder_or_raw))
        else:
            serder = serder_or_raw
            
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

    def __init__(self, serder_or_raw):
        """
        Initialize the event instance.
        """
        if isinstance(serder_or_raw, (bytes, bytearray, memoryview)):
            serder = serdering.SerderKERI(raw=bytes(serder_or_raw))
        else:
            serder = serder_or_raw
        super().__init__(serder)

    @property
    def aid(self) -> AID:
        """The Autonomous Identifier (AID) associated with this event."""
        return AID(self._serder.pre)

    @property
    def sequence(self) -> int:
        """The sequence number of the event."""
        return int(self._serder.sn)

    @property
    def event_type(self) -> str:
        """The message type (ilk) of the event."""
        return self._serder.ilk

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
    def __repr__(self):
        return f"InteractionEvent(aid='{self.aid}', sequence={self.sequence})"
