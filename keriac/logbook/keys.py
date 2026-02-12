from typing import Iterator
from keriac.logbook.entries.event import Event, InteractionEvent
class KeyLog:
    """
    KeyLog (Key Event Log) provides an iterable interface to an identity's event history.
    """

    def __init__(self, hab):
        self._hab = hab

    def __iter__(self) -> Iterator[Event]:
        """Iterate over all events in the KEL from inception to latest."""
        # getEvtLastPreIter returns an iterator of raw bytes for each SN
        # (excluding superseded events, which is what 'Last' implies in KERI)
        for raw in self._hab.db.getEvtLastPreIter(self._hab.pre):
            yield Event(raw)

    def __len__(self) -> int:
        """Return the number of events in the KEL."""
        # The sequence number is 0-indexed, so we add 1 to the highest SN.
        return self._hab.kever.sn + 1

    def is_anchored(self, said: str) -> bool:
        """
        Check if the given SAID is anchored in this KEL.
        """
        said_str = str(said)
        for event in self:
            if isinstance(event, InteractionEvent):
                for anchor in event.anchors:
                    if anchor.get('d') == said_str:
                        return True
        return False

    def __repr__(self):
        return f"KeyLog(identity='{self._hab.name}', length={len(self)})"
