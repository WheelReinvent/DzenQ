import pysodium
from pysodium import sodium

print(sodium.sodium_version_string().decode('utf8'))
print(pysodium.sodium_version_check(major=1, minor=0, patch=21))


import pysodium

pk, sk = pysodium.crypto_sign_keypair()  # pk=32 bytes, sk=64 bytes

print("public (hex):", pk.hex())
print("secret (hex):", sk.hex())

