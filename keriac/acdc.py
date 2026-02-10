from typing import Optional, Union
from keri.vc import proving
from .identifier import Identifier
from .base import SAD

class ACDC(SAD):
    """
    Academic wrapper for the Authentic Chained Data Container (ACDC).
    Represents a Verifiable Credential in the KERI ecosystem.
    Inherits from SAD for consistent SAID and serialization handling.
    """

    @classmethod
    def create(cls, 
               issuer: Identifier, 
               schema: str, 
               attributes: dict, 
               recipient: Optional[str] = None,
               registry: Optional[str] = None,
               source: Optional[Union[dict, list]] = None,
               rules: Optional[Union[dict, list]] = None,
               **kwargs):
        """
        Create a new ACDC.
        
        Args:
            issuer (Identifier): The Identifier object representing the issuer.
            schema (str): The SAID of the ACDC Schema.
            attributes (dict): The data values for the credential subject.
            recipient (str, optional): The AID of the recipient.
            registry (str, optional): The SAID of the Transaction Event Log (TEL) registry.
            source (dict|list, optional): Chained source credentials (EOW/SAID).
            rules (dict|list, optional): ACDC rules section.
            **kwargs: Additional parameters for the underlying keri library.
            
        Returns:
            ACDC: A new ACDC instance.
        """
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
        return cls(serder)

    def __repr__(self):
        return f"ACDC(said='{self.said}')"
