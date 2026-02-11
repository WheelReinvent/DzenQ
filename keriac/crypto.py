"""
Cryptographic primitives for KERI operations.
Uses academic terminology from KERI whitepapers.
"""
from typing import TYPE_CHECKING

from keri.core.signing import Signer as KeriSigner, Siger as KeriSiger
from keri.core.coring import Verfer as KeriVerfer

from .base import Serializable

if TYPE_CHECKING:
    pass


class PublicKey(str, Serializable):
    """
    A public key verifier (academic: Verifier).
    Wraps KERI's Verfer with a clean, serializable interface.
    """
    
    def __new__(cls, qb64: str):
        """Create new PublicKey string instance."""
        return str.__new__(cls, qb64)
    
    def __init__(self, qb64: str):
        """Initialize from qb64 public key string."""
        self._verfer = KeriVerfer(qb64=qb64)
    
    @property
    def qb64(self) -> str:
        """Base64 qualified representation."""
        return self._verfer.qb64
    
    @property
    def size(self) -> int:
        """Binary size of public key."""
        return len(self._verfer.qb2)
    
    def serialize(self) -> bytes:
        """Return binary CESR (qb2) representation."""
        return self._verfer.qb2
    
    @classmethod
    def deserialize(cls, raw: bytes) -> "PublicKey":
        """Reconstruct PublicKey from binary bytes (qb2)."""
        verfer = KeriVerfer(qb2=raw)
        return cls(verfer.qb64)
    
    def verify(self, data: bytes, signature: 'Signature') -> bool:
        """
        Verify a signature over data.
        
        Args:
            data: The data that was signed.
            signature: The signature to verify.
            
        Returns:
            bool: True if signature is valid.
        """
        try:
            return self._verfer.verify(sig=signature._raw, ser=data)
        except Exception:
            return False
    
    def __str__(self):
        return self.qb64
    
    def __repr__(self):
        return f"PublicKey('{self.qb64[:16]}...')"


class Signature(str, Serializable):
    """
    A cryptographic signature (academic: Signature).
    Wraps KERI's Siger with a clean, serializable interface.
    """
    
    def __new__(cls, qb64: str):
        """Create new Signature string instance."""
        return str.__new__(cls, qb64)
    
    def __init__(self, qb64: str):
        """Initialize from qb64 signature string."""
        self._siger = KeriSiger(qb64=qb64)
    
    @property
    def qb64(self) -> str:
        """Base64 qualified representation."""
        return self._siger.qb64
    
    @property
    def _raw(self) -> bytes:
        """Raw signature bytes (internal use)."""
        return self._siger.raw
    
    @property
    def size(self) -> int:
        """Binary size of signature."""
        return len(self._siger.qb2)
    
    def serialize(self) -> bytes:
        """Return binary CESR (qb2) representation."""
        return self._siger.qb2
    
    @classmethod
    def deserialize(cls, raw: bytes) -> "Signature":
        """Reconstruct Signature from binary bytes (qb2)."""
        siger = KeriSiger(qb2=raw)
        return cls(siger.qb64)
    
    def __str__(self):
        return self.qb64
    
    def __repr__(self):
        return f"Signature('{self.qb64[:16]}...')"


class PrivateKey:
    """
    A private signing key (academic: Signing Key).
    Wraps KERI's Signer with a clean interface.
    
    SECURITY: This class does NOT extend Serializable.
    Private keys should never be serialized or transmitted.
    """
    
    def __init__(self, signer: KeriSigner):
        """Initialize from KERI Signer (internal use only)."""
        self._signer = signer
    
    def sign(self, data: bytes) -> Signature:
        """
        Sign data with this private key.
        
        Args:
            data: The data to sign.
            
        Returns:
            Signature: The cryptographic signature.
        """
        siger = self._signer.sign(ser=data)
        return Signature(siger.qb64)
    
    @property
    def public_key(self) -> PublicKey:
        """Get the corresponding public key."""
        return PublicKey(self._signer.verfer.qb64)
