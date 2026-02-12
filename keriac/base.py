import json
from abc import ABC, abstractmethod
from typing import Optional, Union, TYPE_CHECKING

from keri.core.coring import Saider

from .const import Fields
from .types import SADDict

if TYPE_CHECKING:
    from .identity import Identity
    from .crypto import PublicKey, Signature


class Serializable(ABC):
    """
    Base class for objects that can be serialized/deserialized to/from CESR.
    """

    @property
    @abstractmethod
    def size(self) -> int:
        """
        Return the size of the serialized object in bytes.
        Essential for stream-based unpacking.
        """
        pass

    @abstractmethod
    def serialize(self) -> bytes:
        """
        Serialize the object to CESR bytes (usually qb2).
        """
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, raw: bytes) -> "Serializable":
        """
        Create an object instance from the provided CESR bytes.
        """
        pass


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
        saider = Saider(qb2=raw)
        return cls(saider.qb64)

    def __repr__(self):
        return f"SAID('{str(self)}')"


class AID(SAID):
    """
    Autonomous Identifier (AID).
    Representing the unique identifier of a KERI agent.
    """

    def __repr__(self):
        return f"AID('{str(self)}')"


class SAD(Serializable, ABC):
    """
    Self-Addressing Data (SAD) Abstract Base Class.
    Represents an object that has a Self-Addressing Identifier (SAID).
    Specific subclasses (Event, ACDC, Schema) must implement the data storage logic.
    """

    @property
    @abstractmethod
    def data(self) -> SADDict:
        """The internal dictionary representation (SAD) of the object."""
        pass

    @property
    @abstractmethod
    def said(self) -> SAID:
        """The Self-Addressing Identifier (SAID) of the object."""
        pass

    @property
    @abstractmethod
    def raw(self) -> bytes:
        """The raw bytes serialization of the object (CESR wire format)."""
        pass

    @property
    def size(self) -> int:
        """The size of the serialized object in bytes."""
        return len(self.raw)

    def serialize(self) -> bytes:
        """Return the raw bytes (CESR wire format)."""
        return self.raw

    @classmethod
    def deserialize(cls, raw: bytes) -> "SAD":
        """Reconstruct SAD from bytes. Note: Base SAD will try to return a concrete instance."""
        # This implementation allows unpack(raw, SAD) to work by sniffing
        from .serialize import unpack
        results = unpack(raw)
        if results and isinstance(results[0], SAD):
            return results[0]
        raise ValueError(f"Could not deserialize {cls.__name__} from bytes")

    @property
    def version(self) -> Optional[str]:
        """The version string."""
        return self.data.get(Fields.VERSION)

    @property
    def qb64(self) -> str:
        """The qb64 serialization of the object."""
        return self.raw.decode("utf-8")

    @property
    def json(self) -> str:
        """The object represented as a JSON string (no indentation)."""
        return self.to_json()

    def to_json(self, indent: Optional[int] = None) -> str:
        """
        Return the object as a JSON string.
        """
        return json.dumps(self.data, indent=indent)

    def sign(self, identity: 'Identity') -> 'Signature':
        """
        Sign the object using the provided Identity.
        """
        return identity.sign(self.raw)

    def verify_signature(self, signature: 'Signature', public_key: 'PublicKey') -> bool:
        """
        Verify a signature over this object.
        """
        return public_key.verify(self.raw, signature)

    def verify(self) -> bool:
        """
        Verify that the object's SAID matches its data.
        """
        try:
            label = 'd'
            if '$id' in self.data:
                label = '$id'
            
            from keri.core import coring
            saider = coring.Saider(qb64=str(self.said), label=label)
            return saider.verify(sad=self.data, label=label, versioned=('v' in self.data))
        except Exception:
            return False

    def __eq__(self, other):
        if isinstance(other, SAD):
            return self.raw == other.raw
        return False


class DataRecord(SAD):
    """
    Concrete implementation of SAD for general-purpose data records.
    Can be used for any dictionary that contains a SAID.
    """

    def __init__(self, data_or_raw: Union[SADDict, bytes, str, 'Serder']):
        """
        Initialize a DataRecord.
        
        Args:
            data_or_raw: A dictionary, bytes, or KERI Serder.
        """
        from keri.core import coring
        from keri.core.serdering import Serder
        
        if isinstance(data_or_raw, dict):
            # Ensure it has SAID fields using saidify
            sad = data_or_raw.copy()
            label = 'd'
            if '$id' in sad:
                label = '$id'

            # KERI Serder requires version string 'v' to be present.
            # Saider.saidify/sizeify expects it to be the first field for JSON.
            # We use KERI protocol but add 't' (ilk) to satisfy Serder requirement.
            
            # 1. Handle version string and field order
            v_val = sad.pop(Fields.VERSION, "KERI10JSON000000_")
            # Reset size to 000000 to let Serder calculate it
            if len(v_val) >= 16:
                v_val = v_val[:10] + "000000" + v_val[16:]
            
            new_sad = {Fields.VERSION: v_val}
            
            # 2. Add 't' field if missing and it's a KERI protocol
            if Fields.TYPE not in sad and v_val.startswith("KERI"):
                new_sad[Fields.TYPE] = "ixn"  # Interaction Event is the most generic
                
            new_sad.update(sad)
            sad = new_sad

            if not sad.get(label):
                _, sad = coring.Saider.saidify(sad=sad, label=label)
            
            import json
            # Manual sizeification to avoid Serder's strictness while ensuring correct version string and size.
            # We assume JSON serialization here.
            # 1. First, compute the current size with the 000000 placeholder
            raw = json.dumps(sad, separators=(',', ':')).encode("utf-8")
            size = len(raw)
            # 2. Update the version string with the correct hex size
            v_val = sad[Fields.VERSION]
            v_val = v_val[:10] + f"{size:06x}" + v_val[16:]
            sad[Fields.VERSION] = v_val
            
            # Use verify=False to allow arbitrary SADs that are not standard KERI messages.
            # We don't use makify=True here because it enforces strict field validation.
            self._serder = Serder(sad=sad, verify=False)
        elif isinstance(data_or_raw, (bytes, bytearray, memoryview)):
            self._serder = Serder(raw=bytes(data_or_raw))
        elif isinstance(data_or_raw, str):
            self._serder = Serder(raw=data_or_raw.encode("utf-8"))
        elif hasattr(data_or_raw, 'sad'): # Likely a keri Serder
            self._serder = data_or_raw
        else:
            raise ValueError(f"Unsupported type for DataRecord initialization: {type(data_or_raw)}")

    @property
    def data(self) -> SADDict:
        return self._serder.sad

    @property
    def said(self) -> SAID:
        return SAID(self._serder.said)

    @property
    def raw(self) -> bytes:
        return self._serder.raw

    def __repr__(self):
        return f"{self.__class__.__name__}(said='{self.said}')"

