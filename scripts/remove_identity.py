#!/usr/bin/env python3
# remove_identity.py - Remove a KERI identity and its data

import os
import sys
import argparse
import platform
import shutil
from pathlib import Path

# Add parent directory to path so we can import adapter.keri module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Apply Windows fixes before importing anything from KERI
if platform.system() == 'Windows':
    from adapter.keri.windows_fix import apply_windows_fixes
    apply_windows_fixes()

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Remove a KERI identity and its data")
    parser.add_argument("name", help="Name of the identity to remove")
    parser.add_argument("--dir", default="./keri_data", help="Base directory for KERI data")
    parser.add_argument("--backup", help="Backup the identity to this directory before removal")
    parser.add_argument("--force", action="store_true", help="Remove without confirmation")
    
    args = parser.parse_args()
    
    # Setup paths
    base_dir = Path(args.dir)
    id_file = base_dir / f"{args.name}_id.json"
    db_dir = base_dir / f"{args.name}"
    
    # Check if the identity exists
    if not id_file.exists() and not db_dir.exists():
        print(f"Identity '{args.name}' not found in {args.dir}")
        return 1
    
    # List what will be removed
    to_remove = []
    if id_file.exists():
        to_remove.append(str(id_file))
    if db_dir.exists():
        to_remove.append(str(db_dir))
    
    # Backup if requested
    if args.backup:
        backup_path = Path(args.backup)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Backup identity information file
            if id_file.exists():
                shutil.copy2(id_file, backup_path / id_file.name)
                
            # Backup the identity's database directory
            if db_dir.exists():
                backup_db_dir = backup_path / f"{args.name}_db"
                if backup_db_dir.exists():
                    shutil.rmtree(backup_db_dir)
                shutil.copytree(db_dir, backup_db_dir)
                
            print(f"Identity backup completed to: {args.backup}")
        except Exception as e:
            print(f"Error backing up identity: {e}")
            if not args.force:
                if input("Continue with removal despite backup failure? (y/n): ").lower() != 'y':
                    print("Removal cancelled")
                    return 1
    
    # Confirm removal
    if not args.force:
        print(f"The following will be removed:")
        for item in to_remove:
            print(f"  - {item}")
        
        if input("Proceed with removal? (y/n): ").lower() != 'y':
            print("Removal cancelled")
            return 0
    
    # Perform removal
    try:
        if id_file.exists():
            id_file.unlink()
            print(f"Removed {id_file}")
            
        if db_dir.exists():
            shutil.rmtree(db_dir)
            print(f"Removed directory {db_dir}")
            
        print(f"Identity '{args.name}' has been removed")
        return 0
    except Exception as e:
        print(f"Error removing identity: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())