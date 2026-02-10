from typing import Optional

class SAD:
    """
    Self-Addressing Data (SAD) base class.
    Represents an object that has a Self-Addressing Identifier (SAID).
    """

    def __init__(self, serder):
        """
        Initialize a SAD object.
        
        Args:
            serder: The underlying keri.core.serdering.Serder instance.
        """
        self._serder = serder

    @property
    def data(self) -> dict:
        """The internal dictionary representation (SAD) of the object."""
        return self._serder.sad

    @property
    def said(self) -> str:
        """The Self-Addressing Identifier (SAID) of the object."""
        return self._serder.said

    @property
    def qb64(self) -> str:
        """The qb64 serialization of the object."""
        # Note: Serder usually has .raw, we decode it to get qb64
        return self._serder.raw.decode("utf-8")

    @property
    def raw(self) -> bytes:
        """The raw bytes serialization of the object."""
        return self._serder.raw

    def to_json(self, indent: Optional[int] = None) -> str:
        """
        Return the object as a JSON string.
        
        Args:
            indent (int, optional): Number of spaces for indentation.
        """
        import json
        return json.dumps(self.data, indent=indent)

    @property
    def json(self) -> str:
        """The object represented as a JSON string (no indentation)."""
        return self.to_json()

    def __repr__(self):
        return f"{self.__class__.__name__}(said='{self.said}')"
