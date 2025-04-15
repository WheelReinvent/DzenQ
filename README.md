# Thank You Certificate System

A decentralized system for issuing, verifying, and acknowledging certificates of appreciation using KERI (Key Event Receipt Infrastructure).

## Overview

This project implements a secure, decentralized system for issuing Thank You certificates without relying on a central authority or blockchain. It uses KERI's cryptographic principles to ensure:

- **Authenticity**: Certificates are cryptographically signed by the issuer
- **Verification**: Anyone can verify the validity of a certificate
- **Immutability**: Certificate history is maintained through KERI's Key Event Logs (KEL)
- **Acknowledgment**: Recipients can acknowledge certificates, adding them to their own history

## Features

- Create and manage identities with secure key generation
- Issue Thank You certificates with custom messages
- Verify received certificates cryptographically
- Acknowledge certificates to add them to recipient's history
- Support for key rotation to maintain long-term security
- Completely decentralized operation - no server or blockchain required

## Installation

1. Clone this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Scripts

The system provides several convenient scripts in the `scripts` directory:

#### Create an Identity

```bash
python scripts/create_identity.py issuer
python scripts/create_identity.py recipient
```

#### Issue a Certificate

```bash
python scripts/issue_certificate.py issuer "John Doe" "Thank you for your contribution!"
```

#### Verify a Certificate

```bash
python scripts/verify_certificate.py /path/to/certificate.json --recipient recipient
```

#### Acknowledge a Certificate

```bash
python scripts/verify_certificate.py /path/to/certificate.json --recipient recipient --acknowledge
```

#### Rotate Keys

```bash
python scripts/rotate_keys.py issuer
```

#### List Certificates

```bash
python scripts/list_certificates.py --details
```

### Example Workflow

You can run a complete example workflow with:

```bash
python keri_example.py
```

This demonstrates:
1. Creating identities for both issuer and recipient
2. Issuing a certificate
3. Verifying the certificate
4. Acknowledging receipt
5. Rotating keys
6. Listing certificates

## Library Usage

You can also use the library directly in your own code:

```python
from keri.identity import Identity
from keri.certificate import ThankYouCertificate

# Create identities
issuer = Identity("issuer")
issuer.create()

recipient = Identity("recipient")
recipient.create()

# Issue certificate
cert_handler = ThankYouCertificate()
cert_file = cert_handler.issue(issuer, "John Doe", "Thank you!")

# Verify and acknowledge
verification = cert_handler.verify(cert_file, recipient)
if verification["valid"]:
    cert_handler.acknowledge(cert_file, recipient)
```

## Technical Details

This implementation uses:

- **KERI** (Key Event Receipt Infrastructure): For identity management and event verification
- **Ed25519**: For digital signatures
- **JSON**: For data serialization

All data is stored locally in the `keri_data` directory by default.

## Security Considerations

- Private keys are stored securely but should be protected
- Key rotation is supported and recommended periodically
- The system provides cryptographic verification but relies on proper key management

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
