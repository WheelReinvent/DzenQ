from typing import List, Dict, Any, Optional, TYPE_CHECKING
import json

if TYPE_CHECKING:
    from .acdc import ACDC

class Presentation:
    """
    Represents a credential presentation with logical selective disclosure.
    
    In this implementation:
    - The full ACDC credential is required for cryptographic verification.
    - 'Selective Disclosure' is implemented as a logical view (disclosed_attributes).
    - The receiver uses 'disclosed_attributes' for business logic, but verifies the full credential.
    """
    
    def __init__(self, credential: 'ACDC', disclose_fields: Optional[List[str]] = None):
        """
        Initialize a Presentation.
        
        Args:
            credential (ACDC): The full credential to present.
            disclose_fields (list): List of attribute names to disclose. 
                                    If None, all attributes are disclosed.
        """
        self.credential = credential
        self._disclose_fields = disclose_fields
        
    @property
    def attributes(self) -> Dict[str, Any]:
        """
        Get the disclosed attributes.
        """
        full_attrs = self.credential.attributes
        if self._disclose_fields is None:
            return full_attrs
            
        return {k: v for k, v in full_attrs.items() if k in self._disclose_fields}
        
    @property
    def disclosed_fields(self) -> List[str]:
        """List of fields that are visible."""
        return list(self.attributes.keys())

    def to_json(self) -> str:
        """
        Serialize the presentation structure (credential + metadata).
        """
        return json.dumps({
            "credential": self.credential.data, # The raw SAD
            "disclosed_fields": self._disclose_fields
        })

    def verify(self) -> bool:
        """
        Verify the integrity of the underlying credential.
        
        Returns:
            bool: True if valid.
        """
        # 1. Verify SAID integrity
        if not self.credential.verify():
            return False
            
        # 2. Verify Schema compliance (if possible)
        # self.credential.verify_schema() 
        
        # 3. Check Revocation
        if self.credential.is_revoked():
            return False
            
        return True

    def __repr__(self):
        return f"Presentation(credential={self.credential.said}, disclosed={self.disclosed_fields})"
