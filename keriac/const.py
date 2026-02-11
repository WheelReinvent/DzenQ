class Fields:
    """
    KERI/ACDC Field Labels.
    """
    # Common
    VERSION = "v"
    TYPE = "t"       # Ilk
    SAID = "d"       # Digest

    # KERI Events
    PREFIX = "i"     # Issuer / Prefix
    SEQUENCE = "s"   # Sequence Number (hex)
    PRIOR = "p"      # Prior Event Digest
    KEYS = "k"       # Signing Keys
    NEXT_KEYS = "n"  # Next Key Digest
    THRESHOLD = "kt" # Key Threshold
    NEXT_THRESHOLD = "nt" # Next Key Threshold
    WITNESSES = "b"  # Backers / Witnesses
    WITNESS_THRESHOLD = "bt" # Backer Threshold
    CUTS = "c"       # Witnesses to cut
    ADDS = "ba"      # Witnesses to add
    SEALS = "a"      # Anchors / Seals

    # ACDC
    ISSUER = "i"     # Issuer AID
    SCHEMA = "s"     # Schema SAID
    ATTRIBUTES = "a" # Attributes block
    RECIPIENT = "ri" # Recipient
    REGISTRY = "r"   # Registry
    RULES = "e"      # Rules


class Schemas:
    """
    Standard KERI/vLEI Schema SAIDs.
    Normative SAIDs for GLEIF vLEI Trust Chain.
    """
    # vLEI Trust Chain
    QVI = "EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao"
    LE = "ENPXp1vQzRF6JwIuS-mp2U8Uf1MoADoP_GqQ62VsDZWY"
    
    # Official Organizational Role (OOR)
    OOR_AUTH = "EKA57bKBKxr_kN7iN5i7lMUxpMG-s19dRcmov1iDxz-E"
    OOR = "EBNaNu-M9P5cgrnfl2Fvymy4E_jvxxyjb70PRtiANlJy"
    
    # Engagement Context Role (ECR)
    ECR_AUTH = "EH6ekLjSr8V32WyFbGe1zXjTzFs9PkTYmupJ9H65O14g"
    ECR = "EEy9PkikFcANV1l7EHukCeXqrzT1hNZjGlUk7wuMO4jw"
