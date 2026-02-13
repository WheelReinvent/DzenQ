import sys
import argparse
import logging
from keri.app import habbing
from keriac.agents.identity import Identity
from keriac.documents.credential import Credential
from keriac.transport import unpack

def accept_acdc(file_path: str, environment_name: str = "keriac", base: str = "", temp: bool = False, salt: str = None, bran: str = None):
    """
    Accept an ACDC from a CESR bundle and anchor it to the recipient's KEL.
    """
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger("accept")

    # 1. Read and unpack the CESR bundle
    try:
        with open(file_path, "rb") as f:
            bundle = f.read()
        objects = unpack(bundle)
    except Exception as e:
        logger.error(f"Failed to read or unpack bundle at {file_path}: {e}")
        sys.exit(1)

    # 2. Find the ACDC in the bundle
    acdc = next((obj for obj in objects if isinstance(obj, Credential)), None)
    if not acdc:
        logger.error(f"No ACDC found in bundle at {file_path}")
        sys.exit(1)

    recipient_aid = acdc.recipient
    if not recipient_aid:
        logger.error("ACDC does not have a recipient AID.")
        sys.exit(1)
    
    recipient_aid_str = str(recipient_aid)
    logger.info(f"ACDC found. Recipient AID: {recipient_aid_str}")

    # 3. Resolve the local identity matching this AID
    # We open the Habery to look up which alias owns this AID
    logger.info(f"Opening Habery: name={environment_name}, base={base}, temp={temp}")
    hby = habbing.Habery(name=environment_name, base=base, temp=temp)
    
    # Try to find by AID in the database
    habitat_record = hby.db.habs.get(recipient_aid_str)
    if not habitat_record:
        logger.error(f"No local identity found for AID {recipient_aid_str} in environment '{environment_name}'")
        hby.close()
        sys.exit(1)
    
    alias = habitat_record.name
    logger.info(f"Found local identity alias: '{alias}'")
    hby.close() # Close it so Identity can reopen its own Resources

    # 4. Initialize the Identity and anchor the ACDC
    # We use the same environment parameters and SECRET
    identity = Identity(name=alias, base=base, temp=temp, salt=salt, bran=bran)
    
    # 5. Idempotent anchoring
    if identity.kel.is_anchored(acdc.said):
        logger.warning(f"ACDC {acdc.said} is already anchored in '{alias}' KEL. Skipping.")
    else:
        try:
            identity.anchor(acdc)
            logger.info(f"Successfully anchored ACDC {acdc.said} in '{alias}' KEL.")
        except Exception as e:
            logger.error(f"Failed to anchor ACDC: {e}")
            identity.close()
            sys.exit(1)
    
    identity.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Accept and anchor an ACDC from a CESR bundle.")
    parser.add_argument("path", help="Path to the .cesr bundle file")
    parser.add_argument("--env", default="keriac", help="Environment name (Habery name)")
    parser.add_argument("--base", default="", help="Directory prefix for database")
    parser.add_argument("--temp", action="store_true", help="Use temporary storage (mostly for tests)")
    parser.add_argument("--salt", help="qb64 salt for key derivation")
    parser.add_argument("--bran", help="Passphrase for key derivation")

    args = parser.parse_args()
    accept_acdc(args.path, environment_name=args.env, base=args.base, temp=args.temp, salt=args.salt, bran=args.bran)
