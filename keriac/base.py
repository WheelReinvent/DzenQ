import json
from typing import Optional

from .const import Fields
from .types import SADDict


class SAID(str):
    """
    Self-Addressing Identifier (SAID).
    Inherits from str for easy usage as a string while providing utility methods.
    """

    def __repr__(self):
        return f"SAID('{str(self)}')"


class AID(SAID):
    """
    Autonomous Identifier (AID).
    Representing the unique identifier of a KERI agent.
    An AID is often a SAID of the inception event.
    """

    def __repr__(self):
        return f"AID('{str(self)}')"


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
        from keri.core import serdering, coring
        from keri.core.serdering import SerderKERI, Serder
        
        self._sad = None
        self._manual_data = None
        self._manual_said = None
        self._manual_raw = None

        def load_sad(sad=None, raw=None):
            try:
                # Try KERI Event first (strict)
                return SerderKERI(sad=sad, raw=raw)
            except Exception:
                # Fallback to general SAD
                return Serder(sad=sad, raw=raw)

        if isinstance(sad_or_raw, SAD):
            self._sad = sad_or_raw._sad
            self._manual_data = sad_or_raw._manual_data
            self._manual_said = sad_or_raw._manual_said
            self._manual_raw = sad_or_raw._manual_raw
        elif hasattr(sad_or_raw, 'sad') and hasattr(sad_or_raw, 'said'): # Likely a keri Serder
            self._sad = sad_or_raw
        elif isinstance(sad_or_raw, dict):
            # If it's a raw dict, try to ensuring it has SAID fields using saidify
            try:
                 from keri.core import coring
                 sad = sad_or_raw.copy()
                 # Only generate SAID if it's missing or empty
                 if not sad.get('d'):
                     _, sad = coring.Saider.saidify(sad=sad)
                 
                 try:
                     self._sad = load_sad(sad=sad)
                 except Exception:
                     # Fallback for non-KERI SADs (no version string)
                     self._manual_data = sad
                     # Extract SAID from 'd' if it's there
                     self._manual_said = sad.get('d')
                     import json
                     self._manual_raw = json.dumps(sad, separators=(',', ':')).encode("utf-8")
            except Exception:
                 # Fallback if even saidify fails (e.g. no 'd' label allowed), try direct load
                 self._sad = load_sad(sad=sad_or_raw)
        elif isinstance(sad_or_raw, (bytes, bytearray, memoryview)):
            try:
                self._sad = load_sad(raw=bytes(sad_or_raw))
            except Exception:
                # If it's not a KERI event, it might be a bare JSON SAD
                import json
                try:
                    data = json.loads(bytes(sad_or_raw).decode("utf-8"))
                    self._manual_data = data
                    self._manual_said = data.get('d')
                    self._manual_raw = bytes(sad_or_raw)
                except Exception:
                    raise ValueError(f"Could not parse raw data as SAD: {sad_or_raw!r}") from None
        elif isinstance(sad_or_raw, str):
            # Delegate to bytes handling
            data_bytes = sad_or_raw.encode("utf-8")
            try:
                self._sad = load_sad(raw=data_bytes)
            except Exception:
                import json
                try:
                    data = json.loads(sad_or_raw)
                    self._manual_data = data
                    self._manual_said = data.get('d')
                    self._manual_raw = data_bytes
                except Exception:
                    raise ValueError(f"Could not parse string as SAD: {sad_or_raw}") from None
        else:
            raise ValueError(f"Unsupported type for SAD initialization: {type(sad_or_raw)}")

    @property
    def data(self) -> SADDict:
        """The internal dictionary representation (SAD) of the object."""
        if self._sad:
            return self._sad.sad
        return self._manual_data

    @property
    def said(self) -> SAID:
        """The Self-Addressing Identifier (SAID) of the object."""
        if self._sad:
            return SAID(self._sad.said)
        return SAID(self._manual_said)

    @property
    def qb64(self) -> str:
        """The qb64 serialization of the object."""
        return self.raw.decode("utf-8")

    @property
    def raw(self) -> bytes:
        """The raw bytes serialization of the object."""
        if self._sad:
            return self._sad.raw
        return self._manual_raw

    @property
    def version(self) -> Optional[str]:
        """The version string."""
        return self.data.get(Fields.VERSION)

    def to_json(self, indent: Optional[int] = None) -> str:
        """
        Return the object as a JSON string.
        
        Args:
            indent (int, optional): Number of spaces for indentation.
        """
        return json.dumps(self.data, indent=indent)

    @property
    def json(self) -> str:
        """The object represented as a JSON string (no indentation)."""
        return self.to_json()

    def verify(self) -> bool:
        """
        Verify that the object's SAID matches its data.
        
        Returns:
            bool: True if verified, False otherwise.
        """
        from keri.core import coring
        try:
            saider = coring.Saider(qb64=str(self.said))
            # Verification against dict is generally safer for flexible SADs
            return saider.verify(sad=self.data)
        except Exception:
            return False

    def __repr__(self):
        return f"{self.__class__.__name__}(said='{self.said}')"
