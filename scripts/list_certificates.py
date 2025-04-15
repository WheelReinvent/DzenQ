#!/usr/bin/env python3
# list_certificates.py - List all stored certificates

import os
import sys
import argparse
import json

# Add parent directory to path so we can import keri module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from keri.certificate import ThankYouCertificate

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="List all stored certificates")
    parser.add_argument("--dir", default="./keri_data", help="Base directory for KERI data")
    parser.add_argument("--details", action="store_true", help="Show certificate details")
    
    args = parser.parse_args()
    
    # Initialize certificate handler
    cert_handler = ThankYouCertificate(args.dir)
    
    # List certificates
    certs = cert_handler.list_certificates()
    
    if not certs:
        print("No certificates found.")
        return
        
    print(f"Found {len(certs)} certificate(s):")
    for i, cert_file in enumerate(certs, 1):
        print(f"\n{i}. {cert_file}")
        
        if args.details:
            # Load and display certificate details
            try:
                full_path = os.path.join(args.dir, "certificates", cert_file)
                with open(full_path, "r") as f:
                    cert_data = json.load(f)
                    
                cert_content = cert_data.get("certificate", {})
                print(f"   Issuer: {cert_data.get('issuer_aid', 'Unknown')}")
                print(f"   Recipient: {cert_content.get('recipient_name', 'Unknown')}")
                print(f"   Issued at: {cert_content.get('issued_at', 'Unknown')}")
                print(f"   Message: {cert_content.get('message', 'No message')}")
            except Exception as e:
                print(f"   Error reading certificate: {e}")
    
if __name__ == "__main__":
    main()