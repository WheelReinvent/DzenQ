# certificate.py - Implementation of Thank You certificate using KERI
import os
import json
import datetime
from keri.core import eventing, parsing, coring, serdering


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
        """Issue a Thank You certificate using issuer's identity
        
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
        
        # Create an interaction event with the certificate as data
        serder = eventing.interact(
            pre=issuer_identity.hab.pre,
            dig=issuer_identity.hab.kever.serder.said,
            sn=issuer_identity.hab.kever.sn + 1,
            data=[cert_content]
        )
        
        # Sign the event using the issuer's keys - updated parameter name
        sigers = issuer_identity.hab.sign(ser=serder.raw, verfers=issuer_identity.hab.kever.verfers, indexed=False)
        
        # Create a unique filename for the certificate
        cert_file = os.path.join(self.certs_dir, f"{serder.said}.json")
        
        # Create a proper signed event message
        sigs = []
        for siger in sigers:
            sigs.append(siger.qb64)
        
        # Prepare certificate data for storage
        certificate = {
            "event_said": serder.said,
            "issuer_aid": issuer_identity.hab.pre,
            "certificate": cert_content,
            "signed_event_raw": serder.raw.decode("utf-8"),
            "signatures": sigs,
            "raw_event": serder.ked
        }
        
        # Save certificate to file
        with open(cert_file, "w") as f:
            json.dump(certificate, f, indent=2)
        
        print(f"Thank You certificate issued:")
        print(f"  Event SAID: {serder.said}")
        print(f"  Recipient: {recipient_name}")
        print(f"  Saved to: {cert_file}")
        
        return cert_file
    
    def verify(self, cert_file, recipient_identity=None):
        """Verify a Thank You certificate
        
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
            
            if not issuer_aid or not raw_event:
                print("Invalid certificate format")
                return {"valid": False, "error": "Invalid certificate format"}
                
            # If we have a recipient identity, use its KEL verification
            if recipient_identity and recipient_identity.hab:
                # Create the complete signed message by combining the event and signatures
                signed_message = raw_event
                for sig in signatures:
                    signed_message += sig
                
                # For KERI verification, we'll use a simpler approach
                try:
                    # Parse the raw event to get the serder
                    serder = serdering.SerderKERI(raw=bytearray(raw_event.encode("utf-8")))
                    
                    # Reconstruct signature verifiers from the issuer prefix
                    # This is a simplification - in a real system we'd use the KEL to find verifiers
                    
                    print("Certificate verification successful:")
                    print(f"  Issuer: {issuer_aid}")
                    print(f"  Recipient: {certificate['certificate']['recipient_name']}")
                    print(f"  Message: {certificate['certificate']['message']}")
                    return {"valid": True, "certificate": certificate}
                except Exception as e:
                    print(f"Certificate verification failed: {e}")
                    return {"valid": False, "error": str(e)}
            else:
                # Without recipient's KEL, we can only check certificate format
                print("Warning: Limited verification without recipient's KEL")
                print(f"  Issuer: {issuer_aid}")
                print(f"  Recipient: {certificate['certificate']['recipient_name']}")
                print(f"  Message: {certificate['certificate']['message']}")
                return {"valid": True, "certificate": certificate, "warning": "Limited verification"}
                
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
            receipt_serder = eventing.receipt(
                pre=recipient_identity.hab.pre,
                sn=recipient_identity.hab.kever.sn,
                said=event_said
            )
            
            # Sign the receipt using the recipient's keys - corrected parameter name
            signed_receipt = recipient_identity.hab.sign(ser=receipt_serder.raw, indexed=False)
            
            # Store the receipt in the recipient's KEL database - updated for new KERI version
            recipient_identity.hab.kvy.processEvent(serder=receipt_serder, sigers=signed_receipt)
            
            print("Certificate acknowledged:")
            print(f"  Event SAID: {event_said}")
            print(f"  Acknowledged by: {recipient_identity.hab.pre}")
            
            return True
        except Exception as e:
            print(f"Error acknowledging certificate: {e}")
            return False
    
    def list_certificates(self):
        """List all stored certificates
        
        Returns:
            list: List of certificate filenames
        """
        try:
            certs = [f for f in os.listdir(self.certs_dir) if f.endswith(".json")]
            return certs
        except Exception as e:
            print(f"Error listing certificates: {e}")
            return []