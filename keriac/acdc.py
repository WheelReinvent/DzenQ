from typing import Union, Optional, TYPE_CHECKING, List
from keri.vc import proving

from .identity import Identity
from .base import SAD, AID, SAID, Fields
from .types import ACDCDict
from .schema import Schema, schema_registry

if TYPE_CHECKING:
    from .registry import Registry
    from .presentation import Presentation


class ACDC(SAD):
    """
    Academic wrapper for the Authentic Chained Data Container (ACDC).
    Represents a Verifiable Credential in the KERI ecosystem.
    Inherits from SAD for consistent SAID and serialization handling.
    """

    def __init__(self, 
                 sad_or_raw: Union[ACDCDict, bytes, str, SAD]):
        """
        Initialize an ACDC by wrapping existing data.
        To create a NEW credential, use ACDC.create().
        
        Args:
            sad_or_raw: Existing ACDC data as a dict, bytes, or SAD instance.
        """
        super().__init__(sad_or_raw)

    @classmethod
    def create(cls, 
               issuer: Identity, 
               schema: Union[str, Schema], 
               attributes: dict, 
               recipient: Optional[str] = None,
               status: Optional[str] = None,
               source: Optional[Union[dict, list]] = None,
               rules: Optional[Union[dict, list]] = None,
               **kwargs) -> "ACDC":
        """
        Create a new ACDC credential.
        
        Args:
            issuer: The Identity issuing the credential.
            schema: Schema instance or alias/SAID.
            attributes: The data fields for the credential.
            recipient: Optional AID of the recipient.
            status: Optional registry AID for status.
            source: Optional cryptographic source seals.
            rules: Optional credential rules.
            **kwargs: Additional fields for proving.credential.
            
        Returns:
            ACDC: A new ACDC instance.
        """
        # Resolve schema SAID
        schema_said = schema_registry.resolve_said(schema)

        serder = proving.credential(
            issuer=issuer.aid,
            schema=schema_said,
            data=attributes,
            recipient=recipient,
            status=status,
            source=source,
            rules=rules,
            **kwargs
        )
        return cls(serder)

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
        return schema_registry.get(self.schema)

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
            
        return schema_inst.validate(self.attributes)

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

    @property
    def recipient(self) -> Optional[AID]:
        """The Recipient AID (if any)."""
        from .const import Fields
        # 'i' in the 'a' block (attributes) is usually the subject/recipient
        # But in KERI ACDC, recipient can be top-level or in attributes depending on version/spec.
        # keri.vc.proving.credential puts recipient in top level subject 'i' usually? 
        # Let's check constructor: subject['i'] = recipient.
        # So it is inside the 'a' (attributes) block usually, but referred to as subject.
        
        # We access the 'a' block
        attrs = self.attributes
        if 'i' in attrs:
            return AID(attrs['i'])
        return None

    def present(self, disclose_fields: Optional[List[str]] = None) -> 'Presentation':
        """
        Create a Presentation from this credential.
        
        Args:
            disclose_fields (list): Attributes to reveal.
            
        Returns:
            Presentation: The presentation object.
        """
        from .presentation import Presentation
        return Presentation(credential=self, disclose_fields=disclose_fields)
    
    # --- TEL / Registry Integration ---

    @property
    def registry(self) -> Optional['Registry']:
        """
        The Registry instance associated with this credential.
        Attached at runtime if issued via Identity.issue_credential.
        """
        return getattr(self, '_registry', None)

    @registry.setter
    def registry(self, value: 'Registry'):
        self._registry = value

    def revoke(self):
        """
        Revoke this credential.
        Requires the credential to be attached to a Registry (via issue_credential).
        """
        if not self.registry:
            raise ValueError("Cannot revoke: Registry instance not attached to this credential.")
        
        self.registry.revoke(self)

    @property
    def revoked(self) -> bool:
        """
        Check if the credential is revoked.
        """
        # In a real system, this would query the DB/Ledger using self.status (Registry AID)
        # For now, we delegate to the attached registry if present
        if self.registry:
            status = self.registry.status(self)
            return status == "Revoked"
        return False
        
    def is_revoked(self) -> bool:
        """Alias for revoked property."""
        return self.revoked

