#!/usr/bin/env python3
# keri_example.py - Example workflow for the KERI Thank You Certificate system

import os

from adapter.keri.certificate import ThankYouCertificate
from adapter.keri.identity import Identity

def main():
    # Base directory for KERI data
    base_dir = "./keri_example_data"
    os.makedirs(base_dir, exist_ok=True)
    
    # 1. Create identities for issuer and recipient
    print("\n1. Creating identities...")
    issuer = Identity("example_issuer", base_dir)
    issuer.create()
    
    recipient = Identity("example_recipient", base_dir)
    recipient.create()
    
    # 2. Issue a thank you certificate
    print("\n2. Issuing a Thank You certificate...")
    cert_handler = ThankYouCertificate(base_dir)
    cert_file = cert_handler.issue(
        issuer,
        "John Doe", 
        "Thank you for your outstanding contribution to our project!",
        recipient.hab.pre  # We know the recipient's AID
    )
    
    # 3. Verify the certificate
    print("\n3. Verifying the certificate...")
    verification = cert_handler.verify(cert_file, recipient)
    
    # 4. Acknowledge the certificate
    if verification["valid"]:
        print("\n4. Acknowledging the certificate...")
        cert_handler.acknowledge(cert_file, recipient)
    
    # 5. Rotate keys for the issuer
    print("\n5. Rotating keys for the issuer...")
    issuer.rotate_keys()
    
    # 6. List all certificates
    print("\n6. Listing all certificates...")
    certs = cert_handler.list_certificates()
    if certs:
        print(f"Found {len(certs)} certificate(s)")
    else:
        print("No certificates found.")
    
    print("\nExample complete!")

if __name__ == "__main__":
    main()