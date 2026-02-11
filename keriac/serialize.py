from typing import Type, TypeVar, Union, Iterable, List

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

T = TypeVar("T", bound=Serializable)

def pack(objs: Union[Serializable, Iterable[Serializable]]) -> bytes:
    """
    Pack one or more Serializable objects into a continuous CESR byte stream.
    
    Args:
        objs: A single Serializable object or an iterable of them.
        
    Returns:
        bytes: The combined CESR byte stream.
    """
    if isinstance(objs, Serializable):
        return objs.serialize()
    
    return b"".join(obj.serialize() for obj in objs)

def unpack(raw: bytes, cls: Type[T] = None) -> List[Union[T, Serializable]]:
    """
    Unpack one or more Serializable objects from a CESR byte stream.
    
    Args:
        raw: The CESR byte stream to unpack.
        cls: Optional specific class to force unpacking. If None, uses polymorphic detection.
        
    Returns:
        List: A list of unpacked object instances.
    """
    from keri.kering import sniff, Colds, Protocols
    from keri.core.serdering import Serdery
    from .base import SAID, SAD
    from .event import Event
    from .acdc import ACDC
    from .crypto import PublicKey, Signature

    results = []
    ims = bytearray(raw)  # Serdery.reap and Matter classes use stripping on bytearrays
    serdery = Serdery()
    
    while ims:
        cold = sniff(ims)
        
        if cls:
            # Force unpacking into the requested class
            obj = cls.deserialize(bytes(ims))
            results.append(obj)
            del ims[:obj.size]
            continue

        if cold == Colds.msg:
            # Polymorphic message reaping using KERI's Serdery
            serder = serdery.reap(ims)
            if serder.proto == Protocols.keri:
                results.append(Event(serder))
            elif serder.proto == Protocols.acdc:
                results.append(ACDC(serder))
            else:
                results.append(SAD(serder))
        else:
            # Binary material - try to detect the type
            # Check if it's a PublicKey (Verfer) or Signature (Siger)
            try:
                # Try PublicKey first
                obj = PublicKey.deserialize(bytes(ims))
                results.append(obj)
                del ims[:obj.size]
            except Exception:
                try:
                    # Try Signature
                    obj = Signature.deserialize(bytes(ims))
                    results.append(obj)
                    del ims[:obj.size]
                except Exception:
                    # Fall back to SAID
                    obj = SAID.deserialize(bytes(ims))
                    results.append(obj)
                    del ims[:obj.size]
            
    return results
