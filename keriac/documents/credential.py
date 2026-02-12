from typing import Union, Optional, TYPE_CHECKING, List
from keri.vc import proving

from ..identity import Identity
from ..domain import SAD, AID, SAID, Fields, ACDCDict
from keriac.documents.schema import Schema, schema_registry

if TYPE_CHECKING:
    from ..logbook.transactions import TransactionLog
    from .presentation import Presentation


class ACDC(SAD):
    """
    Academic wrapper for the Authentic Chained Data Container (ACDC).
    Represents a Verifiable Credential in the KERI ecosystem.
    Inherits from SAD for consistent SAID and serialization handling.
    """

    def __init__(self, sad_or_raw: Union[ACDCDict, bytes, str, SAD, 'Serder']):
        """
        Initialize an ACDC by wrapping existing data.
        To create a NEW credential, use ACDC.create().
        
        Args:
            sad_or_raw: Existing ACDC data as a dict, bytes, SAD instance, or Serder.
        """
        from keri.core.serdering import Serder
        if isinstance(sad_or_raw, ACDC):
             self._serder = sad_or_raw._serder
        elif isinstance(sad_or_raw, dict):
             self._serder = Serder(sad=sad_or_raw)
        elif isinstance(sad_or_raw, (bytes, bytearray, memoryview)):
             self._serder = Serder(raw=bytes(sad_or_raw))
        elif hasattr(sad_or_raw, 'sad'): # Likely a keri Serder
             self._serder = sad_or_raw
        else:
            raise ValueError(f"Unsupported type for ACDC initialization: {type(sad_or_raw)}")

    @property
    def data(self) -> ACDCDict:
        """The internal dictionary representation (SAD) of the ACDC."""
        return self._serder.sad

    @property
    def said(self) -> SAID:
        """The Self-Addressing Identifier (SAID) of the ACDC."""
        return SAID(self._serder.said)

    @property
    def raw(self) -> bytes:
        """The raw bytes serialization of the ACDC (CESR)."""
        return self._serder.raw

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
        from ..const import Fields
        return self.data[Fields.ATTRIBUTES]

    def __repr__(self):
        return f"ACDC(said='{self.said}')"

    @property
    def recipient(self) -> Optional[AID]:
        """The Recipient AID (if any)."""
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
    def transaction_log(self) -> Optional['TransactionLog']:
        """
        The TransactionLog instance associated with this credential.
        Attached at runtime if issued via Identity.issue_credential.
        """
        return getattr(self, '_transaction_log', None)

    @transaction_log.setter
    def transaction_log(self, value: 'TransactionLog'):
        self._transaction_log = value

    def revoke(self):
        """
        Revoke this credential.
        Requires the credential to be attached to a TransactionLog (via issue_credential).
        """
        if not self.transaction_log:
            raise ValueError("Cannot revoke: TransactionLog instance not attached to this credential.")
        
        self.transaction_log.revoke(self)

    @property
    def revoked(self) -> bool:
        """
        Check if the credential is revoked.
        """
        # In a real system, this would query the DB/Ledger using self.status (Registry AID)
        # For now, we delegate to the attached registry if present
        if self.transaction_log:
            status = self.transaction_log.status(self)
            return status == "Revoked"
        return False
        
    def is_revoked(self) -> bool:
        """Alias for revoked property."""
        return self.revoked

