# issue_thank_you.py
import json
import base64
import datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import hashes # Needed for signing

def sign_message(private_key_path, message_bytes):
    """Signs a message using a private key."""
    with open(private_key_path, "rb") as key_file:
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(key_file.read())
    # Ed25519 signs data directly, not requiring pre-hashing here
    signature = private_key.sign(message_bytes)
    return signature

def issue_credential(issuer_id_path, issuer_private_key_path, recipient_name, thank_you_text, output_file="thank_you_credential.json"):
    """Creates, signs, and saves a thank you certificate."""

    with open(issuer_id_path, "r") as f:
        issuer_id = f.read().strip()

    # Create the thank you structure (simplified analog of ixn event)
    credential_data = {
        "issuer": issuer_id,
        "type": "ThankYouCredential",
        "issued_at": datetime.datetime.utcnow().isoformat() + "Z", # ISO 8601 format UTC
        "recipient_name": recipient_name,
        "text": thank_you_text
        # In KERI there would be a sequence number, reference to previous event, etc.
    }

    # Prepare data for signing: serialize to JSON canonically (sorted keys, no extra spaces)
    # This is IMPORTANT for signature verification
    message_to_sign_bytes = json.dumps(credential_data, sort_keys=True, separators=(',', ':')).encode('utf-8')

    # Sign it
    signature = sign_message(issuer_private_key_path, message_to_sign_bytes)

    # Add the signature to our structure (in base64 format)
    signed_credential = {
        "credential_data": credential_data,
        "signature": base64.urlsafe_b64encode(signature).decode('utf-8')
    }

    # Save the signed thank you to a file
    with open(output_file, "w") as f:
        json.dump(signed_credential, f, indent=2) # indent=2 for readability
    print(f"Signed thank you saved to: {output_file}")

if __name__ == "__main__":
    issuer_id_file = "issuer_id.txt"
    issuer_priv_key = "issuer_private.key"
    recipient = "Valued User"
    message = "Thank you for your excellent question and interest in KERI!"
    output = "thank_you_credential.json"

    print(f"Generating thank you from {issuer_id_file} for '{recipient}'...")
    issue_credential(issuer_id_file, issuer_priv_key, recipient, message, output)