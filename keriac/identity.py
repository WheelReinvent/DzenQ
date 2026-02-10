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
        """
        Access the underlying KERI Hab instance.
        .. deprecated:: 0.1.0
           Use Identity-level methods like `anchor()` instead.
        """
        return self._hab

    def anchor(self, data=None, **kwargs) -> 'Event':
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
        from .event import Event
        
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
    def kel(self) -> 'KEL':
        """Access the Key Event Log (KEL) for this identity."""
        from .kel import KEL
        return KEL(self)

    def close(self):
        """Close the underlying database and resources."""
        self._hby.close()

    def __repr__(self):
        return f"Identity(alias='{self._hab.name}', aid='{self.aid}')"
