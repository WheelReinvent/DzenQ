from typing import Type, TypeVar, Union, Iterable, List

from keri import kering
from keri.kering import sniff, Colds, Protocols
from keri.core.serdering import Serdery
from keriac.logbook.entries.event import Event
from keri.help.helping import nabSextets, codeB2ToB64
from keri.core.coring import Matter, DigDex, PreDex, NonTransDex
from keri.core.indexing import Indexer, IdxSigDex

from keriac.domain import Serializable, DataRecord, SAID, Signature, PublicKey
from keriac.documents.credential import Credential


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
            # Backup ims because reap might partially consume it or modify it on failure
            ims_backup = bytes(ims)
            try:
                # Polymorphic message reaping using KERI's Serdery
                serder = serdery.reap(ims)
                if serder.proto == Protocols.keri:
                    results.append(Event(serder))
                elif serder.proto == Protocols.acdc:
                    results.append(Credential(serder))
                else:
                    results.append(DataRecord(serder))
                reaped = True
            except (kering.VersionError, kering.ProtocolError, kering.ValidationError, kering.DeserializeError, ValueError):
                # Restore ims
                ims[:] = ims_backup
                # Fallback: try to see if it's a valid DataRecord even if reap failed
                # This handles arbitrary SADs that have a version string but aren't standard KERI messages.
                try:
                    import json
                    import re
                    # Sniff for version string to determine size. Pattern matches KERI/ACDC version strings.
                    # Capture group 2 is the hex size.
                    match = re.search(rb'"v"\s*:\s*"([A-Z0-9]{4}[0-9A-F]{2}[A-Z]{4}([0-9A-F]{6})_)"', ims_backup[:128])
                    if match:
                        size_str = match.group(2).decode("utf-8")
                        size = int(size_str, 16)
                        if size > 0 and size <= len(ims_backup):
                            sad_data = json.loads(ims_backup[:size])
                            results.append(DataRecord(sad_data))
                            del ims[:size]
                            reaped = True
                except Exception:
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
