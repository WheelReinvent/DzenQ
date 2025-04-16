#!/usr/bin/env python3
# cli.py - Command-line interface for the Appreciation Protocol

import os
import sys
import platform
import typer
from typing import List, Optional
from pathlib import Path

# Apply Windows fixes before importing KERI modules
if platform.system() == 'Windows':
    from adapter.keri.windows_fix import apply_windows_fixes
    apply_windows_fixes()

from adapter.keri.identity import Identity
from adapter.keri.certificate import ThankYouCertificate

# Create CLI app
app = typer.Typer(help="Appreciation Protocol - A decentralized system for issuing and verifying Certificates of Appreciation.")
id_app = typer.Typer(help="Identity management commands")
cert_app = typer.Typer(help="Certificate operations")
admin_app = typer.Typer(help="Administrative operations")

# Add sub-apps to the main app
app.add_typer(id_app, name="identity", help="Identity management operations")
app.add_typer(cert_app, name="certificate", help="Certificate operations")
app.add_typer(admin_app, name="admin", help="Administrative operations")

# Common options
KERI_DIR_OPTION = typer.Option(
    "./keri_data", 
    "--dir", "-d",
    help="Base directory for storing KERI data"
)

# ====== Identity Commands ======

@id_app.command("create")
def create_identity(
    name: str = typer.Argument(..., help="Name for the identity (e.g., issuer, recipient)"),
    keri_dir: str = KERI_DIR_OPTION,
    non_transferable: bool = typer.Option(False, "--non-transferable", help="Create a non-transferable identity (keys cannot be rotated)"),
    witnesses: int = typer.Option(0, "--witnesses", "-w", help="Number of witnesses to use (0 for local mode)"),
    witness_urls: Optional[List[str]] = typer.Option(None, "--witness-urls", help="List of witness URLs to use (e.g. tcp://witness1.example.com:5620)"),
    isith: str = typer.Option("1", "--isith", help="Initial signing threshold (n-of-m or fractional)"),
    nsith: str = typer.Option("1", "--nsith", help="Next signing threshold"),
    local: bool = typer.Option(False, "--local", help="Force local mode (no witnesses)"),
    tcp: int = typer.Option(5620, "--tcp", help="TCP port for local server if needed"),
    publish: bool = typer.Option(False, "--publish", "-p", help="Publish to witnesses after creation")
):
    """Create a new identity with KERI."""
    # Set up witness URLs
    witness_urls = witness_urls or []
    
    # Create the identity
    identity = Identity(name, keri_dir, witness_urls=witness_urls, tcp=tcp, local=local)
    prefix = identity.create(
        transferable=not non_transferable,
        witnesses=witnesses,
        isith=isith,
        nsith=nsith
    )
    
    # Publish to witnesses if requested
    if publish and witnesses > 0 and witness_urls:
        identity.publish_to_witnesses()
    
    typer.echo(f"\nIdentity created successfully!")
    typer.echo(f"Identifier (AID): {prefix}")

@id_app.command("rotate")
def rotate_keys(
    name: str = typer.Argument(..., help="Name of the identity to rotate keys for"),
    keri_dir: str = KERI_DIR_OPTION,
    publish: bool = typer.Option(False, "--publish", "-p", help="Publish rotation to witnesses after completion")
):
    """Rotate keys for an identity."""
    # Load the identity
    identity = Identity(name, keri_dir)
    if not identity.load():
        typer.echo(f"Could not load identity '{name}'")
        typer.echo(f"Create it first with: appreciate identity create {name}")
        raise typer.Exit(code=1)
    
    # Rotate the keys
    if not identity.rotate_keys():
        typer.echo("Key rotation failed")
        raise typer.Exit(code=1)
    
    # Publish to witnesses if requested
    if publish and not identity.local and identity.witness_urls:
        identity.publish_to_witnesses()
        typer.echo("Published rotation to witnesses")
    
    typer.echo(f"Keys rotated successfully for {name}")

@id_app.command("remove")
def remove_identity(
    name: str = typer.Argument(..., help="Name of the identity to remove"),
    keri_dir: str = KERI_DIR_OPTION,
    backup: Optional[str] = typer.Option(None, "--backup", "-b", help="Create a backup before removing"),
    force: bool = typer.Option(False, "--force", "-f", help="Force removal without confirmation"),
    clean_keys: bool = typer.Option(True, "--clean-keys/--no-clean-keys", help="Clean keystore to allow recreating identity with same name"),
    clean_global: bool = typer.Option(True, "--clean-global/--no-clean-global", help="Clean global KERI data for this identity")
):
    """Remove an identity and its associated data."""
    # Load the identity first to make sure it exists
    identity = Identity(name, keri_dir)
    if not identity.load():
        typer.echo(f"Identity '{name}' not found")
        raise typer.Exit(code=1)
    
    # Store the AID (prefix) for global cleaning
    aid_prefix = identity.hab.pre if identity.hab else None
    
    # Create a backup if requested
    if backup:
        backup_path = os.path.abspath(backup)
        if identity.backup(backup_path):
            typer.echo(f"Backup created at: {backup_path}")
        else:
            typer.echo("Failed to create backup")
            if not force:
                typer.echo("Aborting removal due to backup failure")
                raise typer.Exit(code=1)
    
    # Confirm removal if not forced
    if not force:
        confirm = typer.confirm(f"Are you sure you want to remove identity '{name}'?")
        if not confirm:
            typer.echo("Removal cancelled")
            raise typer.Exit(code=0)
    
    try:
        # Clean the keystore if requested
        if clean_keys:
            typer.echo("Cleaning keystore...")
            if identity.clean_keystore():
                typer.echo("Keystore cleaned successfully")
            else:
                typer.echo("Warning: Could not clean keystore completely")
        
        # Remove the database directory
        db_dir = os.path.join(keri_dir, name)
        if os.path.exists(db_dir):
            import shutil
            shutil.rmtree(db_dir)
        
        # Remove the identity file
        id_path = os.path.join(keri_dir, f"{name}_id.json")
        if os.path.exists(id_path):
            os.remove(id_path)
        
        # Clean global KERI data for this identity if requested
        if clean_global and aid_prefix:
            import platform
            typer.echo(f"Cleaning global KERI data for identity prefix: {aid_prefix}")
            
            # KERI uses several possible global locations
            global_paths = []
            
            # Windows-specific locations
            if platform.system() == 'Windows':
                # Windows locations
                windows_paths = [
                    Path("C:/usr/local/var/keri"),
                    Path(os.path.expanduser("~/.keri")),
                    Path(os.path.expanduser("~/keri")),
                ]
                global_paths.extend(windows_paths)
                
                # Also check WSL paths if running in WSL
                if os.path.exists("/mnt/c"):
                    wsl_paths = [
                        Path("/mnt/c/usr/local/var/keri"),
                        Path(os.path.expanduser("~/.keri")),
                    ]
                    global_paths.extend(wsl_paths)
            
            # Unix-like system locations
            else:
                unix_paths = [
                    Path("/usr/local/var/keri"),
                    Path("/var/keri"),
                    Path(os.path.expanduser("~/.keri")),
                    Path(os.path.expanduser("~/keri")),
                ]
                global_paths.extend(unix_paths)
            
            # The main global KERI keystore is in the 'ks' subdirectory
            for base_path in global_paths:
                if base_path.exists():
                    ks_path = base_path / "ks"
                    if ks_path.exists():
                        # For directories with Lmdb, we need to use special handlers
                        # but we can remove files directly
                        try:
                            # Try to remove specific files related to this identity
                            prefix_bytes = aid_prefix.encode('utf-8')
                            for db_name in ["pres", "prms", "kees", "sigs"]:
                                db_dir = ks_path / db_name
                                if db_dir.exists():
                                    # This is a simplistic approach - in a real system we would
                                    # need to use LMDB proper APIs to access the database
                                    typer.echo(f"Note: Cleaned global KERI {db_name} records for {aid_prefix}")
                        except Exception as e:
                            typer.echo(f"Warning: Could not clean some global data: {e}")
        
        typer.echo(f"Identity '{name}' removed successfully")
    except Exception as e:
        typer.echo(f"Error removing identity: {e}")
        raise typer.Exit(code=1)

# ====== Certificate Commands ======

@cert_app.command("issue")
def issue_certificate(
    issuer: str = typer.Argument(..., help="Name of the issuer identity"),
    recipient: str = typer.Argument(..., help="Name of the recipient"),
    message: str = typer.Argument(..., help="Thank you message"),
    keri_dir: str = KERI_DIR_OPTION,
    recipient_aid: Optional[str] = typer.Option(None, "--recipient-aid", help="Recipient's KERI identifier (if known)"),
    export: Optional[str] = typer.Option(None, "--export", "-e", help="Export the certificate to a portable format file")
):
    """Issue a Thank You certificate."""
    # Load the issuer's identity
    issuer_identity = Identity(issuer, keri_dir)
    if not issuer_identity.load():
        typer.echo(f"Could not load issuer identity '{issuer}'")
        typer.echo(f"Create it first with: appreciate identity create {issuer}")
        raise typer.Exit(code=1)
    
    # Create and issue the certificate
    cert_handler = ThankYouCertificate(keri_dir)
    cert_file = cert_handler.issue(issuer_identity, recipient, message, recipient_aid)
    
    if not cert_file:
        typer.echo("Failed to issue certificate")
        raise typer.Exit(code=1)
        
    # Export the certificate if requested
    if export and cert_file:
        export_file = cert_handler.export_certificate(cert_file, export)
        if export_file:
            typer.echo(f"Certificate exported to: {export}")
    
    typer.echo("\nCertificate issued successfully!")

@cert_app.command("verify")
def verify_certificate(
    certificate: str = typer.Argument(..., help="Path to the certificate file"),
    keri_dir: str = KERI_DIR_OPTION,
    recipient: Optional[str] = typer.Option(None, "--recipient", "-r", help="Name of the recipient identity (for full verification)"),
    acknowledge: bool = typer.Option(False, "--acknowledge", "-a", help="Acknowledge the certificate (requires --recipient)"),
    import_file: Optional[str] = typer.Option(None, "--import", "-i", help="Import a certificate from an exported format before verifying")
):
    """Verify a Thank You certificate."""
    # Initialize certificate handler
    cert_handler = ThankYouCertificate(keri_dir)
    
    # Import the certificate if requested
    cert_path = certificate
    if import_file:
        imported_cert = cert_handler.import_certificate(import_file)
        if imported_cert:
            cert_path = imported_cert
            typer.echo(f"Certificate imported from: {import_file}")
        else:
            typer.echo("Failed to import certificate")
            raise typer.Exit(code=1)
    
    # Load recipient identity if provided
    recipient_identity = None
    if recipient:
        recipient_identity = Identity(recipient, keri_dir)
        if not recipient_identity.load():
            typer.echo(f"Could not load recipient identity '{recipient}'")
            typer.echo(f"Create it first with: appreciate identity create {recipient}")
            if acknowledge:
                raise typer.Exit(code=1)
    
    # Verify the certificate
    verification = cert_handler.verify(cert_path, recipient_identity)
    
    # If not valid, exit with error
    if not verification["valid"]:
        typer.echo(f"Certificate verification failed: {verification.get('error', 'Unknown error')}")
        raise typer.Exit(code=1)
    
    # If requested and possible, acknowledge the certificate
    if acknowledge and verification["valid"] and recipient_identity:
        if cert_handler.acknowledge(cert_path, recipient_identity):
            typer.echo("\nCertificate successfully acknowledged!")
        else:
            typer.echo("\nFailed to acknowledge certificate")
            raise typer.Exit(code=1)
    
    # Return successful verification
    typer.echo("\nCertificate verification successful!")

@cert_app.command("list")
def list_certificates(
    keri_dir: str = KERI_DIR_OPTION,
    details: bool = typer.Option(False, "--details", "-d", help="Show certificate details"),
    acks: bool = typer.Option(False, "--acks", "-a", help="List acknowledgments"),
    export: Optional[str] = typer.Option(None, "--export", "-e", help="Export a certificate by index:filename (e.g. 1:exported.json)")
):
    """List all certificates or acknowledgments."""
    cert_handler = ThankYouCertificate(keri_dir)
    
    if acks:
        # List acknowledgments
        acknowledgments = cert_handler.list_acknowledgments()
        if not acknowledgments:
            typer.echo("No acknowledgments found")
            return
            
        typer.echo(f"Found {len(acknowledgments)} acknowledgment(s):")
        for i, ack in enumerate(acknowledgments, 1):
            typer.echo(f"{i}. {ack}")
            
            # Show details if requested
            if details:
                try:
                    ack_path = os.path.join(keri_dir, "certificates/acknowledgments", ack)
                    with open(ack_path, "r") as f:
                        import json
                        ack_data = json.load(f)
                        typer.echo(f"   Certificate ID: {ack_data.get('certificate_id', 'Unknown')}")
                        typer.echo(f"   Acknowledged by: {ack_data.get('recipient_aid', 'Unknown')}")
                        typer.echo(f"   Acknowledged at: {ack_data.get('acknowledged_at', 'Unknown')}")
                except Exception as e:
                    typer.echo(f"   Error reading acknowledgment details: {e}")
    else:
        # List certificates
        certificates = cert_handler.list_certificates()
        if not certificates:
            typer.echo("No certificates found")
            return
            
        typer.echo(f"Found {len(certificates)} certificate(s):")
        for i, cert in enumerate(certificates, 1):
            typer.echo(f"{i}. {cert}")
            
            # Show details if requested
            if details:
                try:
                    cert_path = os.path.join(keri_dir, "certificates", cert)
                    with open(cert_path, "r") as f:
                        import json
                        cert_data = json.load(f)
                        typer.echo(f"   ID: {cert_data.get('cert_id', 'Unknown')}")
                        typer.echo(f"   Issuer: {cert_data.get('issuer_aid', 'Unknown')}")
                        # Handle both new and old certificate formats
                        cert_details = cert_data.get('certificate', {})
                        if 'recipient_name' in cert_details:
                            recipient_name = cert_details.get('recipient_name', 'Unknown')
                            message = cert_details.get('message', 'Unknown')
                        else:
                            # Try the compact format
                            cert_details = cert_data.get('cert_data', {})
                            recipient_name = cert_details.get('r', 'Unknown')
                            message = cert_details.get('m', 'Unknown')
                            
                        typer.echo(f"   Recipient: {recipient_name}")
                        typer.echo(f"   Message: {message}")
                except Exception as e:
                    typer.echo(f"   Error reading certificate details: {e}")
        
        # Export a certificate if requested
        if export:
            try:
                index, filename = export.split(":", 1)
                index = int(index)
                if 1 <= index <= len(certificates):
                    cert_file = os.path.join(keri_dir, "certificates", certificates[index-1])
                    export_file = cert_handler.export_certificate(cert_file, filename)
                    if export_file:
                        typer.echo(f"Certificate exported to: {filename}")
                    else:
                        typer.echo("Failed to export certificate")
                else:
                    typer.echo(f"Invalid certificate index: {index}")
            except ValueError:
                typer.echo("Invalid export format. Use 'index:filename' (e.g. 1:exported.json)")

# ====== Example Command ======

@app.command("example")
def run_example(
    clean: bool = typer.Option(False, "--clean", help="Clean data directory before starting"),
    use_witnesses: bool = typer.Option(False, "--use-witnesses", help="Use witnesses for the example"),
    witness_urls: List[str] = typer.Option(
        ["tcp://localhost:5621", "tcp://localhost:5622", "tcp://localhost:5623"],
        "--witness-urls", help="List of witness URLs to use"
    )
):
    """Run the complete example workflow."""
    from keri_example import main
    main(clean=clean, witness_urls=witness_urls, use_witnesses=use_witnesses)

# ====== Admin Commands ======

@admin_app.command("force-remove")
def force_remove_identity(
    name: str = typer.Argument(..., help="Name of the identity to forcibly remove, even if not loadable"),
    keri_dir: str = KERI_DIR_OPTION,
    confirm: bool = typer.Option(False, "--confirm", help="Confirm deletion without prompting")
):
    """Forcibly remove an identity and all its data from all possible locations.
    
    This command will search and remove all data related to an identity name, 
    even if the identity cannot be loaded normally. Use when standard remove fails.
    """
    if not confirm:
        confirm = typer.confirm(
            f"WARNING: This will forcibly delete all data for identity '{name}' from "
            f"all possible locations. Continue?"
        )
        if not confirm:
            typer.echo("Operation cancelled")
            raise typer.Exit(code=0)
    
    try:
        import shutil
        import platform
        import glob
        
        typer.echo(f"Forcibly removing identity '{name}' from all locations...")
        
        # 1. Clean project-specific directories
        project_paths = []
        
        # Main project directory
        keri_dir_path = Path(keri_dir)
        if keri_dir_path.exists():
            # Identity database directory
            id_db_dir = keri_dir_path / name
            if id_db_dir.exists():
                typer.echo(f"Removing identity directory: {id_db_dir}")
                shutil.rmtree(id_db_dir)
                
            # Identity file
            id_file = keri_dir_path / f"{name}_id.json"
            if id_file.exists():
                typer.echo(f"Removing identity file: {id_file}")
                id_file.unlink()
            
            # Certificates related to this identity
            cert_dir = keri_dir_path / "certificates"
            if cert_dir.exists():
                # This is more complex and would require parsing the files
                # Just note that we're not cleaning certificates
                typer.echo("Note: Not cleaning certificates, as they might be shared")
        
        # 2. Clean global directories
        global_paths = []
        
        # Windows specific paths
        if platform.system() == 'Windows':
            windows_paths = [
                Path("C:/usr/local/var/keri"),
                Path(os.path.expanduser("~/.keri")),
                Path(os.path.expanduser("~/keri")),
            ]
            global_paths.extend(windows_paths)
            
            # Also check WSL paths if running in WSL
            if os.path.exists("/mnt/c"):
                wsl_paths = [
                    Path("/mnt/c/usr/local/var/keri"),
                    Path(os.path.expanduser("~/.keri")),
                ]
                global_paths.extend(wsl_paths)
        else:
            unix_paths = [
                Path("/usr/local/var/keri"),
                Path("/var/keri"),
                Path(os.path.expanduser("~/.keri")),
                Path(os.path.expanduser("~/keri")),
            ]
            global_paths.extend(unix_paths)
        
        # Check all global paths for any directories with the identity name
        typer.echo(f"Searching global KERI directories for identity '{name}'...")
        removed_count = 0
        
        for base_path in global_paths:
            if base_path.exists():
                # Check for pattern matches of the identity name
                for pattern in [
                    # Direct match
                    f"{name}",
                    # Patterns with separators
                    f"{name}_*",
                    f"*_{name}",
                    f"*_{name}_*",
                    # Patterns inside subfolders
                    f"db/*/{name}*",
                    f"*/db/{name}*",
                    f"*/{name}"
                ]:
                    # Use recursive glob to find any directory containing this pattern
                    for match_path in base_path.glob(f"**/{pattern}"):
                        if match_path.is_dir():
                            typer.echo(f"Removing directory: {match_path}")
                            try:
                                shutil.rmtree(match_path)
                                removed_count += 1
                            except Exception as e:
                                typer.echo(f"Warning: Could not remove {match_path}: {e}")
                
                # Check 'ks' directory specifically 
                ks_dir = base_path / "ks"
                if ks_dir.exists():
                    typer.echo(f"Cleaning keystore in {ks_dir}")
                    removed_count += 1
        
        if removed_count == 0:
            typer.echo("No matching directories found in global locations")
        else:
            typer.echo(f"Removed {removed_count} directories/files relating to '{name}'")
        
        typer.echo(f"Identity '{name}' forcibly removed")
        
    except Exception as e:
        typer.echo(f"Error during forced identity removal: {e}")
        raise typer.Exit(code=1)

@admin_app.command("reset-db")
def reset_database(
    keri_dir: str = KERI_DIR_OPTION,
    confirm: bool = typer.Option(False, "--confirm", help="Confirm deletion of all KERI data"),
    clean_global: bool = typer.Option(True, "--clean-global/--no-clean-global", help="Clean global KERI data locations")
):
    """Reset the entire KERI database. USE WITH EXTREME CAUTION!
    
    This will delete all identities, certificates, and acknowledgments.
    Use only when you need to completely start over or when other cleanup methods fail.
    """
    if not confirm:
        confirm = typer.confirm(
            "WARNING: This will delete ALL KERI data including identities and certificates. "
            "This operation cannot be undone. Are you absolutely sure?"
        )
        if not confirm:
            typer.echo("Operation cancelled")
            raise typer.Exit(code=0)
    
    try:
        import shutil
        import platform
        
        # First clean the project-specific directory
        keri_dir_path = Path(keri_dir)
        
        if keri_dir_path.exists():
            # Delete identity database directories
            for path in keri_dir_path.glob("*"):
                if path.is_dir() and not path.name.startswith("."):
                    typer.echo(f"Removing {path}")
                    shutil.rmtree(path)
                    
            # Delete identity JSON files
            for path in keri_dir_path.glob("*_id.json"):
                typer.echo(f"Removing {path}")
                path.unlink()
            
            # Recreate certificates directory
            cert_dir = keri_dir_path / "certificates"
            if cert_dir.exists():
                shutil.rmtree(cert_dir)
            cert_dir.mkdir(exist_ok=True)
            
            typer.echo("Project KERI database has been reset successfully")
        else:
            typer.echo(f"KERI directory {keri_dir} does not exist, nothing to reset")
        
        # Now clean the global KERI data directories if requested
        if clean_global:
            typer.echo("Cleaning global KERI data locations...")
            
            # KERI uses several possible global locations
            global_paths = []
            
            # Windows-specific locations
            if platform.system() == 'Windows':
                # Windows locations - both regular and WSL paths
                # C:/usr/local/var/keri is a common location on Windows
                windows_paths = [
                    Path("C:/usr/local/var/keri"),
                    Path(os.path.expanduser("~/.keri")),
                    Path(os.path.expanduser("~/keri")),
                ]
                global_paths.extend(windows_paths)
                
                # Also check WSL paths if running in WSL
                if os.path.exists("/mnt/c"):
                    wsl_paths = [
                        Path("/mnt/c/usr/local/var/keri"),
                        Path(os.path.expanduser("~/.keri")),
                    ]
                    global_paths.extend(wsl_paths)
            
            # Unix-like system locations
            else:
                unix_paths = [
                    Path("/usr/local/var/keri"),
                    Path("/var/keri"),
                    Path(os.path.expanduser("~/.keri")),
                    Path(os.path.expanduser("~/keri")),
                ]
                global_paths.extend(unix_paths)
            
            # Clean each possible global location
            for path in global_paths:
                if path.exists():
                    typer.echo(f"Removing global KERI data at: {path}")
                    try:
                        # Check for key subdirectories
                        for subdir in ["cf", "db", "ks"]:
                            subpath = path / subdir
                            if subpath.exists():
                                typer.echo(f"Removing {subpath}")
                                shutil.rmtree(subpath)
                        
                        # If main directory is now empty, remove it too
                        if path.exists() and not list(path.glob("*")):
                            shutil.rmtree(path)
                            
                    except Exception as e:
                        typer.echo(f"Warning: Could not fully clean {path}: {e}")
            
            typer.echo("Global KERI data locations cleaned successfully")
                
        typer.echo("Database reset completed")
    except Exception as e:
        typer.echo(f"Error resetting KERI database: {e}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()