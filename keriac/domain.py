import json
from abc import ABC, abstractmethod
from typing import Optional, TypedDict, Dict, Any
from typing_extensions import Self

from keri.core.coring import Saider
from keri.core.signing import Signer as KeriSigner, Siger as KeriSiger
from keri.core.coring import Verfer as KeriVerfer

from .const import Fields


SADDict = TypedDict('SADDict', {
    'v': str,   # Version
    't': str,   # Type (Ilk)
    'd': str,   # SAID (Digest)
    '$id': str  # Schema SAID
}, total=False)

SchemaDict = TypedDict('SchemaDict', {
    'v': str,   # Version
    't': str,   # Type (Ilk)
    'd': str,   # SAID (Digest)
    '$id': str, # Schema SAID
    '$schema': str,
    'title': str,
    'description': str,
    'type': str,
    'properties': dict[str, Any],
    'required': list[str],
}, total=False)

class EventDict(SADDict):
    """
    TypedDict for KERI Events (icp, rot, ixn, etc.).
    """
    i: str              # AID (Prefix)
    s: str              # Sequence Number (hex)
    p: Optional[str]    # Prior Event Digest
    k: Optional[list[str]] # Signing Keys
    n: Optional[str]    # Next Key Digest
    bt: Optional[str]   # Backer Threshold
    b: Optional[list[str]] # Witnesses (Backers)
    c: Optional[list[str]] # Cuts
    a: Optional[list[Any]] # Seals

class ACDCDict(SADDict):
    """
    TypedDict for ACDC Credentials.
    """
    i: str              # Issuer AID
    s: str              # Schema SAID
    a: dict[str, Any]   # Attributes
    ri: Optional[str]   # Recipient AID

class DigestSeal(TypedDict):
    """Seal pointing to a SAD's digest."""
    d: str  # SAID/Digest

class EventSeal(TypedDict):
    """Seal pointing to a specific KEL event."""
    i: str  # AID
    s: str  # Sequence number (hex)
    d: str  # Event digest

class HashSeal(TypedDict):
    """Seal containing a generic hash (e.g. Merkle root)."""
    h: str  # Hash

from typing import Union
Seal = Union[DigestSeal, EventSeal, HashSeal, Dict[str, Any]]


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
    def deserialize(cls, raw: bytes) -> Self:
        """
        Create an object instance from the provided CESR bytes.
        """
        pass


class PublicKey(str, Serializable):
    """
    A public key verifier (academic: Verifier).
    Wraps KERI's Verfer with a clean, serializable interface.
    """

    def __new__(cls, qb64: str):
        """Create new PublicKey string instance."""
        return str.__new__(cls, qb64)

    def __init__(self, qb64: str):
        """Initialize from qb64 public key string."""
        self._verfer = KeriVerfer(qb64=qb64)

    @property
    def qb64(self) -> str:
        """Base64 qualified representation."""
        return self._verfer.qb64

    @property
    def size(self) -> int:
        """Binary size of public key."""
        return len(self._verfer.qb2)

    def serialize(self) -> bytes:
        """Return binary CESR (qb2) representation."""
        return self._verfer.qb2

    @classmethod
    def deserialize(cls, raw: bytes) -> "PublicKey":
        """Reconstruct PublicKey from binary bytes (qb2)."""
        verfer = KeriVerfer(qb2=raw)
        return cls(verfer.qb64)

    def verify(self, data: bytes, signature: 'Signature') -> bool:
        """
        Verify a signature over data.

        Args:
            data: The data that was signed.
            signature: The signature to verify.

        Returns:
            bool: True if signature is valid.
        """
        try:
            return self._verfer.verify(sig=signature._raw, ser=data)
        except Exception:
            return False

    def __str__(self):
        return self.qb64

    def __repr__(self):
        return f"PublicKey('{self.qb64[:16]}...')"


class Signature(str, Serializable):
    """
    A cryptographic signature (academic: Signature).
    Wraps KERI's Siger with a clean, serializable interface.
    """

    def __new__(cls, qb64: str):
        """Create new Signature string instance."""
        return str.__new__(cls, qb64)

    def __init__(self, qb64: str):
        """Initialize from qb64 signature string."""
        self._siger = KeriSiger(qb64=qb64)

    @property
    def qb64(self) -> str:
        """Base64 qualified representation."""
        return self._siger.qb64

    @property
    def _raw(self) -> bytes:
        """Raw signature bytes (internal use)."""
        return self._siger.raw

    @property
    def size(self) -> int:
        """Binary size of signature."""
        return len(self._siger.qb2)

    def serialize(self) -> bytes:
        """Return binary CESR (qb2) representation."""
        return self._siger.qb2

    @classmethod
    def deserialize(cls, raw: bytes) -> "Signature":
        """Reconstruct Signature from binary bytes (qb2)."""
        siger = KeriSiger(qb2=raw)
        return cls(siger.qb64)

    def __str__(self):
        return self.qb64

    def __repr__(self):
        return f"Signature('{self.qb64[:16]}...')"


class PrivateKey:
    """
    A private signing key (academic: Signing Key).
    Wraps KERI's Signer with a clean interface.

    SECURITY: This class does NOT extend Serializable.
    Private keys should never be serialized or transmitted.
    """

    def __init__(self, signer: KeriSigner):
        """Initialize from KERI Signer (internal use only)."""
        self._signer = signer

    def sign(self, data: bytes) -> Signature:
        """
        Sign data with this private key.

        Args:
            data: The data to sign.

        Returns:
            Signature: The cryptographic signature.
        """
        siger = self._signer.sign(ser=data)
        return Signature(siger.qb64)

    @property
    def public_key(self) -> PublicKey:
        """Get the corresponding public key."""
        return PublicKey(self._signer.verfer.qb64)


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
        from keriac.transport.serialize import unpack
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

    def __init__(self, data_or_raw: Union[SADDict, bytes, str, 'Serder'], kind: str = "JSON"):
        """
        Initialize a DataRecord.
        
        Args:
            data_or_raw: A dictionary, bytes, or KERI Serder.
            kind: Serialization kind (JSON, CBOR, MGPK). Default is JSON.
        """
        from keri.core import coring
        from keri.core.serdering import Serder
        from keri.kering import Kinds
        
        if isinstance(data_or_raw, dict):
            # Ensure it has SAID fields using saidify
            sad = data_or_raw.copy()
            label = 'd'
            if '$id' in sad:
                label = '$id'

            # KERI Serder requires version string 'v' to be present.
            # 1. Handle version string and field order
            v_val = sad.pop(Fields.VERSION, f"KERI10{kind}000000_")
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
            
            # Manual sizeification to avoid Serder's strictness while ensuring correct version string and size.
            if kind == Kinds.json:
                import json
                raw = json.dumps(sad, separators=(',', ':')).encode("utf-8")
            elif kind == Kinds.cbor:
                import cbor2
                raw = cbor2.dumps(sad)
            elif kind == Kinds.mgpk:
                import msgpack
                raw = msgpack.dumps(sad)
            else:
                raise ValueError(f"Unsupported serialization kind: {kind}")

            size = len(raw)
            # Update the version string with the correct hex size
            v_val = sad[Fields.VERSION]
            v_val = v_val[:10] + f"{size:06x}" + v_val[16:]
            sad[Fields.VERSION] = v_val
            
            # Use verify=False to allow arbitrary SADs that are not standard KERI messages.
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




