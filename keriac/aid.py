from .said import SAID

class AID(SAID):
    """
    Autonomous Identifier (AID).
    Representing the unique identifier of a KERI agent.
    An AID is often a SAID of the inception event.
    """
    
    def __repr__(self):
        return f"AID('{str(self)}')"
