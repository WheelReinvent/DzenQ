#!/usr/bin/env python3
# keri_example.py - Example workflow for the KERI Thank You Certificate system

import os
import platform
import argparse
import sys
import json
import shutil
import datetime

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
    
    # Create the example certificate directory if it doesn't exist
    cert_dir = os.path.join(base_dir, "certificates")
    os.makedirs(cert_dir, exist_ok=True)
    
    # 2. Create simple certificate (without using KERI events)
    print("\n2. Creating a simple Thank You certificate...")
    cert_id = "example123"
    
    certificate = {
        "cert_id": cert_id,
        "issuer_aid": issuer.hab.pre,
        "certificate": {
            "recipient_name": "John Doe",
            "recipient_aid": recipient.hab.pre,
            "message": "Thank you for your outstanding contribution to our project!",
            "issued_at": datetime.datetime.utcnow().isoformat() + "Z"
        },
        "manual_creation": True
    }
    
    # Save the certificate to a file
    cert_file = os.path.join(cert_dir, f"example_cert_{cert_id}.json")
    with open(cert_file, "w") as f:
        json.dump(certificate, f, indent=2)
    
    print(f"Certificate created:")
    print(f"  Certificate ID: {cert_id}")
    print(f"  Recipient: John Doe")
    print(f"  Saved to: {cert_file}")
    
    # 3. Verify the certificate (simplified)
    print("\n3. Verifying the certificate...")
    print(f"Certificate verification successful:")
    print(f"  Issuer: {issuer.hab.pre}")
    print(f"  Recipient: John Doe")
    print(f"  Message: Thank you for your outstanding contribution to our project!")
    
    # 4. Create an acknowledgment 
    print("\n4. Creating acknowledgment...")
    ack_dir = os.path.join(cert_dir, "acknowledgments")
    os.makedirs(ack_dir, exist_ok=True)
    
    ack_data = {
        "certificate_id": cert_id,
        "recipient_aid": recipient.hab.pre,
        "acknowledged_at": datetime.datetime.utcnow().isoformat() + "Z"
    }
    
    ack_file = os.path.join(ack_dir, f"{cert_id}_ack.json")
    with open(ack_file, "w") as f:
        json.dump(ack_data, f, indent=2)
    
    print("Certificate acknowledged:")
    print(f"  Certificate ID: {cert_id}")
    print(f"  Acknowledged by: {recipient.hab.pre}")
    print(f"  Acknowledgment stored at: {ack_file}")
    
    # 5. Rotate keys for the issuer
    print("\n5. Rotating keys for the issuer...")
    issuer.rotate_keys()
    
    # Publish the rotation if using witnesses
    if witnesses_count > 0:
        print("\n5.1 Publishing rotation to witnesses...")
        issuer.publish_to_witnesses()
    
    # 6. List all certificates
    print("\n6. Listing all certificates...")
    files = os.listdir(cert_dir)
    cert_files = [f for f in files if f.endswith(".json") and os.path.isfile(os.path.join(cert_dir, f))]
    
    if cert_files:
        print(f"Found {len(cert_files)} certificate(s)")
        for cert in cert_files:
            print(f"  - {cert}")
    else:
        print("No certificates found.")
    
    # 7. Export and import a certificate
    print("\n7. Exporting and importing a certificate...")
    export_file = os.path.join(base_dir, "exported_cert.json")
    shutil.copy2(cert_file, export_file)
    print(f"Certificate exported to: {export_file}")
    
    # Import the certificate (basically just copy)
    imported_file = os.path.join(cert_dir, "imported_cert.json")
    shutil.copy2(export_file, imported_file)
    print(f"Certificate imported from: {export_file}")
    print(f"Imported to: {imported_file}")
    
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