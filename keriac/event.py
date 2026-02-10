from .base import SAD
from .aid import AID
from keri.core import coring, serdering

class Event(SAD):
    """
    Base class for all KERI events.
    Inherits from SAD for SAID and serialization handling.
    """

    @property
    def aid(self) -> AID:
        """The Autonomous Identifier (AID) associated with this event."""
        return AID(self._serder.pre)

    @property
    def sn(self) -> int:
        """The sequence number of the event."""
        return int(self._serder.sn)

    @property
    def ilk(self) -> str:
        """The message type (ilk) of the event."""
        return self._serder.ilk

    @classmethod
    def create(cls, serder):
        """
        Factory method to create the appropriate Event subclass based on ilk.
        Can accept a Serder or raw bytes/bytearray.
        """
        if isinstance(serder, (bytes, bytearray)):
            serder = serdering.SerderKERI(raw=bytes(serder))
            
        ilk = serder.ilk
        if ilk in (coring.Ilks.icp, coring.Ilks.dip):
            return InceptionEvent(serder)
        elif ilk in (coring.Ilks.rot, coring.Ilks.drt):
            return RotationEvent(serder)
        elif ilk == coring.Ilks.ixn:
            return InteractionEvent(serder)
        else:
            return Event(serder)

class InceptionEvent(Event):
    """Represents an Inception Event (icp) or Delegated Inception Event (dip)."""
    def __repr__(self):
        return f"InceptionEvent(aid='{self.aid}', sn={self.sn})"

class RotationEvent(Event):
    """Represents a Rotation Event (rot) or Delegated Rotation Event (drt)."""
    def __repr__(self):
        return f"RotationEvent(aid='{self.aid}', sn={self.sn})"

class InteractionEvent(Event):
    """Represents an Interaction Event (ixn)."""
    def __repr__(self):
        return f"InteractionEvent(aid='{self.aid}', sn={self.sn})"
