from typing_extensions import TypedDict, Optional, List, Dict, Any

class SADDict(TypedDict, total=False):
    """
    Base TypedDict for Self-Addressing Data (SAD).
    Using total=False to allow for optional fields in the base.
    """
    v: str  # Version
    t: str  # Type (Ilk)
    d: str  # SAID (Digest)

class EventDict(SADDict):
    """
    TypedDict for KERI Events (icp, rot, ixn, etc.).
    """
    i: str              # AID (Prefix)
    s: str              # Sequence Number (hex)
    p: Optional[str]    # Prior Event Digest
    k: Optional[List[str]] # Signing Keys
    n: Optional[str]    # Next Key Digest
    bt: Optional[str]   # Backer Threshold
    b: Optional[List[str]] # Witnesses (Backers)
    c: Optional[List[str]] # Cuts
    a: Optional[List[Any]] # Seals

class ACDCDict(SADDict):
    """
    TypedDict for ACDC Credentials.
    """
    i: str              # Issuer AID
    s: str              # Schema SAID
    a: Dict[str, Any]   # Attributes
    ri: Optional[str]   # Recipient AID
