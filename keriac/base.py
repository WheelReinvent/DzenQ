import json
from typing import Optional, Union, TYPE_CHECKING

from keri.core.serdering import SerderKERI, Serder
from keri.core import coring
from keri.core.coring import Saider

from .const import Fields
from .types import SADDict


class Serializable:
    """
    Base class for objects that can be serialized/deserialized to/from CESR.
    """

    @property
    def size(self) -> int:
        """
        Return the size of the serialized object in bytes.
        Essential for stream-based unpacking.
        """
        raise NotImplementedError

    def serialize(self) -> bytes:
        """
        Serialize the object to CESR bytes (usually qb2).
        """
        raise NotImplementedError

    @classmethod
    def deserialize(cls, raw: bytes) -> "Serializable":
        """
        Create an object instance from the provided CESR bytes.
        """
        raise NotImplementedError


class SAID(str, Serializable):
    """
    Self-Addressing Identifier (SAID).
    Inherits from str for easy usage as a string while providing utility methods.
    """

    @property
    def size(self) -> int:
        """The size of the binary SAID (qb2)."""
        return len(Saider(qb64=str(self)).qb2)

    def serialize(self) -> bytes:
        """Return the binary CESR (qb2) representation."""
        return Saider(qb64=str(self)).qb2

    @classmethod
    def deserialize(cls, raw: bytes) -> "SAID":
        """Reconstruct SAID from binary bytes (qb2)."""
        # Saider handles extracting exactly one SAID from the start of raw
        saider = Saider(qb2=raw)
        return cls(saider.qb64)

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


class GeneralSAD:
    """
    Internal wrapper for non-standard KERI SAD dictionaries.
    Provides .sad, .said, and .raw properties to satisfy the SAD interface
    when the data is not a strict KERI event or ACDC.
    """
    def __init__(self, sad: dict, label: str = 'd'):
        self.sad = sad
        self.label = label
        
        # Ensure SAID is present
        if not self.sad.get(self.label):
             _, self.sad = coring.Saider.saidify(sad=self.sad, label=self.label)
             
    @property
    def said(self) -> str:
        return self.sad.get(self.label)
        
    @property
    def raw(self) -> bytes:
        return coring.dumps(self.sad)


class SAD(Serializable):
    """
    Self-Addressing Data (SAD) base class.
    Represents an object that has a Self-Addressing Identifier (SAID).
    """

    def __init__(self, sad_or_raw: Union['SAD', SADDict, bytes, str]):
        """
        Initialize a SAD object.
        
        Args:
            sad_or_raw: A dict (SAD data), bytes/str (raw data), or another SAD instance.
        """
        self._sad = None

        if isinstance(sad_or_raw, SAD):
            self._sad = sad_or_raw._sad
        elif hasattr(sad_or_raw, 'sad') and hasattr(sad_or_raw, 'said'): # Likely a keri Serder or Schemer
            self._sad = sad_or_raw
        elif isinstance(sad_or_raw, dict):
            # Ensure it has SAID fields using saidify
            sad = sad_or_raw.copy()
            label = 'd'
            if '$id' in sad:
                label = '$id'

            # Only generate SAID if it's missing or empty
            if not sad.get(label):
                _, sad = coring.Saider.saidify(sad=sad, label=label)
            
            self._sad = self._load_internal_repr(sad=sad)
        elif isinstance(sad_or_raw, (bytes, bytearray, memoryview)):
            self._sad = self._load_internal_repr(raw=bytes(sad_or_raw))
        elif isinstance(sad_or_raw, str):
            # Delegate to bytes handling
            self._sad = self._load_internal_repr(raw=sad_or_raw.encode("utf-8"))
        else:
            raise ValueError(f"Unsupported type for SAD initialization: {type(sad_or_raw)}")

        if self._sad is None:
            raise ValueError(f"Could not initialize SAD from provided data: {sad_or_raw!r}")

    def _load_internal_repr(self, sad: Optional[dict] = None, raw: Optional[bytes] = None):
        """
        Template method to load the internal KERI representation.
        Subclasses (like Schema) should override this to return their specific type.
        """
        if raw and not sad:
            try:
                # If we only have raw, we MUST be able to parse it as some Serder
                # to know what it is (including protocol/version).
                try:
                    return SerderKERI(raw=raw)
                except Exception:
                    return Serder(raw=raw)
            except Exception:
                # Fallback: try to deserialize raw into a dict and handle it
                try:
                    # Try sniffing kind and loading
                    from keri.kering import smell
                    _, _, kind, _, _ = smell(raw)
                    sad = coring.loads(raw=raw, kind=kind)
                    if not isinstance(sad, dict):
                         raise ValueError("Raw data is not a dictionary")
                except Exception as e:
                    raise ValueError(f"Data is not a valid KERI/CESR serialization") from e

        # If we have a dict (sad), we try to be helpful
        if sad and 'v' in sad:
            try:
                # Try KERI Event first (strict)
                return SerderKERI(sad=sad, makify=True)
            except Exception:
                try:
                    # Fallback to general KERI SAD (requires version string)
                    return Serder(sad=sad, makify=True)
                except Exception:
                    pass

        # Last resort: Wrap it in GeneralSAD which is very lenient
        label = 'd'
        if sad and '$id' in sad:
            label = '$id'
        return GeneralSAD(sad=sad, label=label)

    @property
    def size(self) -> int:
        """The size of the serialized object in bytes."""
        return len(self.raw)

    def serialize(self) -> bytes:
        """Return the raw bytes (CESR wire format)."""
        return self.raw

    @classmethod
    def deserialize(cls, raw: bytes) -> "SAD":
        """Reconstruct SAD from bytes."""
        return cls(raw)

    @property
    def data(self) -> SADDict:
        """The internal dictionary representation (SAD) of the object."""
        return self._sad.sad

    @property
    def said(self) -> SAID:
        """The Self-Addressing Identifier (SAID) of the object."""
        return SAID(self._sad.said)

    @property
    def qb64(self) -> str:
        """The qb64 serialization of the object."""
        return self.raw.decode("utf-8")

    @property
    def raw(self) -> bytes:
        """The raw bytes serialization of the object."""
        return self._sad.raw

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

    def sign(self, identity: 'Identity') -> 'Signature':
        """
        Sign the object using the provided Identity.
        
        Args:
            identity: The Identity to sign with.
            
        Returns:
            Signature: The resulting cryptographic signature.
        """
        return identity.sign(self.raw)

    def verify_signature(self, signature: 'Signature', public_key: 'PublicKey') -> bool:
        """
        Verify a signature over this object.
        
        Args:
            signature: The signature to verify.
            public_key: The Public Key to verify against.
            
        Returns:
            bool: True if signature is valid.
        """
        return public_key.verify(self.raw, signature)

    def verify(self) -> bool:
        """
        Verify that the object's SAID matches its data.
        
        Returns:
            bool: True if verified, False otherwise.
        """
        try:
            # Determine label
            label = 'd'
            if '$id' in self.data:
                label = '$id'
                
            # Verification against dict is generally safer for flexible SADs
            saider = coring.Saider(qb64=str(self.said), label=label)
            return saider.verify(sad=self.data, label=label, versioned=('v' in self.data))
        except Exception:
            return False

    def __repr__(self):
        return f"{self.__class__.__name__}(said='{self.said}')"
