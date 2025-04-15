#!/usr/bin/env python3
# issue_certificate.py - Issue a Thank You certificate

import os
import sys
import argparse

# Add parent directory to path so we can import adapter.keri module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    
    args = parser.parse_args()
    
    # Load the issuer's identity
    issuer = Identity(args.issuer, args.dir)
    if not issuer.load():
        print(f"Could not load issuer identity '{args.issuer}'")
        print(f"Create it first with: python scripts/create_identity.py {args.issuer}")
        return
    
    # Create and issue the certificate
    cert_handler = ThankYouCertificate(args.dir)
    cert_file = cert_handler.issue(issuer, args.recipient, args.message, args.recipient_aid)
    
    if cert_file:
        print("\nCertificate issued successfully!")
    
if __name__ == "__main__":
    main()