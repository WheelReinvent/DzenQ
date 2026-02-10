
class SAID(str):
    """
    Self-Addressing Identifier (SAID).
    Inherits from str for easy usage as a string while providing utility methods.
    """

    def __repr__(self):
        return f"SAID('{str(self)}')"
