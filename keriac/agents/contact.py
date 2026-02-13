"""
Discovery module for OOBI (Out-of-Band Introduction) support.

Provides the Card abstraction for discovering and resolving remote Identities.
"""
from typing import Optional
from typing_extensions import Self
import requests
from keri.core import eventing
from keri.app import habbing
from keri.core import serdering
from keri.core.counting import Counter
from keri.core.indexing import Siger

from .identity import Identity

class Card:
    """
    A Card represents an Out-of-Band Introduction (OOBI) locator.
    
    It contains a URL that points to a KEL (Key Event Log) for an Identity.
    The Card can be resolved to obtain a Remote Identity instance.
    """
    
    def __init__(self, url: str):
        """
        Initialize a Card with an OOBI URL.
        
        Args:
            url (str): The OOBI URL pointing to a KEL.
        """
        self.url = url
    
    def resolve(self, name: Optional[str] = None, temp: bool = True) -> Identity:
        """
        Resolve this Card to obtain a Remote Identity View.
        
        Args:
            name (str, optional): Alias for the resolved identity.
            temp (bool): Whether to use temporary storage.
            
        Returns:
            Identity: A Remote Identity View instance.
        """
        # 1. Fetch KEL from URL
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            raise ValueError(f"Failed to fetch OOBI from {self.url}: {e}")
        
        # 2. Validate content type
        content_type = response.headers.get('Content-Type', '')
        if 'application/json+cesr' not in content_type:
            raise ValueError(f"Invalid OOBI response content type: {content_type}")
        
        # 3. Use Identity.observe to process the content and return a View
        # We pass the raw content (messagized KEL)
        return Identity.observe(response.content)
    
    @staticmethod
    def issue(identity: Identity, role: str = "controller") -> Self:
        """
        Generate a Card for the given Identity.
        
        Args:
            identity (Identity): The Identity to create a Card for.
            role (str): The role for the OOBI (default: "controller").
            
        Returns:
            Card: A new Card instance with the OOBI URL.
            
        Raises:
            ValueError: If the Identity is Remote (no keys).
        """
        if not identity.is_controller:
            raise ValueError("Cannot issue Card for Remote Identity (no keys)")
        
        # Generate OOBI URL
        # Format: http://localhost:5623/oobi/{aid}/{role}
        # For now, we'll use a placeholder base URL
        # In production, this would come from configuration
        base_url = "http://localhost:5623"
        oobi_url = f"{base_url}/oobi/{identity.aid}/{role}"
        
        return Card(oobi_url)
    
    def __repr__(self):
        return f"Card(url='{self.url}')"
