# KERI Library Review

I have reviewed the `keri` library (version 1.3.4) installed in your `.venv`. KERI stands for **Key Event Receipt Infrastructure**, and it is a decentralized identity system that focuses on "autonomic identifiers" and "key event logs."

## 1. Core Architecture: KEL (Key Event Log)
The fundamental concept in KERI is the **Key Event Log (KEL)**. Instead of relying on a central authority or a global blockchain to prove identity, KERI uses a hash-chained log of events that define the state of an identifier (AID).
- **Inception (`icp`)**: Defines the initial keys and rules for the identifier.
- **Rotation (`rot`)**: Changes the signing keys, providing forward secrecy.
- **Interaction (`ixn`)**: Anchors external data into the log.

## 2. Key Modules and Primitives

### `keri.core.coring` & `keri.core.signing`
These modules contain the "Matter" classes, which handle self-describing cryptographic data using **CESR** (Composable Event Streaming Representation).
- **`Matter`**: Base class for all crypto material. It uses derivation codes to tell you what it is (e.g., an Ed25519 public key vs. a Blake3 hash) within the string itself.
- **`Signer`**: Handles private keys and signing operations.
- **`Verfer`**: Handles public keys and signature verification.
- **`Diger`**: Handles hashing (digests).
- **`Salter`**: Generates deterministic secrets from a salt.

### `keri.core.eventing`
This is the heart of the library's logic.
- **`Kever`**: The "Key Event Verifier." It processes events and maintains the current "Key State" of an identifier.
- **`Kevery`**: The "Key Event Message Processing Facility." It acts as a processor for streams of KERI messages, creating and updating `Kever` instances as it goes.

### `keri.app.habbing`
This module provides high-level abstractions for managing identities.
- **`Habery`**: A "factory" and container for multiple identities (Habitats). It manages the underlying `lmdb` databases for keys and events.
- **`Hab`**: Short for "Habitat." it represents a specific identifier's environment, including its keys, logs, and state.

## 3. CESR Encoding (qb64/qb2)
KERI uses a unique encoding format called **CESR**. You'll see strings starting with specific characters (like `B`, `D`, `E`):
- **`qb64`**: A Base64 representation that is 24-bit aligned and includes a prefix (derivation code) that identifies the algorithm and length.
- **`qb2`**: The binary equivalent.

## 4. How it works in practice
1. You create a **`Habery`** to manage your local environment.
2. You create a **`Hab`** (Inception) which generates your initial keys and AID.
3. You share your **Inception Event** with others.
4. When you need to rotate keys, you create a **Rotation Event**.
5. Others use a **`Kevery`** (or a `Kever` for your specific AID) to process these events and verify that the changes were authorized by your previous keys.

> [!NOTE]
> The library is heavily asynchronous and relies on the `hio` library for its internal event loop and I/O.
