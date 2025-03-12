# Decentralized File Storage Manager AI Agent

The Decentralized File Storage Manager (DFS Manager) is an AI agent built with the NEAR AI CLI to manage file storage on IPFS, integrated with NEAR Protocol smart contracts. It automates secure file uploads, extracts metadata using specialized AI agents (e.g., BPM for audio), optimizes IPFS storage for fast retrieval, and enforces token-based access control. Designed as an independent tool, it offers blockchain developers a modular solution for decentralized content management, initially developed for the 1000fans app but adaptable to other projects.

## Repo Structure
- `contracts/dfs/`: Smart contract for `dfs.devbot.testnet` (replaces IPFS proxy).
- `agents/storage-agent/`: Storage Agent for file uploads.
- `agents/dfs-manager/`: Manager Agent overseeing the system.
- `scripts/`: Deployment and testing scripts.

### Purpose
The DFS Manager aims to:
- Replace centralized storage (such as AWS S3 or Google Firebase) with IPFS for decentralized, content-addressed file hosting.
- Use AI to analyze and index files, enhancing retrieval efficiency.
- Leverage NEAR smart contracts for group-based access control and metadata tracking.
- Provide a reusable agent framework for developers building on NEAR and IPFS.

### Architecture
Inspired by *"A Secure File Sharing System Based on IPFS and Blockchain"* (2022) [5], the DFS Manager adapts a group-based model, replacing the IPFS proxy with NEAR smart contracts and adding an AI agent team for retrieval optimization.

#### System Entities
- **Owners**: NEAR account holders (e.g., 1000fans.testnet) who create content groups and upload files. 
- **Users**: Token holders authorized to access group-specific files.
- **NEAR Smart Contract**: Manages group keys, access control, and metadata (CIDs, file hashes).
- **NEAR Blockchain**: Logs transactions and enforces access.
- **IPFS**: Stores encrypted files, pinned for availability.
- **AI Agent Team**: 
    - Manager Agent: Chats with users, routes tasks (e.g., uploads, NFT actions).
    - Upload Agent: Receives files, and delegates feature extraction.
    - Feature Extraction Agents: Extracts features from files using dedicated pre-trained models.
    - Storage Agent: Encrypts files, pins them to IPFS, and updates NEAR metadata.

#### Workflow
1. **User Interaction**: Owners/users chat with the Manager Agent via a frontend interface.
2. **File Upload**: Owners drop files; the Upload Agent receives them and routes to extraction agents.
3. **Feature Extraction**: AI analyzes files (e.g., audio genre, video tags) and generates metadata.
4. **Encryption**: The Storage Agent encrypts files with a group key from the NEAR contract.
6. **IPFS Storage**: Encrypted files are pinned to IPFS, generating CIDs (e.g., Qm...)..
7. **Blockchain Logging**: The Storage Agent records CIDs and file hashes on the NEAR contract.
8. **Access**: Token holders request files; NEAR verifies ownership and releases decryption keys.

#### Retrieval Optimization
- **Local Pinning**: Agent pins popular files on owner nodes.
- **Geo-Distribution**: Pins files on regional IPFS nodes.
- **Caching**: Off-chain cache stores recent requests.
- **Erasure Coding**: Redundant shards enable parallel retrieval.
- **Indexing**: Metadata (e.g., BPM) is used to cluster files on IPFS (e.g., /bpm-120/).
- **Retrieval**: IPFS DHT and strategic pinning ensure fast access.
- **Security**: Group keys encrypt files; NEAR enforces token-gated access.

#### Benefits
- Decentralized: Replaces centralized storage with IPFS.
- Efficient: AI-optimized indexing speeds up retrieval.
- Secure: Token-based access ensures privacy.
- Modular: Reusable across NEAR-based apps.

-----------------------------------------------------
### Literature review: Designing a Decentralized File Storage Manager Agent for IPFS.
Centralized storage struggles with single points of failure and scalability, driving the shift to decentralized systems [2, 3]. IPFS provides a content-addressed, peer-to-peer file system ideal for large data, enhanced by blockchain for security and access control [1, 3, 4]. This review leverages key research [1-4] to design an AI agent that streamlines file management on IPFS with NEAR smart contracts.

#### IPFS: The Foundation of Decentralized Storage
IPFS uses a Merkle DAG to split files into hashed blocks, enabling deduplication, integrity, and retrieval via a Distributed Hash Table (DHT) [1]. BitSwap incentivizes caching, ensuring availability [1]. Content-addressing eliminates redundancy and supports permanent links, outpacing HTTP [1, 2].

#### Blockchain Integration: Security and Incentives
Blockchain adds incentives and access control to IPFS [2, 3]. Filecoin’s storage market and proofs (PoRep, PoSt) exemplify secure, verifiable storage [4]. NEAR adapts these principles: immutability, encryption, and fault tolerance for decentralized management [3, 4].

#### Challenges & Solutions
IPFS retrieval slows with scale [2]; geo-distributed pinning and erasure coding mitigate this [4]. Privacy risks are addressed with off-chain metadata and encryption [3]. Mutable updates use IPNS [2]; NEAR penalizes unreliable nodes [4].

IPFS’s content-addressed model [1], enhanced by blockchain [3, 4], empowers an AI agent for decentralized storage. It ensures secure uploads, smart indexing, and fast retrieval, refined further in the strategy below.

### Bibliographical References
- [1]: 2014 [IPFS - Content Addressed, Versioned, P2P File System](https://arxiv.org/abs/1407.3561)
- [2]: 2020 [When Blockchain Meets Distributed File Systems:
An Overview, Challenges, and Open Issues](https://www.researchgate.net/publication/339067478_When_Blockchain_Meets_Distributed_File_Systems_An_Overview_Challenges_and_Open_Issues)
- [3]: 2023 [A Comprehensive Survey on Blockchain-Based
Decentralized Storage Networks](https://ieeexplore.ieee.org/document/10026822)
- [4]: 2017 [Filecoin: A Decentralized Storage Network](https://filecoin.io/filecoin.pdf)
- [5]: 2022 [A Secure File Sharing System Based on IPFS and Blockchain](https://www.researchgate.net/publication/360383364_A_Secure_File_Sharing_System_Based_on_IPFS_and_Blockchain)