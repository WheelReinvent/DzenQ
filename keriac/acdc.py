from typing import Union, Optional
from keri.vc import proving

from .identity import Identity
from .base import *
from .types import ACDCDict
from .schema import Schema, registry


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
                 schema: Optional[Union[str, Schema]] = None, 
                 attributes: Optional[dict] = None, 
                 recipient: Optional[str] = None,
                 registry_aid: Optional[str] = None, # Renamed to avoid confusion with registry
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
            
            # Resolve schema SAID
            schema_said = registry.resolve_said(schema)

            serder = proving.credential(
                issuer=issuer.aid,
                schema=schema_said,
                data=attributes,
                recipient=recipient,
                status=registry_aid,
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

    @property
    def data(self) -> ACDCDict:
        """The internal dictionary representation (SAD) of the object."""
        return super().data

    @property
    def issuer(self) -> AID:
        """The Issuer AID."""
        return AID(self.data[Fields.ISSUER])

    @property
    def schema(self) -> str:
        """The Schema SAID."""
        return self.data[Fields.SCHEMA]

    @property
    def schema_instance(self) -> Optional[Schema]:
        """Try to get the Schema instance from registry."""
        return registry.get(self.schema)

    def verify_schema(self) -> bool:
        """
        Verify the credential attributes against its schema.
        
        Returns:
            bool: True if attributes conform to schema.
        """
        schema_inst = self.schema_instance
        if not schema_inst:
            # If we don't have the schema locally, we can't verify its content
            # (In a real system, we'd fetch it by SAID first)
            return False
            
        return schema_inst.verify_dict(self.attributes)

    @property
    def attributes(self) -> dict:
        """The credential attributes."""
        from .const import Fields
        return self.data[Fields.ATTRIBUTES]

    @classmethod
    def deserialize(cls, raw: bytes) -> "ACDC":
        """Reconstruct ACDC from bytes."""
        return cls(raw)

    def __repr__(self):
        return f"ACDC(said='{self.said}')"
