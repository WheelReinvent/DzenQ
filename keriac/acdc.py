from typing import Optional, Union
from keri.vc import proving
from .base import SAD
from .identity import Identity
from .said import SAID

class ACDC(SAD):
    """
    Academic wrapper for the Authentic Chained Data Container (ACDC).
    Represents a Verifiable Credential in the KERI ecosystem.
    Inherits from SAD for consistent SAID and serialization handling.
    """

    def __init__(self, 
                 sad_or_raw: Optional[Union[dict, bytes, str, SAD]] = None,
                 *,
                 issuer: Optional[Identity] = None, 
                 schema: Optional[str] = None, 
                 attributes: Optional[dict] = None, 
                 recipient: Optional[str] = None,
                 registry: Optional[str] = None,
                 source: Optional[Union[dict, list]] = None,
                 rules: Optional[Union[dict, list]] = None,
                 **kwargs):
        """
        Initialize an ACDC.
        
        Style 1: Wrap existing credential
            ACDC(sad_or_raw)
            
        Style 2: Create new credential
            ACDC(issuer=..., schema=..., attributes=...)
        """
        if sad_or_raw is not None:
            if any([issuer, schema, attributes]):
                raise ValueError("Cannot provide both sad_or_raw and creation arguments (issuer, schema, etc.)")
            super().__init__(sad_or_raw)
        elif all([issuer, schema, attributes]):
            serder = proving.credential(
                issuer=issuer.aid,
                schema=schema,
                data=attributes,
                recipient=recipient,
                status=registry,
                source=source,
                rules=rules,
                **kwargs
            )
            super().__init__(serder)
        else:
            raise ValueError("Must provide either sad_or_raw OR (issuer, schema, and attributes)")

    @classmethod
    def create(cls, *args, **kwargs):
        """
        [Deprecated] Use ACDC constructor directly.
        """
        import warnings
        warnings.warn("ACDC.create() is deprecated. Use ACDC() constructor directly.", DeprecationWarning, stacklevel=2)
        return cls(*args, **kwargs)

    def __repr__(self):
        return f"ACDC(said='{self.said}')"
