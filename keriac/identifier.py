from keri.app import habbing

class Identifier:
    """
    Academic wrapper for the KERI Habitat (Hab).
    Represents an Identifier Environment (the 'house' of an AID).
    """

    def __init__(self, name: str, **kwargs):
        """
        Initialize an Identifier environment.
        
        Args:
            name (str): The human-readable alias for this identifier.
            **kwargs: Additional parameters passed to the underlying Hab.
        """
        # We'll use Hby (Habery) to manage the habitat.
        # For simplicity in this facade, we use a temporary Hby if one isn't provided.
        self._hby = habbing.Habery(name=name, temp=True)
        self._hab = self._hby.makeHab(name=name, **kwargs)

    @property
    def aid(self) -> str:
        """The Autonomic Identifier (Prefix) in qb64."""
        return self._hab.pre

    @property
    def habitat(self):
        """Access the underlying KERI Hab instance."""
        return self._hab

    def close(self):
        """Close the underlying database and resources."""
        self._hby.close()

    def __repr__(self):
        return f"Identifier(alias='{self._hab.name}', aid='{self.aid}')"
