from typing import Optional

class SAD:
    """
    Self-Addressing Data (SAD) base class.
    Represents an object that has a Self-Addressing Identifier (SAID).
    """

    def __init__(self, sad_or_raw):
        """
        Initialize a SAD object.
        
        Args:
            sad_or_raw: A dict (SAD data), bytes/str (raw data), or a Serder instance.
        """
        from keri.core import serdering
        from keri.core.serdering import SerderKERI, Serder
        
        def load_sad(sad=None, raw=None):
            try:
                # Try KERI Event first (strict)
                return SerderKERI(sad=sad, raw=raw)
            except Exception:
                # Fallback to general SAD
                return Serder(sad=sad, raw=raw)

        if isinstance(sad_or_raw, dict):
            self._sad = load_sad(sad=sad_or_raw)
        elif isinstance(sad_or_raw, (bytes, bytearray, memoryview)):
            self._sad = load_sad(raw=bytes(sad_or_raw))
        elif isinstance(sad_or_raw, str):
            self._sad = load_sad(raw=sad_or_raw.encode("utf-8"))
        elif isinstance(sad_or_raw, SAD):
            self._sad = sad_or_raw._sad
        elif hasattr(sad_or_raw, 'sad'): # Likely a keri Serder
            self._sad = sad_or_raw
        else:
            raise ValueError(f"Unsupported type for SAD initialization: {type(sad_or_raw)}")

    @property
    def data(self) -> dict:
        """The internal dictionary representation (SAD) of the object."""
        return self._sad.sad

    @property
    def said(self) -> 'SAID':
        """The Self-Addressing Identifier (SAID) of the object."""
        from .said import SAID
        return SAID(self._sad.said)

    @property
    def qb64(self) -> str:
        """The qb64 serialization of the object."""
        return self._sad.raw.decode("utf-8")

    @property
    def raw(self) -> bytes:
        """The raw bytes serialization of the object."""
        return self._sad.raw

    @property
    def version(self) -> str:
        """The version string."""
        from .const import Fields
        return self.data[Fields.VERSION]

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
