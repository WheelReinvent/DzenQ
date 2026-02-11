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

def unpack(raw: bytes, cls: Type[T]) -> List[T]:
    """
    Unpack one or more objects of type 'cls' from a CESR byte stream.
    
    Args:
        raw: The CESR byte stream to unpack.
        cls: The Serializable subclass to instantiate for each object.
        
    Returns:
        List[T]: A list of unpacked object instances.
    """
    results = []
    view = memoryview(raw)
    
    while len(view) > 0:
        # Pass the remaining stream to deserialize.
        # The subclass is responsible for parsing only its own part.
        obj = cls.deserialize(bytes(view))
        results.append(obj)
        
        # Advance the view by the actual size of the unpacked object
        view = view[obj.size:]
        
    return results
