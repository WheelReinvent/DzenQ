#!/usr/bin/env python3
# issue_certificate.py - Issue a Thank You certificate

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
from adapter.keri.certificate import ThankYouCertificate

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Issue a Thank You certificate")
    parser.add_argument("issuer", help="Name of the issuer identity")
    parser.add_argument("recipient", help="Name of the recipient")
    parser.add_argument("message", help="Thank you message")
    parser.add_argument("--recipient-aid", help="Recipient's KERI identifier (if known)")
    parser.add_argument("--dir", default="./keri_data", help="Base directory for KERI data")
    parser.add_argument("--export", help="Export the certificate to a portable format file")
    
    args = parser.parse_args()
    
    # Load the issuer's identity
    issuer = Identity(args.issuer, args.dir)
    if not issuer.load():
        print(f"Could not load issuer identity '{args.issuer}'")
        print(f"Create it first with: python scripts/create_identity.py {args.issuer}")
        return 1
    
    # Create and issue the certificate
    cert_handler = ThankYouCertificate(args.dir)
    cert_file = cert_handler.issue(issuer, args.recipient, args.message, args.recipient_aid)
    
    if not cert_file:
        print("Failed to issue certificate")
        return 1
        
    # Export the certificate if requested
    if args.export and cert_file:
        export_file = cert_handler.export_certificate(cert_file, args.export)
        if export_file:
            print(f"Certificate exported to: {args.export}")
    
    print("\nCertificate issued successfully!")
    return 0
    
if __name__ == "__main__":
    sys.exit(main())