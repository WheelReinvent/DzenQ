# identity.py - KERI identity creation and management
import os
import json
import platform

# Apply Windows fixes before importing KERI modules
if platform.system() == 'Windows':
    from adapter.keri.windows_fix import apply_windows_fixes
    apply_windows_fixes()

from keri.core import coring, eventing, serdering
from keri.app import habbing, keeping
# Update import to use basing instead of dbing for Baser class
from keri.db import basing


class Identity:
    """Manages KERI identities with key generation and rotation capabilities"""
    
    def __init__(self, name, base_dir="./keri_data"):
        """Initialize a KERI identity with persistent storage
        
        Args:
            name (str): Name for this identity
            base_dir (str): Base directory for storing KERI databases
        """
        self.name = name
        self.base_dir = base_dir
        self.hab = None
        
        # Ensure base directory exists
        os.makedirs(base_dir, exist_ok=True)
        
        # Path to store identity information for this instance
        self.id_path = os.path.join(base_dir, f"{name}_id.json")
    
    def create(self, transferable=True):
        """Create a new KERI identity with habitat
        
        Args:
            transferable (bool): Whether keys can be rotated (usually True)
            
        Returns:
            str: The identity prefix (AID)
        """
        # Setup keeper for key storage
        ks = keeping.Keeper(name=self.name, 
                            base=self.base_dir,
                            temp=False)
        
        # Setup baser for database
        db = basing.Baser(name=self.name, 
                         base=self.base_dir,
                         temp=False)
        
        # Create habitat
        # We use Habery to create a Hab now, with simplified parameters
        habery = habbing.Habery(name=self.name, base=self.base_dir, temp=False)
        
        # Create the habitat using the Habery
        self.hab = habery.makeHab(
            name=self.name,
            transferable=transferable,
            isith=1,    # Signature threshold of 1-of-1 keys
            icount=1,   # Initial number of keys
            nsith=1,    # Next signature threshold
            ncount=1    # Number of next pre-rotated keys
        )
        
        # Save identity information to file
        id_info = {
            "name": self.name,
            "prefix": self.hab.pre,
            "transferable": transferable,
        }
        
        with open(self.id_path, "w") as f:
            json.dump(id_info, f, indent=2)
        
        print(f"Identity created: {self.name}")
        print(f"Identifier (AID): {self.hab.pre}")
        print(f"Identity details saved to: {self.id_path}")
        
        return self.hab.pre
    
    def load(self):
        """Load an existing KERI identity
        
        Returns:
            bool: Success or failure
        """
        if not os.path.exists(self.id_path):
            print(f"Identity file not found: {self.id_path}")
            return False
            
        # Setup keeper for key storage
        ks = keeping.Keeper(name=self.name, 
                          base=self.base_dir,
                          temp=False)
        
        # Setup baser for database
        db = basing.Baser(name=self.name, 
                       base=self.base_dir,
                       temp=False)
                       
        # Load habitat from existing database
        try:
            # Create a Habery to load an existing Hab
            habery = habbing.Habery(name=self.name, base=self.base_dir, temp=False)
            # The loaded Hab should already be in habery.habs
            self.hab = next(iter(habery.habs.values()), None)
            print(f"Identity loaded: {self.name}")
            print(f"Identifier (AID): {self.hab.pre}")
            return True
        except Exception as e:
            print(f"Error loading identity: {e}")
            return False
    
    def rotate_keys(self):
        """Rotate the keys for this identity
        
        Returns:
            bool: Success or failure
        """
        if not self.hab:
            print("No identity loaded. Use create() or load() first.")
            return False
            
        if not self.hab.kever.transferable:
            print("This identity is not transferable (keys cannot be rotated)")
            return False
        
        try:
            # Create rotation event
            self.hab.rotate()
            print(f"Keys rotated successfully for {self.name}")
            return True
        except Exception as e:
            print(f"Error rotating keys: {e}")
            return False

    def get_kel(self):
        """Get the Key Event Log for this identity
        
        Returns:
            list: List of events in the KEL
        """
        if not self.hab:
            print("No identity loaded. Use create() or load() first.")
            return []
        
        # Get all events for this prefix from the database
        events = []
        for event_dig in self.hab.db.getKelIter(self.hab.pre):
            event_bytes = self.hab.db.getEvt(diger=coring.Diger(qb64=event_dig))
            if event_bytes:
                serder = serdering.SerderKERI(raw=event_bytes)
                events.append(serder.ked)
        
        return events
