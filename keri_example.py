#!/usr/bin/env python3
# keri_example.py - Example workflow for the KERI Thank You Certificate system

import os
import platform
import argparse
import sys

# Apply Windows fixes before importing any KERI modules
if platform.system() == 'Windows':
    from adapter.keri.windows_fix import apply_windows_fixes
    apply_windows_fixes()

from adapter.keri.certificate import ThankYouCertificate
from adapter.keri.identity import Identity

def clean_directory(dir_path):
    """Remove directory if it exists and create a fresh one"""
    import shutil
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

def main(clean=False, witness_urls=None, use_witnesses=False):
    """Run the complete example workflow
    
    Args:
        clean (bool): Whether to clean the data directory before starting
        witness_urls (list): List of witness URLs to use
        use_witnesses (bool): Whether to use witnesses
    """
    # Base directory for KERI data
    base_dir = "./keri_example_data"
    
    if clean:
        clean_directory(base_dir)
    else:
        os.makedirs(base_dir, exist_ok=True)
    
    witnesses_count = 0
    if use_witnesses and witness_urls:
        witnesses_count = len(witness_urls)
        print(f"Using {witnesses_count} witnesses: {', '.join(witness_urls)}")
    
    # 1. Create identities for issuer and recipient
    print("\n1. Creating identities...")
    issuer = Identity("example_issuer", base_dir, witness_urls=witness_urls)
    issuer.create(witnesses=witnesses_count)
    
    recipient = Identity("example_recipient", base_dir, witness_urls=witness_urls)
    recipient.create(witnesses=witnesses_count)
    
    # Publish to witnesses if using them
    if witnesses_count > 0:
        print("\n1.1 Publishing identities to witnesses...")
        issuer.publish_to_witnesses()
        recipient.publish_to_witnesses()
    
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
        
        # List acknowledgments
        print("\n4.1 Listing acknowledgments...")
        acks = cert_handler.list_acknowledgments()
        if acks:
            print(f"Found {len(acks)} acknowledgment(s):")
            for ack in acks:
                print(f"  - {ack}")
    
    # 5. Rotate keys for the issuer
    print("\n5. Rotating keys for the issuer...")
    issuer.rotate_keys()
    
    # Publish the rotation if using witnesses
    if witnesses_count > 0:
        print("\n5.1 Publishing rotation to witnesses...")
        issuer.publish_to_witnesses()
    
    # 6. List all certificates
    print("\n6. Listing all certificates...")
    certs = cert_handler.list_certificates()
    if certs:
        print(f"Found {len(certs)} certificate(s)")
        for cert in certs:
            print(f"  - {cert}")
    else:
        print("No certificates found.")
    
    # 7. Export and import a certificate
    if cert_file:
        print("\n7. Exporting and importing a certificate...")
        export_file = os.path.join(base_dir, "exported_cert.json")
        cert_handler.export_certificate(cert_file, export_file)
        print(f"Certificate exported to: {export_file}")
        
        # Import the certificate
        imported_cert = cert_handler.import_certificate(export_file)
        if imported_cert:
            print(f"Certificate imported from: {export_file}")
            print(f"Imported to: {imported_cert}")
    
    print("\nExample complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the KERI Thank You Certificate example")
    parser.add_argument("--clean", action="store_true", help="Clean data directory before starting")
    parser.add_argument("--use-witnesses", action="store_true", help="Use witnesses for the example")
    parser.add_argument("--witness-urls", nargs="+", 
                        default=["tcp://localhost:5621", "tcp://localhost:5622", "tcp://localhost:5623"],
                        help="List of witness URLs to use")
    
    args = parser.parse_args()
    
    main(clean=args.clean, witness_urls=args.witness_urls, use_witnesses=args.use_witnesses)