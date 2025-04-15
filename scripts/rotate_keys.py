#!/usr/bin/env python3
# rotate_keys.py - Rotate keys for an existing KERI identity

import os
import sys
import argparse
import platform

# Add parent directory to path so we can import adapter.keri module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Apply Windows fixes before importing any KERI modules
if platform.system() == 'Windows':
    from adapter.keri.windows_fix import apply_windows_fixes
    apply_windows_fixes()

from adapter.keri.identity import Identity

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Rotate keys for a KERI identity")
    parser.add_argument("name", help="Name of the identity to rotate keys for")
    parser.add_argument("--dir", default="./keri_data", help="Base directory for KERI data")
    parser.add_argument("--publish", action="store_true", 
                        help="Publish rotation event to witnesses")
    parser.add_argument("--backup", help="Backup the identity to this directory before rotation")
    
    args = parser.parse_args()
    
    # Load the identity
    identity = Identity(args.name, args.dir)
    if not identity.load():
        print(f"Could not load identity '{args.name}'")
        print(f"Create it first with: python scripts/create_identity.py {args.name}")
        return 1
    
    # Backup first if requested
    if args.backup:
        if identity.backup(args.backup):
            print(f"Identity backed up to: {args.backup}")
        else:
            print(f"Failed to backup identity to: {args.backup}")
            if input("Continue with key rotation without backup? (y/n): ").lower() != 'y':
                print("Rotation cancelled")
                return 1
    
    # Rotate the keys
    if identity.rotate_keys():
        print("\nKeys rotated successfully!")
        
        # Publish to witnesses if requested
        if args.publish and not identity.local and identity.witness_urls:
            if identity.publish_to_witnesses():
                print("Rotation event published to witnesses")
            else:
                print("Failed to publish rotation to witnesses")
        
        return 0
    else:
        print("Key rotation failed")
        return 1
    
if __name__ == "__main__":
    sys.exit(main())