from typing import Union
from keri.core import coring
from .base import SAD

class SAID:
    """
    Utility for calculating and verifying Self-Addressing Identifiers (SAIDs).
    """

    @staticmethod
    def calculate(target: Union[dict, SAD], label: str = coring.Saids.d) -> str:
        """
        Calculate the SAID for a dictionary or a SAD object.
        
        Args:
            target (dict | SAD): The data to calculate the SAID for.
            label (str): The field label for the SAID (default is 'd').
            
        Returns:
            str: The calculated qb64 SAID.
        """
        sad_dict = target.data if isinstance(target, SAD) else target
        
        # Saider.saidify does not modify the original dict, it returns a new one
        saider, _ = coring.Saider.saidify(sad=sad_dict, label=label)
        return saider.qb64

    @staticmethod
    def verify(target: Union[dict, SAD], said: str, label: str = coring.Saids.d) -> bool:
        """
        Verify that the provided SAID correctly matches the target data.
        
        Args:
            target (dict | SAD): The data to verify.
            said (str): The SAID to check against.
            label (str): The field label where the SAID is stored.
            
        Returns:
            bool: True if verified, False otherwise.
        """
        sad_dict = target.data if isinstance(target, SAD) else target
        
        try:
            saider = coring.Saider(qb64=said)
            return saider.verify(sad=sad_dict, label=label)
        except Exception:
            return False
