from typing import Union, Self
from keri.core import coring

class SAID(str):
    """
    Self-Addressing Identifier (SAID).
    Inherits from str for easy usage as a string while providing utility methods.
    """

    @classmethod
    def from_data(cls, target: dict, label: str = coring.Saids.d) -> Self:
        """
        Calculate the SAID for a dictionary and return a SAID instance.
        
        Args:
            target (dict): The data dictionary to calculate the SAID for.
            label (str): The field label for the SAID (default is 'd').
            
        Returns:
            SAID: The calculated SAID.
        """
        # Saider.saidify does not modify the original dict, it returns a new one
        saider, _ = coring.Saider.saidify(sad=target, label=label)
        return cls(saider.qb64)

    def verify(self, target: dict, label: str = coring.Saids.d) -> bool:
        """
        Verify that this SAID correctly matches the target data.
        
        Args:
            target (dict): The data dictionary to verify.
            label (str): The field label where the SAID is stored.
            
        Returns:
            bool: True if verified, False otherwise.
        """
        try:
            saider = coring.Saider(qb64=str(self))
            return saider.verify(sad=target, label=label)
        except Exception:
            return False

    def __repr__(self):
        return f"SAID('{str(self)}')"
