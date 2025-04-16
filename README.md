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

# Make the CLI executable (optional)
chmod +x appreciate.py
```

## Usage

The Appreciation Protocol provides a unified command-line interface for all operations:

```bash
# Show help and available commands
python appreciate.py --help
```

### Identity Management

```bash
# Create a new identity
python appreciate.py identity create my_identity

# Create an identity with witness support
python appreciate.py identity create my_identity --witnesses 3 --witness-urls tcp://witness1.example.com:5620 tcp://witness2.example.com:5620 tcp://witness3.example.com:5620

# Rotate keys for an identity
python appreciate.py identity rotate my_identity

# Remove an identity
python appreciate.py identity remove my_identity

# Remove an identity with backup
python appreciate.py identity remove my_identity --backup ./backups
```

### Certificate Operations

```bash
# Issue a certificate
python appreciate.py certificate issue my_identity "Recipient Name" "Thank you message"

# Verify a certificate
python appreciate.py certificate verify /path/to/certificate.json --recipient recipient_identity

# Acknowledge a certificate
python appreciate.py certificate verify /path/to/certificate.json --recipient recipient_identity --acknowledge

# List all certificates
python appreciate.py certificate list

# List with details
python appreciate.py certificate list --details

# List acknowledgments
python appreciate.py certificate list --acks
```

### Export and Import

```bash
# Export a certificate
python appreciate.py certificate list --export 1:exported_cert.json

# Import and verify a certificate
python appreciate.py certificate verify /path/to/certificate.json --import exported_cert.json
```

### Complete Example

Run the complete example workflow:

```bash
# Run in local mode (no witnesses)
python appreciate.py example --clean

# Run with witness support
python appreciate.py example --clean --use-witnesses
```

## Architecture

This implementation uses the KERI (Key Event Receipt Infrastructure) framework for secure identity management:

- `adapter/keri/identity.py`: Manages KERI identities with key generation and rotation capabilities
- `adapter/keri/certificate.py`: Implements certificate issuance, verification, and acknowledgment
- `cli.py`: Unified command-line interface using Typer
- `appreciate.py`: Entry point for the command-line application

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