from keriac import Identifier, ACDC, SAID
import json

def debug_said():
    alice = Identifier(name="alice")
    try:
        schema_said = "EM9M_xyz_dummy_schema_said_1234567890" 
        attributes = {"name": "Alice"}
        cred = ACDC.create(issuer=alice, schema=schema_said, attributes=attributes)
        
        original_said = cred.said
        calculated_said = SAID.calculate(cred)
        
        print(f"DEBUG: original   = '{original_said}'")
        print(f"DEBUG: calculated = '{calculated_said}'")
        assert calculated_said == original_said
        
    finally:
        alice.close()

if __name__ == "__main__":
    debug_said()
