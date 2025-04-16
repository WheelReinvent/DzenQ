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

The Appreciation Protocol provides a unified command-line interface with multiple ways to run it:

```bash
# Using the short command (recommended)
./tnx --help

# Using Python with the short script
python tnx.py --help

# Using the original script
python appreciate.py --help
```

### Installing as a System-Wide Command

To use the `tnx` command anywhere in your system:

```bash
# Install the package in development mode
pip install -e .

# Now you can use the command directly
tnx --help
```

### Identity Management

```bash
# Create a new identity
tnx identity create my_identity

# Create an identity with witness support
tnx identity create my_identity --witnesses 3 --witness-urls tcp://witness1.example.com:5620 tcp://witness2.example.com:5620 tcp://witness3.example.com:5620

# Rotate keys for an identity
tnx identity rotate my_identity

# Remove an identity
tnx identity remove my_identity

# Remove an identity with backup
tnx identity remove my_identity --backup ./backups

# Remove an identity without cleaning the keystore (not recommended)
tnx identity remove my_identity --no-clean-keys
```

### Administrative Commands

For situations where normal operations fail or you need to start fresh:

```bash
# Reset the entire KERI database (use with extreme caution!)
tnx admin reset-db

# Reset with immediate confirmation (no interactive prompt)
tnx admin reset-db --confirm

# Reset only project data (preserve global KERI data)
tnx admin reset-db --no-clean-global
```

#### Dealing with KERI's Global Data

KERI sometimes stores data in global locations like `C:/usr/local/var/keri` on Windows or `/usr/local/var/keri` on Unix systems. This can cause issues when trying to recreate identities with the same name. Our tools automatically handle this:

1. When removing an identity: `--clean-global` flag (on by default) cleans related global data
2. When resetting the database: `--clean-global` flag (on by default) cleans all global KERI data

If you encounter issues recreating identities, try these options in order:

```bash
# Option 1: Force remove a specific identity (even if it can't be loaded)
tnx admin force-remove identity-name --confirm

# Option 2: Reset the entire database as a last resort
tnx admin reset-db --confirm
```

The `force-remove` command is especially useful when normal remove operations fail because it searches for and removes all data related to an identity name, even if KERI cannot load the identity normally due to corrupted or locked files.

### Certificate Operations

```bash
# Issue a certificate
tnx certificate issue my_identity "Recipient Name" "Thank you message"

# Verify a certificate
tnx certificate verify /path/to/certificate.json --recipient recipient_identity

# Acknowledge a certificate
tnx certificate verify /path/to/certificate.json --recipient recipient_identity --acknowledge

# List all certificates
tnx certificate list

# List with details
tnx certificate list --details

# List acknowledgments
tnx certificate list --acks
```

### Export and Import

```bash
# Export a certificate
tnx certificate list --export 1:exported_cert.json

# Import and verify a certificate
tnx certificate verify /path/to/certificate.json --import exported_cert.json
```

### Complete Example

Run the complete example workflow:

```bash
# Run in local mode (no witnesses)
tnx example --clean

# Run with witness support
tnx example --clean --use-witnesses
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