from typing import Optional, Union
from keri.vc import proving
from .identifier import Identifier

class ACDC:
    """
    Academic wrapper for the Authentic Chained Data Container (ACDC).
    Represents a Verifiable Credential in the KERI ecosystem.
    """

    def __init__(self, serder):
        """
        Initialize an ACDC object.
        
        Args:
            serder: The underlying keri.core.serdering.SerderACDC instance.
        """
        self._serder = serder

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

    @property
    def said(self) -> str:
        """The Self-Addressing Identifier (SAID) of the ACDC."""
        return self._serder.said

    @property
    def qb64(self) -> str:
        """The qb64 serialization of the ACDC."""
        # Serder doesn't have qb64, use raw.decode()
        return self._serder.raw.decode("utf-8")

    @property
    def raw(self) -> bytes:
        """The raw bytes serialization of the ACDC."""
        return self._serder.raw

    def to_json(self, indent: Optional[int] = None) -> str:
        """
        Return the ACDC as a JSON string.
        
        Args:
            indent (int, optional): Number of spaces for indentation.
        """
        import json
        return json.dumps(self._serder.sad, indent=indent)

    @property
    def json(self) -> str:
        """The ACDC represented as a JSON string (no indentation)."""
        return self.to_json()

    def __repr__(self):
        return f"ACDC(said='{self.said}')"
