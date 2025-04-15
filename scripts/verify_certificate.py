#!/usr/bin/env python3
# verify_certificate.py - Verify a Thank You certificate

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
    parser = argparse.ArgumentParser(description="Verify a Thank You certificate")
    parser.add_argument("certificate", help="Path to the certificate file")
    parser.add_argument("--recipient", help="Name of the recipient identity (for full verification)")
    parser.add_argument("--dir", default="./keri_data", help="Base directory for KERI data")
    parser.add_argument("--acknowledge", action="store_true", 
                        help="Acknowledge the certificate (requires --recipient)")
    parser.add_argument("--import", dest="import_file", 
                        help="Import a certificate from an exported format before verifying")
    
    args = parser.parse_args()
    
    # Initialize certificate handler
    cert_handler = ThankYouCertificate(args.dir)
    
    # Import the certificate if requested
    cert_path = args.certificate
    if getattr(args, "import_file"):
        imported_cert = cert_handler.import_certificate(args.import_file)
        if imported_cert:
            cert_path = imported_cert
        else:
            print("Failed to import certificate")
            return 1
    
    # Load recipient identity if provided
    recipient = None
    if args.recipient:
        recipient = Identity(args.recipient, args.dir)
        if not recipient.load():
            print(f"Could not load recipient identity '{args.recipient}'")
            print(f"Create it first with: python scripts/create_identity.py {args.recipient}")
            if args.acknowledge:
                return 1
    
    # Verify the certificate
    verification = cert_handler.verify(cert_path, recipient)
    
    # If not valid, exit with error
    if not verification["valid"]:
        print(f"Certificate verification failed: {verification.get('error', 'Unknown error')}")
        return 1
    
    # If requested and possible, acknowledge the certificate
    if args.acknowledge and verification["valid"] and recipient:
        if cert_handler.acknowledge(cert_path, recipient):
            print("\nCertificate successfully acknowledged!")
        else:
            print("\nFailed to acknowledge certificate")
            return 1
    
    # Return successful verification
    print("\nCertificate verification successful!")
    return 0
    
if __name__ == "__main__":
    sys.exit(main())