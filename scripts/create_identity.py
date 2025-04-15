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
    parser.add_argument("--witnesses", type=int, default=0,
                        help="Number of witnesses to use (0 for local mode)")
    parser.add_argument("--witness-urls", nargs="+", 
                        help="List of witness URLs to use (e.g., tcp://witness1.example.com:5620)")
    parser.add_argument("--isith", default="1",
                        help="Initial signing threshold (n-of-m or fractional)")
    parser.add_argument("--nsith", default="1", 
                        help="Next signing threshold")
    parser.add_argument("--local", action="store_true",
                        help="Force local mode (no witnesses)")
    parser.add_argument("--tcp", type=int, default=5620,
                        help="TCP port for local server if needed")
    parser.add_argument("--publish", action="store_true",
                        help="Publish to witnesses after creation")
    
    args = parser.parse_args()
    
    # Set up witness URLs
    witness_urls = args.witness_urls or []
    
    # Create the identity
    identity = Identity(args.name, args.dir, witness_urls=witness_urls, tcp=args.tcp, local=args.local)
    prefix = identity.create(
        transferable=not args.non_transferable,
        witnesses=args.witnesses,
        isith=args.isith,
        nsith=args.nsith
    )
    
    # Publish to witnesses if requested
    if args.publish and args.witnesses > 0 and witness_urls:
        identity.publish_to_witnesses()
    
    print("\nIdentity created successfully!")
    print(f"Identifier (AID): {prefix}")
    
if __name__ == "__main__":
    main()