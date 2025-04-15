#!/usr/bin/env python3
# create_identity.py - Create a new KERI identity

import os
import sys
import argparse
import platform

# Add parent directory to path so we can import adapter.keri module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Apply Windows fixes before importing anything from KERI
if platform.system() == 'Windows':
    from adapter.keri.windows_fix import apply_windows_fixes
    apply_windows_fixes()

from adapter.keri.identity import Identity

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Create a new KERI identity")
    parser.add_argument("name", help="Name for the identity (e.g., issuer, recipient)")
    parser.add_argument("--dir", default="./keri_data", help="Base directory for storing KERI data")
    parser.add_argument("--non-transferable", action="store_true", 
                        help="Create a non-transferable identity (keys cannot be rotated)")
    
    args = parser.parse_args()
    
    # Create the identity
    identity = Identity(args.name, args.dir)
    identity.create(transferable=not args.non_transferable)
    
    print("\nIdentity created successfully!")
    
if __name__ == "__main__":
    main()