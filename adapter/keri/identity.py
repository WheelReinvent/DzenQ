# identity.py - KERI identity creation and management
import os
import json
import platform
import shutil
from pathlib import Path

# Apply Windows fixes before importing KERI modules
if platform.system() == 'Windows':
    from adapter.keri.windows_fix import apply_windows_fixes
    apply_windows_fixes()

from keri.core import coring, serdering
from keri.app import habbing, directing


class Identity:
    """Manages KERI identities with key generation, rotation, and witnessing capabilities"""
    
    def __init__(self, name, base_dir="./keri_data", witness_urls=None, tcp=5620, local=False):
        """Initialize a KERI identity with persistent storage
        
        Args:
            name (str): Name for this identity
            base_dir (str): Base directory for storing KERI databases
            witness_urls (list): Optional list of witness URLs for witnessing
            tcp (int): TCP port for local server if needed
            local (bool): Use local mode without witnesses if True
        """
        self.name = name
        self.base_dir = base_dir
        self.hab = None
        self.habery = None
        self.witness_urls = witness_urls or []
        self.tcp = tcp
        self.local = local
        
        # Ensure base directory exists
        os.makedirs(base_dir, exist_ok=True)
        
        # Path to store identity information for this instance
        self.id_path = os.path.join(base_dir, f"{name}_id.json")
    
    def create(self, transferable=True, witnesses=0, isith="1", nsith="1"):
        """Create a new KERI identity with habitat
        
        Args:
            transferable (bool): Whether keys can be rotated (usually True)
            witnesses (int): Number of witnesses to use (0 for local/direct mode)
            isith (str): Initial signing threshold (n-of-m or fractional)
            nsith (str): Next signing threshold
            
        Returns:
            str: The identity prefix (AID)
        """
        # Setup Habery for key storage and identity management
        self.habery = habbing.Habery(name=self.name, 
                                    base=self.base_dir,
                                    temp=False)
        
        # Set up witness configuration if needed
        witness_config = None
        if not self.local and witnesses > 0 and self.witness_urls:
            witness_config = dict(
                # Use a subset of the provided witness URLs based on the count
                toad=str(max(1, round(witnesses * 2 / 3))),  # 2/3 threshold for witnesses as string
                wits=self.witness_urls[:witnesses]
            )
        
        # Create the habitat using the Habery with witness config if provided
        if witness_config:
            print(f"Using {witnesses} witnesses with threshold {witness_config['toad']}")
            self.hab = self.habery.makeHab(
                name=self.name,
                transferable=transferable,
                isith=isith,
                icount=1 if isith == "1" else int(isith),
                nsith=nsith,
                ncount=1 if nsith == "1" else int(nsith),
                wits=witness_config["wits"],
                toad=witness_config["toad"]
            )
        else:
            print("Creating identity in local/direct mode (no witnesses)")
            self.hab = self.habery.makeHab(
                name=self.name,
                transferable=transferable,
                isith=isith,
                icount=1 if isith == "1" else int(isith),
                nsith=nsith,
                ncount=1 if nsith == "1" else int(nsith)
            )
        
        # Save identity information to file
        id_info = {
            "name": self.name,
            "prefix": self.hab.pre,
            "transferable": transferable,
            "witness_urls": self.witness_urls[:witnesses] if witnesses > 0 else [],
            "local": self.local or witnesses == 0,
            "tcp": self.tcp
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
        
        # Load configuration from file
        with open(self.id_path, "r") as f:
            try:
                id_info = json.load(f)
                self.witness_urls = id_info.get("witness_urls", [])
                self.local = id_info.get("local", True)
                self.tcp = id_info.get("tcp", 5620)
            except json.JSONDecodeError as e:
                print(f"Error reading identity file: {e}")
                return False
        
        # Create Habery for identity management
        self.habery = habbing.Habery(name=self.name, base=self.base_dir, temp=False)
        
        # Try to load the identity
        try:
            self.hab = next(iter(self.habery.habs.values()), None)
            if not self.hab:
                print(f"No identity found for '{self.name}'")
                return False
            
            print(f"Identity loaded: {self.name}")
            print(f"Identifier (AID): {self.hab.pre}")
            
            # If we have witness URLs and not in local mode, set up to use witnesses
            if not self.local and self.witness_urls:
                print(f"Using witnesses: {', '.join(self.witness_urls)}")
            else:
                print("Operating in local/direct mode (no witnesses)")
            
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
            
            # Update the saved info
            id_info = {
                "name": self.name,
                "prefix": self.hab.pre,
                "transferable": True,
                "witness_urls": self.witness_urls,
                "local": self.local,
                "tcp": self.tcp
            }
            
            with open(self.id_path, "w") as f:
                json.dump(id_info, f, indent=2)
                
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
        
    def backup(self, backup_dir):
        """Backup the identity's keystore and database
        
        Args:
            backup_dir (str): Directory to store backup
            
        Returns:
            bool: Success or failure
        """
        if not self.hab:
            print("No identity loaded. Use create() or load() first.")
            return False
            
        try:
            # Create backup directory if it doesn't exist
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup the KERI database directory for this identity
            db_dir = Path(self.base_dir) / f"{self.name}"
            if db_dir.exists():
                backup_db_dir = backup_path / f"{self.name}_db"
                if backup_db_dir.exists():
                    shutil.rmtree(backup_db_dir)
                shutil.copytree(db_dir, backup_db_dir)
                
            # Backup the identity info file
            id_file = Path(self.id_path)
            if id_file.exists():
                shutil.copy2(id_file, backup_path / id_file.name)
                
            print(f"Identity backup completed to: {backup_dir}")
            return True
        except Exception as e:
            print(f"Error backing up identity: {e}")
            return False
            
    def restore(self, backup_dir):
        """Restore the identity from a backup
        
        Args:
            backup_dir (str): Directory containing the backup
            
        Returns:
            bool: Success or failure
        """
        try:
            backup_path = Path(backup_dir)
            
            # Check if backup exists
            backup_db_dir = backup_path / f"{self.name}_db"
            backup_id_file = backup_path / f"{self.name}_id.json"
            
            if not backup_db_dir.exists() or not backup_id_file.exists():
                print(f"Backup not found in: {backup_dir}")
                return False
                
            # Restore the database
            db_dir = Path(self.base_dir) / f"{self.name}"
            if db_dir.exists():
                shutil.rmtree(db_dir)
            shutil.copytree(backup_db_dir, db_dir)
            
            # Restore the identity info file
            shutil.copy2(backup_id_file, self.id_path)
            
            print(f"Identity restored from: {backup_dir}")
            return self.load()  # Load the restored identity
        except Exception as e:
            print(f"Error restoring identity: {e}")
            return False

    def publish_to_witnesses(self):
        """Publish identity to witnesses if using witness mode
        
        Returns:
            bool: Success or failure 
        """
        if not self.hab:
            print("No identity loaded. Use create() or load() first.")
            return False
            
        if self.local or not self.witness_urls:
            print("Not using witnesses (local mode). Nothing to publish.")
            return True
            
        try:
            # Create a client director to communicate with witnesses
            with directing.Director(hab=self.hab, doers=[]) as director:
                # Tell director to send the identity information to witnesses
                director.wind(self.hab.kever.prefixer.qb64)  # send KEL to witnesses
                print(f"Published identity to witnesses")
                return True
        except Exception as e:
            print(f"Error publishing to witnesses: {e}")
            return False