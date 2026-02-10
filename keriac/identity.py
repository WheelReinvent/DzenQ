from keri.app import habbing

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
    def aid(self) -> 'AID':
        """The Autonomous Identifier (AID) of this entity (qb64)."""
        from .aid import AID
        return AID(self._hab.pre)

    @property
    def habitat(self):
        """Access the underlying KERI Hab instance."""
        return self._hab

    @property
    def kel(self) -> 'KEL':
        """Access the Key Event Log (KEL) for this identity."""
        from .kel import KEL
        return KEL(self)

    def close(self):
        """Close the underlying database and resources."""
        self._hby.close()

    def __repr__(self):
        return f"Identity(alias='{self._hab.name}', aid='{self.aid}')"
