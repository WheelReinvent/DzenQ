# receive_and_acknowledge.py
import json
import base64
import datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature
# Import signing function from previous script
from issue_thank_you import sign_message

def verify_signature(public_key_path, signature_bytes, message_bytes):
    """Verifies a signature using a public key."""
    with open(public_key_path, "rb") as key_file:
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(key_file.read())
    try:
        public_key.verify(signature_bytes, message_bytes)
        return True
    except InvalidSignature:
        return False

def receive_and_verify(credential_file, issuer_public_key_path):
    """Loads a thank you certificate and verifies its signature."""
    print(f"\n--- Verifying certificate from file {credential_file} ---")
    try:
        with open(credential_file, "r") as f:
            signed_credential = json.load(f)
    except FileNotFoundError:
        print(f"Error: File {credential_file} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not read JSON from file {credential_file}.")
        return None

    credential_data = signed_credential.get("credential_data")
    signature_b64 = signed_credential.get("signature")

    if not credential_data or not signature_b64:
        print("Error: Invalid certificate format.")
        return None

    # Decode signature from base64
    try:
        signature = base64.urlsafe_b64decode(signature_b64)
    except Exception as e:
         print(f"Error decoding signature: {e}")
         return None

    # Recreate the bytes that were signed (VERY IMPORTANT to recreate EXACTLY the same way)
    message_to_verify_bytes = json.dumps(credential_data, sort_keys=True, separators=(',', ':')).encode('utf-8')

    # Verify the signature
    try:
        is_valid = verify_signature(issuer_public_key_path, signature, message_to_verify_bytes)
    except FileNotFoundError:
         print(f"Error: Issuer's public key {issuer_public_key_path} not found.")
         return None

    if is_valid:
        print(">>> Signature valid! The certificate is authentic.")
        print(f"    Issuer: {credential_data.get('issuer')}")
        print(f"    Recipient: {credential_data.get('recipient_name')}")
        print(f"    Text: {credential_data.get('text')}")
        return signed_credential # Return full structure to create receipt
    else:
        print("!!! WARNING: Invalid signature! The certificate is forged or corrupted.")
        return None


def create_receipt(recipient_id_path, recipient_private_key_path, received_credential, output_file="thank_you_receipt.json"):
    """Creates a signed receipt for the received certificate."""
    print(f"\n--- Creating Receipt ---")
    with open(recipient_id_path, "r") as f:
        recipient_id = f.read().strip()

    # Data for the receipt (analog of receipt event in KERL)
    receipt_data = {
        "recipient": recipient_id,
        "type": "CredentialReceipt",
        "received_at": datetime.datetime.utcnow().isoformat() + "Z",
        # Reference to received event (could be a hash, here simply using issuer ID and issuance time)
        "acknowledged_issuer": received_credential["credential_data"]["issuer"],
        "acknowledged_issued_at": received_credential["credential_data"]["issued_at"]
    }

    # Prepare data for signing
    receipt_to_sign_bytes = json.dumps(receipt_data, sort_keys=True, separators=(',', ':')).encode('utf-8')

    # Sign with recipient's key
    signature = sign_message(recipient_private_key_path, receipt_to_sign_bytes)

    # Create signed receipt
    signed_receipt = {
        "receipt_data": receipt_data,
        "signature": base64.urlsafe_b64encode(signature).decode('utf-8')
    }

    # Save it
    with open(output_file, "w") as f:
        json.dump(signed_receipt, f, indent=2)
    print(f"Signed receipt saved to: {output_file}")


if __name__ == "__main__":
    credential_to_check = "thank_you_credential.json"
    issuer_pub_key = "issuer_public.key" # Needed for verification

    recipient_id_file = "recipient_id.txt" # Recipient's identity
    recipient_priv_key = "recipient_private.key" # For signing receipt
    receipt_output = "thank_you_receipt.json"

    # 1. Verify received certificate
    verified_credential = receive_and_verify(credential_to_check, issuer_pub_key)

    # 2. If certificate is valid, create receipt
    if verified_credential:
        create_receipt(recipient_id_file, recipient_priv_key, verified_credential, receipt_output)