# create_identity.py
import base64
import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

def create_identity(prefix="person"):
    """Generates Ed25519 key pair and stores the keys and identifier."""

    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Serialize keys for file storage
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )

    # Create a simple identifier (similar to KERI, but very simplified)
    # Use base64 of public key as the ID base
    # In real KERI, there would be a prefix encoding the key/hash type
    identifier = "E" + base64.urlsafe_b64encode(public_pem).decode('utf-8').rstrip('=')

    # Save to files
    private_key_file = f"{prefix}_private.key"
    public_key_file = f"{prefix}_public.key"
    id_file = f"{prefix}_id.txt"

    with open(private_key_file, "wb") as f:
        f.write(private_pem)
    print(f"Private key saved to: {private_key_file}")

    with open(public_key_file, "wb") as f:
        f.write(public_pem)
    print(f"Public key saved to: {public_key_file}")

    with open(id_file, "w") as f:
        f.write(identifier)
    print(f"Identifier saved to: {id_file}")

    return identifier, private_key_file, public_key_file

if __name__ == "__main__":
    print("Creating identity for 'Issuer'...")
    create_identity("issuer")
    print("\nCreating identity for 'Recipient'...")
    create_identity("recipient")
    print("\nDone. You now have key files and IDs for the issuer and recipient.")