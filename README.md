# Appreciation Protocol - DzenQ

A decentralized, secure system for issuing and verifying Certificates of Appreciation using KERI.

## Overview

The Appreciation Protocol leverages KERI (Key Event Receipt Infrastructure) to create a fully decentralized system for issuing and verifying certificates of appreciation. This implementation provides:

- Full KERI integration with proper KEL and KERL storage
- Witness support for enhanced security and availability
- Cryptographically secure certificates with tamper-proof verification
- No central authority, blockchain, or trusted third parties
- Key rotation capabilities for long-term identity management
- Import/export functionality for certificate portability

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/DzenQ.git
cd DzenQ

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Identity Management

```bash
# Create a new identity
python scripts/create_identity.py my_identity

# Create an identity with witness support
python scripts/create_identity.py my_identity --witnesses 3 --witness-urls tcp://witness1.example.com:5620 tcp://witness2.example.com:5620 tcp://witness3.example.com:5620

# Rotate keys for an identity
python scripts/rotate_keys.py my_identity
```

### Certificate Operations

```bash
# Issue a certificate
python scripts/issue_certificate.py my_identity "Recipient Name" "Thank you message"

# Verify a certificate
python scripts/verify_certificate.py /path/to/certificate.json --recipient recipient_identity

# Acknowledge a certificate
python scripts/verify_certificate.py /path/to/certificate.json --recipient recipient_identity --acknowledge

# List all certificates
python scripts/list_certificates.py

# List with details
python scripts/list_certificates.py --details

# List acknowledgments
python scripts/list_certificates.py --acks
```

### Export and Import

```bash
# Export a certificate
python scripts/list_certificates.py --export 1:exported_cert.json

# Import and verify a certificate
python scripts/verify_certificate.py /path/to/certificate.json --import exported_cert.json
```

## Complete Example

Run the complete example workflow:

```bash
# Run in local mode (no witnesses)
python keri_example.py --clean

# Run with witness support
python keri_example.py --clean --use-witnesses
```

## Architecture

This implementation uses the KERI (Key Event Receipt Infrastructure) framework for secure identity management:

- `adapter/keri/identity.py`: Manages KERI identities with key generation and rotation capabilities
- `adapter/keri/certificate.py`: Implements certificate issuance, verification, and acknowledgment
- `scripts/`: Command-line tools for all certificate operations

### Storage

- All KERI data is stored in the `keri_data` directory by default
- Key Event Logs (KEL) store the identity events
- Key Event Receipt Logs (KERL) store receipts and acknowledgments
- Certificates are stored in JSON format

## Security Considerations

- Private keys are stored locally and must be protected
- Consider using a secure key management solution for production
- For high-security deployments, use multiple witnesses
- Backup your KERI database directory regularly

## License

This project is licensed under the MIT License - see the LICENSE file for details.