#!/usr/bin/env python3
# list_certificates.py - List all stored certificates

import os
import sys
import argparse
import json
import platform

# Add parent directory to path so we can import adapter.keri module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Apply Windows fixes before importing any KERI modules
if platform.system() == 'Windows':
    from adapter.keri.windows_fix import apply_windows_fixes
    apply_windows_fixes()

from adapter.keri.certificate import ThankYouCertificate

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="List all stored certificates")
    parser.add_argument("--dir", default="./keri_data", help="Base directory for KERI data")
    parser.add_argument("--details", action="store_true", help="Show certificate details")
    parser.add_argument("--acks", action="store_true", help="Show acknowledgments instead of certificates")
    parser.add_argument("--export", help="Export a certificate by index to a file")
    
    args = parser.parse_args()
    
    # Initialize certificate handler
    cert_handler = ThankYouCertificate(args.dir)
    
    if args.acks:
        # List acknowledgments
        acks = cert_handler.list_acknowledgments()
        
        if not acks:
            print("No acknowledgments found.")
            return 0
            
        print(f"Found {len(acks)} acknowledgment(s):")
        ack_dir = os.path.join(args.dir, "certificates", "acknowledgments")
        
        for i, ack_file in enumerate(acks, 1):
            print(f"\n{i}. {ack_file}")
            
            if args.details:
                # Load and display acknowledgment details
                try:
                    full_path = os.path.join(ack_dir, ack_file)
                    with open(full_path, "r") as f:
                        ack_data = json.load(f)
                        
                    print(f"   Certificate ID: {ack_data.get('certificate_id', 'Unknown')}")
                    print(f"   Certificate SAID: {ack_data.get('certificate_said', 'Unknown')}")
                    print(f"   Acknowledged by: {ack_data.get('recipient_aid', 'Unknown')}")
                    print(f"   Acknowledged at: {ack_data.get('acknowledged_at', 'Unknown')}")
                except Exception as e:
                    print(f"   Error reading acknowledgment: {e}")
    else:
        # List certificates
        certs = cert_handler.list_certificates()
        
        if not certs:
            print("No certificates found.")
            return 0
            
        print(f"Found {len(certs)} certificate(s):")
        
        # Store certificate paths for export option
        cert_paths = []
        
        for i, cert_file in enumerate(certs, 1):
            full_path = os.path.join(args.dir, "certificates", cert_file)
            cert_paths.append(full_path)
            
            print(f"\n{i}. {cert_file}")
            
            if args.details:
                # Load and display certificate details
                try:
                    with open(full_path, "r") as f:
                        cert_data = json.load(f)
                        
                    cert_content = cert_data.get("certificate", {})
                    print(f"   Certificate ID: {cert_data.get('cert_id', 'Unknown')}")
                    print(f"   Issuer: {cert_data.get('issuer_aid', 'Unknown')}")
                    print(f"   Recipient: {cert_content.get('recipient_name', 'Unknown')}")
                    print(f"   Issued at: {cert_content.get('issued_at', 'Unknown')}")
                    print(f"   Message: {cert_content.get('message', 'No message')}")
                except Exception as e:
                    print(f"   Error reading certificate: {e}")
        
        # Export a certificate if requested
        if args.export and cert_paths:
            try:
                export_idx = int(args.export.split(":")[0]) - 1
                export_file = args.export.split(":", 1)[1] if ":" in args.export else None
                
                if 0 <= export_idx < len(cert_paths):
                    if not export_file:
                        # Generate a default filename
                        export_file = f"exported_cert_{export_idx+1}.json"
                        
                    cert_handler.export_certificate(cert_paths[export_idx], export_file)
                    print(f"\nExported certificate {export_idx+1} to {export_file}")
                else:
                    print(f"\nInvalid certificate index for export: {export_idx+1}")
                    print(f"Valid range is 1-{len(cert_paths)}")
            except (ValueError, IndexError) as e:
                print(f"\nError exporting certificate: {e}")
                print("Use format: --export INDEX:FILENAME or --export INDEX")
    
    return 0
    
if __name__ == "__main__":
    sys.exit(main())