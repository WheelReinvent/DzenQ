from typing import Union, TYPE_CHECKING
from keri.core import coring

if TYPE_CHECKING:
    from .base import SAD

class SAID(str):
    """
    Self-Addressing Identifier (SAID).
    Inherits from str for easy usage as a string while providing utility methods.
    """

    @classmethod
    def from_data(cls, target: Union[dict, 'SAD'], label: str = coring.Saids.d) -> 'SAID':
        """
        Calculate the SAID for a dictionary or a SAD object and return a SAID instance.
        
        Args:
            target (dict | SAD): The data to calculate the SAID for.
            label (str): The field label for the SAID (default is 'd').
            
        Returns:
            SAID: The calculated SAID.
        """
        # Avoid circular import if SAD import is needed at runtime
        from .base import SAD
        
        sad_dict = target.data if isinstance(target, SAD) else target
        
        # Saider.saidify does not modify the original dict, it returns a new one
        saider, _ = coring.Saider.saidify(sad=sad_dict, label=label)
        return cls(saider.qb64)

    def verify(self, target: Union[dict, 'SAD'], label: str = coring.Saids.d) -> bool:
        """
        Verify that this SAID correctly matches the target data.
        
        Args:
            target (dict | SAD): The data to verify.
            label (str): The field label where the SAID is stored.
            
        Returns:
            bool: True if verified, False otherwise.
        """
        from .base import SAD
        sad_dict = target.data if isinstance(target, SAD) else target
        
        try:
            saider = coring.Saider(qb64=str(self))
            return saider.verify(sad=sad_dict, label=label)
        except Exception:
            return False

    def __repr__(self):
        return f"SAID('{str(self)}')"
