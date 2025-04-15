#!/usr/bin/env python3
# rotate_keys.py - Rotate keys for an existing KERI identity

import os
import sys
import argparse

# Add parent directory to path so we can import keri module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from keri.identity import Identity

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Rotate keys for a KERI identity")
    parser.add_argument("name", help="Name of the identity to rotate keys for")
    parser.add_argument("--dir", default="./keri_data", help="Base directory for KERI data")
    
    args = parser.parse_args()
    
    # Load the identity
    identity = Identity(args.name, args.dir)
    if not identity.load():
        print(f"Could not load identity '{args.name}'")
        print(f"Create it first with: python scripts/create_identity.py {args.name}")
        return
    
    # Rotate the keys
    if identity.rotate_keys():
        print("\nKeys rotated successfully!")
    
if __name__ == "__main__":
    main()