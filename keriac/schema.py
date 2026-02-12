import json
from typing import Union, Dict, Optional, override
from keri.core import scheming
from .base import SAD, SAID
from .const import Schemas
from .types import SADDict, SchemaDict

class Schema(SAD):
    """
    Academic wrapper for KERI Schemas.
    Supports JSON Schema 2020-12 and SAIDification.
    """
    
    def __init__(self, raw_or_dict: Union[bytes, SchemaDict, dict, str]):
        """
        Initialize a Schema.
        
        Args:
            raw_or_dict: The raw JSON bytes, a dictionary of the schema, 
                         or a JSON string.
        """
        if isinstance(raw_or_dict, Schema):
            self._schemer = raw_or_dict._schemer
        elif isinstance(raw_or_dict, dict):
            self._schemer = scheming.Schemer(sed=raw_or_dict)
        elif isinstance(raw_or_dict, (bytes, bytearray, memoryview)):
            self._schemer = scheming.Schemer(raw=bytes(raw_or_dict))
        elif isinstance(raw_or_dict, str):
            self._schemer = scheming.Schemer(raw=raw_or_dict.encode("utf-8"))
        else:
            raise ValueError(f"Unsupported type for Schema initialization: {type(raw_or_dict)}")

    @property
    def data(self) -> SADDict:
        """The underlying JSON Schema dictionary."""
        return self._schemer.sed

    @property
    def said(self) -> SAID:
        """The Self-Addressing Identifier (SAID) of the schema."""
        return SAID(self._schemer.said)

    @property
    def raw(self) -> bytes:
        """The raw bytes serialization of the schema (CESR)."""
        return self._schemer.raw

    def validate(self, data: bytes | dict) -> bool:
        """
        Verify that the provided raw data (JSON bytes) conforms to this schema.
        
        Args:
            data: Raw serialization of the data to verify.
            
        Returns:
            bool: True if valid.
        """
        from keri import kering
        if isinstance(data, dict):
            data = json.dumps(data).encode("utf-8")
        try:
            return self._schemer.verify(raw=data)
        except (kering.ValidationError, Exception):
            return False


    def __repr__(self):
        return f"Schema(said='{self.said}')"


class SchemaRegistry:
    """
    Global registry for KERI schemas.
    Allows accessing schemas by SAID or friendly aliases.
    """
    _instance = None
    _schemas: Dict[str, Schema] = {}
    _aliases: Dict[str, str] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SchemaRegistry, cls).__new__(cls)
            cls._instance._preload_vlei()
        return cls._instance

    def register(self, schema: Schema, alias: Optional[str] = None):
        """Register a schema in the registry."""
        self._schemas[schema.said] = schema
        if alias:
            self._aliases[alias.lower()] = schema.said

    def get(self, key: str) -> Optional[Schema]:
        """
        Retrieve a schema by alias or SAID.
        """
        # Try alias first
        said = self._aliases.get(key.lower())
        if said:
            return self._schemas.get(said)
        
        # Try SAID directly
        return self._schemas.get(key)

    def resolve_said(self, key: str) -> str:
        """
        Resolve a key (alias or SAID) to a SAID string.
        """
        # If it's a Schema object, it might have been passed directly (though ACDC handles this)
        if hasattr(key, 'said'):
            return key.said

        # 1. Is it a known alias?
        said = self._aliases.get(key.lower())
        if said:
            return said
        
        # 2. Is it already a SAID? (Basic check - starts with E)
        if isinstance(key, str) and key.startswith("E") and len(key) >= 44:
            return key
            
        # 3. Return as-is (might be a raw SAID or invalid)
        return key

    def _preload_vlei(self):
        """Pre-load standard vLEI SAIDs as stubs if they aren't fully resolved yet."""
        # For now, we map aliases to the known SAIDs.
        # Note: In a real system, we might need to fetch the actual schema content
        # to perform validation. Here we provide the registry for alias resolution.
        self._aliases["qvi"] = Schemas.QVI
        self._aliases["vlei_issuer"] = Schemas.QVI
        self._aliases["le"] = Schemas.LE
        self._aliases["legal_entity"] = Schemas.LE
        self._aliases["oor_auth"] = Schemas.OOR_AUTH
        self._aliases["oor"] = Schemas.OOR
        self._aliases["ecr_auth"] = Schemas.ECR_AUTH
        self._aliases["ecr"] = Schemas.ECR

# Global singleton
schema_registry = SchemaRegistry()
