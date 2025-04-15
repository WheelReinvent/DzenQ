# identity.py - KERI identity creation and management
import os
import json
from keri.core import coring, eventing
from keri.app import habbing, keeping
from keri.db import dbing


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
        db = dbing.Baser(name=self.name, 
                         base=self.base_dir,
                         temp=False)
        
        # Create habitat with:
        # isith=1, nsith=1: Signature threshold of 1-of-1 keys
        # icount=1: Initial number of keys
        # ncount=1: Number of next pre-rotated keys
        self.hab = habbing.Habitat(
            name=self.name,
            ks=ks,
            db=db,
            isith=1,
            icount=1,
            nsith=1,
            ncount=1,
            transferable=transferable,
            temp=False
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
        db = dbing.Baser(name=self.name, 
                       base=self.base_dir,
                       temp=False)
                       
        # Load habitat from existing database
        try:
            self.hab = habbing.Habitat(
                name=self.name,
                ks=ks,
                db=db,
                temp=False
            )
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
                serder = coring.Serder(raw=event_bytes)
                events.append(serder.ked)
        
        return events
