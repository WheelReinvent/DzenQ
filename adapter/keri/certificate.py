# certificate.py - Implementation of Thank You certificate using KERI
import os
import json
import datetime
import hashlib
import base64
from pathlib import Path
import platform

# Apply Windows fixes before importing KERI modules if needed
if platform.system() == 'Windows':
    from adapter.keri.windows_fix import apply_windows_fixes
    apply_windows_fixes()

from keri.core import eventing, parsing, coring, serdering
from keri.core.coring import Saider
from keri.app import habbing, directing
from keri.vdr import credentialing, verifying


class ThankYouCertificate:
    """Issues, verifies, and stores thank you certificates using KERI"""
    
    def __init__(self, base_dir="./keri_data"):
        """Initialize the certificate handler
        
        Args:
            base_dir (str): Base directory for storing certificates
        """
        self.base_dir = base_dir
        self.certs_dir = os.path.join(base_dir, "certificates")
        
        # Ensure directories exist
        os.makedirs(self.certs_dir, exist_ok=True)
    
    def issue(self, issuer_identity, recipient_name, message, recipient_aid=None):
        """Issue a Thank You certificate using issuer's identity with proper KERI event
        
        Args:
            issuer_identity: Loaded Identity object for the issuer
            recipient_name (str): Name of the recipient
            message (str): Thank you message content
            recipient_aid (str, optional): Recipient's KERI identifier if known
            
        Returns:
            str: Certificate filename
        """
        if not issuer_identity.hab:
            print("Issuer identity not loaded. Use create() or load() first.")
            return None
            
        # Create certificate content
        cert_content = {
            "recipient_name": recipient_name,
            "recipient_aid": recipient_aid,
            "message": message,
            "issued_at": datetime.datetime.utcnow().isoformat() + "Z"  # ISO 8601 UTC
        }
        
        try:
            # Create a unique ID for the certificate
            cert_id = hashlib.sha256(json.dumps(cert_content, sort_keys=True).encode()).hexdigest()[:24]
            
            # Create an interaction event with the certificate as data
            serder = eventing.interact(
                pre=issuer_identity.hab.pre,
                dig=issuer_identity.hab.kever.serder.said,
                sn=issuer_identity.hab.kever.sn + 1,
                data=[cert_content]
            )
            
            # Sign the event using the issuer's keys
            sigers = issuer_identity.hab.sign(ser=serder.raw, verfers=issuer_identity.hab.kever.verfers, indexed=False)
            
            # Process the event in the issuer's KEL
            issuer_identity.hab.kvy.processEvent(serder=serder, sigers=sigers)
            
            # Create a unique filename for the certificate
            cert_file = os.path.join(self.certs_dir, f"{serder.said}.json")
            
            # Prepare signatures for storage
            sigs = []
            for siger in sigers:
                sigs.append(siger.qb64)
            
            # Prepare certificate data for storage
            certificate = {
                "event_said": serder.said,
                "cert_id": cert_id,
                "issuer_aid": issuer_identity.hab.pre,
                "certificate": cert_content,
                "signed_event_raw": serder.raw.decode("utf-8"),
                "signatures": sigs,
                "raw_event": serder.ked
            }
            
            # Save certificate to file
            with open(cert_file, "w") as f:
                json.dump(certificate, f, indent=2)
            
            # If we're using witnesses, publish the event
            if not issuer_identity.local and issuer_identity.witness_urls:
                self._publish_to_witnesses(issuer_identity, serder.said)
            
            print(f"Thank You certificate issued:")
            print(f"  Event SAID: {serder.said}")
            print(f"  Certificate ID: {cert_id}")
            print(f"  Recipient: {recipient_name}")
            print(f"  Saved to: {cert_file}")
            
            return cert_file
        except Exception as e:
            print(f"Error issuing certificate: {e}")
            return None
    
    def _publish_to_witnesses(self, identity, said):
        """Helper to publish an event to witnesses
        
        Args:
            identity: The Identity object
            said (str): The SAID of the event to publish
        """
        try:
            # Create a client director to communicate with witnesses
            with directing.Director(hab=identity.hab, doers=[]) as director:
                # Send the specific event to witnesses
                director.windEvent(said=said)
                print(f"Published certificate event to witnesses")
        except Exception as e:
            print(f"Warning: Could not publish to witnesses: {e}")
    
    def verify(self, cert_file, recipient_identity=None):
        """Verify a Thank You certificate with proper KERI verification
        
        Args:
            cert_file (str): Path to the certificate file
            recipient_identity: Loaded Identity object for the recipient (optional)
            
        Returns:
            dict: Verification result with certificate if valid
        """
        print(f"Verifying certificate: {cert_file}")
        
        try:
            # Load certificate from file
            with open(cert_file, "r") as f:
                certificate = json.load(f)
                
            issuer_aid = certificate.get("issuer_aid")
            raw_event = certificate.get("signed_event_raw")
            signatures = certificate.get("signatures", [])
            event_said = certificate.get("event_said")
            
            if not issuer_aid or not raw_event or not event_said:
                print("Invalid certificate format")
                return {"valid": False, "error": "Invalid certificate format"}
                
            # Create a credentialing verifier
            try:
                # Parse the raw event to get the serder
                serder = serdering.SerderKERI(raw=bytearray(raw_event.encode("utf-8")))
                
                # If we have a recipient identity, use its KEL for proper verification
                if recipient_identity and recipient_identity.hab:
                    # Use KERI's proper verification via the KEL
                    kever = recipient_identity.hab.kevers.get(issuer_aid)
                    if kever:
                        # We have the issuer's KEL, so we can verify properly
                        # Convert the sigs to Sigers
                        sigers = []
                        for sig in signatures:
                            siger = coring.Siger(qb64=sig)
                            sigers.append(siger)
                        
                        # Verify using the KEL
                        if kever.verifyEvent(serder=serder, sigers=sigers):
                            # Verify the SAID matches
                            if serder.said == event_said:
                                print("Certificate verification successful:")
                                print(f"  Issuer: {issuer_aid}")
                                print(f"  Recipient: {certificate['certificate']['recipient_name']}")
                                print(f"  Message: {certificate['certificate']['message']}")
                                return {"valid": True, "certificate": certificate}
                            else:
                                print("Certificate SAID doesn't match the event")
                                return {"valid": False, "error": "Certificate SAID mismatch"}
                        else:
                            print("Certificate signature verification failed")
                            return {"valid": False, "error": "Signature verification failed"}
                    else:
                        # We don't have the KEL, so we need to fetch it
                        print("Warning: Issuer's KEL not available locally")
                        
                        # Basic verification just confirming the certificate format is correct
                        # In a real system, we would fetch the KEL from witnesses
                        saider = Saider(qb64=event_said)
                        if saider.verify(serder.raw):
                            print("Certificate format verification successful (limited):")
                            print(f"  Issuer: {issuer_aid}")
                            print(f"  Recipient: {certificate['certificate']['recipient_name']}")
                            print(f"  Message: {certificate['certificate']['message']}")
                            return {"valid": True, "certificate": certificate, 
                                   "warning": "Limited verification - issuer's KEL not available"}
                        else:
                            print("Certificate SAID verification failed")
                            return {"valid": False, "error": "Certificate SAID verification failed"}
                else:
                    # Without recipient identity, do basic verification
                    print("Warning: Limited verification without recipient identity")
                    print(f"  Issuer: {issuer_aid}")
                    print(f"  Recipient: {certificate['certificate']['recipient_name']}")
                    print(f"  Message: {certificate['certificate']['message']}")
                    return {"valid": True, "certificate": certificate, 
                           "warning": "Limited verification - no recipient identity provided"}
                    
            except Exception as e:
                print(f"Error during certificate verification: {e}")
                return {"valid": False, "error": f"Verification error: {str(e)}"}
                
        except FileNotFoundError:
            print(f"Certificate file not found: {cert_file}")
            return {"valid": False, "error": "Certificate file not found"}
        except json.JSONDecodeError:
            print(f"Invalid JSON in certificate file: {cert_file}")
            return {"valid": False, "error": "Invalid JSON in certificate file"}
        except Exception as e:
            print(f"Error verifying certificate: {e}")
            return {"valid": False, "error": str(e)}
    
    def acknowledge(self, cert_file, recipient_identity):
        """Acknowledge a certificate by creating a receipt in recipient's KEL
        
        Args:
            cert_file (str): Path to the certificate file
            recipient_identity: Loaded Identity object for the recipient
            
        Returns:
            bool: Success or failure
        """
        # First verify the certificate
        verification = self.verify(cert_file, recipient_identity)
        if not verification["valid"]:
            print("Cannot acknowledge an invalid certificate")
            return False
            
        try:
            # Get the certificate
            certificate = verification["certificate"]
            event_said = certificate["event_said"]
            
            # Create a receipt for the event SAID
            try:
                # Use proper KERI receipt mechanism with the event's SAID
                receipt_serder = eventing.receipt(
                    pre=recipient_identity.hab.pre,
                    sn=recipient_identity.hab.kever.sn,
                    said=event_said
                )
                
                # Sign the receipt using the recipient's keys
                sigers = recipient_identity.hab.sign(ser=receipt_serder.raw, indexed=False)
                
                # Add the receipt to the recipient's KEL
                recipient_identity.hab.kvy.processEvent(serder=receipt_serder, sigers=sigers)
                
                # If we're using witnesses, publish the receipt
                if not recipient_identity.local and recipient_identity.witness_urls:
                    self._publish_to_witnesses(recipient_identity, receipt_serder.said)
                
                # Save a record of the acknowledgment
                ack_dir = os.path.join(self.certs_dir, "acknowledgments")
                os.makedirs(ack_dir, exist_ok=True)
                
                ack_file = os.path.join(ack_dir, f"{certificate['cert_id']}_ack.json")
                ack_data = {
                    "certificate_said": event_said,
                    "certificate_id": certificate["cert_id"],
                    "receipt_said": receipt_serder.said,
                    "recipient_aid": recipient_identity.hab.pre,
                    "acknowledged_at": datetime.datetime.utcnow().isoformat() + "Z",
                    "raw_receipt": receipt_serder.ked
                }
                
                with open(ack_file, "w") as f:
                    json.dump(ack_data, f, indent=2)
                
                print("Certificate acknowledged:")
                print(f"  Event SAID: {event_said}")
                print(f"  Acknowledged by: {recipient_identity.hab.pre}")
                print(f"  Acknowledgment stored at: {ack_file}")
                
                return True
            except Exception as e:
                print(f"Error creating acknowledgment: {e}")
                return False
                
        except Exception as e:
            print(f"Error acknowledging certificate: {e}")
            return False
    
    def list_certificates(self):
        """List all stored certificates
        
        Returns:
            list: List of certificate filenames
        """
        try:
            certs = [f for f in os.listdir(self.certs_dir) if f.endswith(".json") and os.path.isfile(os.path.join(self.certs_dir, f))]
            return certs
        except Exception as e:
            print(f"Error listing certificates: {e}")
            return []
            
    def list_acknowledgments(self):
        """List all stored acknowledgments
        
        Returns:
            list: List of acknowledgment filenames
        """
        try:
            ack_dir = os.path.join(self.certs_dir, "acknowledgments")
            if not os.path.exists(ack_dir):
                return []
                
            acks = [f for f in os.listdir(ack_dir) if f.endswith("_ack.json")]
            return acks
        except Exception as e:
            print(f"Error listing acknowledgments: {e}")
            return []
            
    def export_certificate(self, cert_file, output_file=None):
        """Export a certificate to a portable format
        
        Args:
            cert_file (str): Path to the certificate file
            output_file (str, optional): Path to save the exported certificate
            
        Returns:
            str: Path to the exported certificate file or the exported data
        """
        try:
            # Load the certificate
            with open(cert_file, "r") as f:
                certificate = json.load(f)
                
            # Create a simplified export format
            export_data = {
                "type": "KERIThankYouCertificate",
                "version": "1.0",
                "issuer_aid": certificate["issuer_aid"],
                "event_said": certificate["event_said"],
                "certificate": certificate["certificate"],
                "signed_event": certificate["signed_event_raw"],
                "signatures": certificate["signatures"]
            }
            
            # If output file provided, save to it
            if output_file:
                with open(output_file, "w") as f:
                    json.dump(export_data, f, indent=2)
                print(f"Certificate exported to: {output_file}")
                return output_file
            else:
                # Return the JSON data as a string
                return json.dumps(export_data, indent=2)
                
        except Exception as e:
            print(f"Error exporting certificate: {e}")
            return None
            
    def import_certificate(self, import_data_or_file):
        """Import a certificate from a portable format
        
        Args:
            import_data_or_file: Either a file path or the JSON data as string
            
        Returns:
            str: Path to the imported certificate file
        """
        try:
            # Determine if input is a file or data
            if os.path.isfile(import_data_or_file):
                with open(import_data_or_file, "r") as f:
                    export_data = json.load(f)
            else:
                # Assume it's JSON data
                export_data = json.loads(import_data_or_file)
                
            # Validate the imported data
            if not all(k in export_data for k in ["type", "issuer_aid", "event_said", "certificate", "signed_event", "signatures"]):
                print("Invalid certificate format")
                return None
                
            if export_data["type"] != "KERIThankYouCertificate":
                print(f"Unsupported certificate type: {export_data.get('type')}")
                return None
                
            # Convert back to internal format
            cert_content = export_data["certificate"]
            
            # Try to parse the event and validate SAID
            try:
                signed_event_bytes = export_data["signed_event"].encode("utf-8")
                serder = serdering.SerderKERI(raw=bytearray(signed_event_bytes))
                
                if serder.said != export_data["event_said"]:
                    print("Warning: Event SAID mismatch")
            except Exception as e:
                print(f"Warning: Could not validate event: {e}")
            
            # Create certificate object
            certificate = {
                "event_said": export_data["event_said"],
                "cert_id": hashlib.sha256(json.dumps(cert_content, sort_keys=True).encode()).hexdigest()[:24],
                "issuer_aid": export_data["issuer_aid"],
                "certificate": cert_content,
                "signed_event_raw": export_data["signed_event"],
                "signatures": export_data["signatures"],
                "raw_event": serder.ked if 'serder' in locals() else {}
            }
            
            # Save to file
            cert_file = os.path.join(self.certs_dir, f"{export_data['event_said']}.json")
            with open(cert_file, "w") as f:
                json.dump(certificate, f, indent=2)
                
            print(f"Certificate imported and saved to: {cert_file}")
            return cert_file
                
        except json.JSONDecodeError:
            print("Invalid JSON format")
            return None
        except Exception as e:
            print(f"Error importing certificate: {e}")
            return None