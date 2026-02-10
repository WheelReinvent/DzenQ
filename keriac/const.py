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
