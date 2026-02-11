from typing import Type, TypeVar, Union, Iterable, List
from .base import Serializable

from keri import kering
from keri.kering import sniff, Colds, Protocols
from keri.core.serdering import Serdery
from .base import SAID, SAD
from .event import Event
from .acdc import ACDC
from .crypto import PublicKey, Signature
from keri.help.helping import nabSextets, codeB2ToB64
from keri.core.coring import Matter, DigDex, PreDex, NonTransDex
from keri.core.indexing import Indexer, IdxSigDex

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
        
        reaped = False
        if cold == Colds.msg:
            try:
                # Polymorphic message reaping using KERI's Serdery
                serder = serdery.reap(ims)
                if serder.proto == Protocols.keri:
                    results.append(Event(serder))
                elif serder.proto == Protocols.acdc:
                    results.append(ACDC(serder))
                else:
                    results.append(SAD(serder))
                reaped = True
            except (kering.VersionError, kering.ProtocolError, kering.ValidationError, ValueError):
                # Fallback to primitive parsing if message parsing fails
                pass

        if not reaped:

            # Extract first sextet to find hard size
            first = nabSextets(ims, 1)
            
            # Use derivation codes to dispatch to the correct wrapper class.
            # Some codes overlap (e.g., 'E' is both Blake3 digest and ECDSA signature).
            # We resolve this by trying the most likely types first.
            
            obj = None
            
            # Check Matter-based objects (SAID, PublicKey)
            if first in Matter.Bards:
                hs = Matter.Bards[first]
                code = codeB2ToB64(ims, hs)
                
                # 1. Try SAID for digest codes ('E', 'F', etc.)
                if code in DigDex:
                    try:
                        obj = SAID.deserialize(bytes(ims))
                    except Exception:
                        pass
                
                # 2. Try PublicKey for prefix codes ('B', 'D', '1AAA', etc.)
                if not obj and (code in PreDex or code in NonTransDex):
                    try:
                        obj = PublicKey.deserialize(bytes(ims))
                    except Exception:
                        pass

            # Check Indexer-based objects (Signature)
            if not obj and first in Indexer.Bards:
                hs = Indexer.Bards[first]
                code = codeB2ToB64(ims, hs)
                
                if code in IdxSigDex:
                    try:
                        obj = Signature.deserialize(bytes(ims))
                    except Exception:
                        pass
                        
            if obj:
                results.append(obj)
                del ims[:obj.size]
            else:
                # Final fallback for truly unknown material
                try:
                    obj = SAID.deserialize(bytes(ims))
                    results.append(obj)
                    del ims[:obj.size]
                except Exception:
                    # If we still fail, break to prevent infinite loop
                    break
            
    return results
