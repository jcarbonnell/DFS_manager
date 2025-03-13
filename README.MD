# Decentralized File Storage Manager

The Decentralized File Storage Manager (DFS Manager) is an AI Agent built with NEAR AI and integrated with the NEAR Protocol Blockchain, to handle file storage on IPFS. The DFS Manager automates a secure file processing, from the drag-and-drop interface to the final storage and retrieval, including metadata extraction with a team of specialized AI models (e.g. tempo detection for audio files). The DFS Manager optimizes file storage on IPFS for fast retrieval, and enforces a token-based access control. Designed as a standalone assistant, it offers blockchain developers a functional solution to upgrade their apps with a decentralized backend.

The DFS Manager aims to:
- **Replace centralized storage** (such as AWS S3 or Google Firebase) with the decentralized storage network IPFS.
- **Use AI to analyze and index files**, enhancing retrieval efficiency.
- **Leverage NEAR smart contracts** for group-based access control and transaction recording.
- **Provide a reusable agent framework** for developers building on NEAR and IPFS.

### Architecture
Inspired by *"A Secure File Sharing System Based on IPFS and Blockchain"* (2022) [5], the DFS Manager adapts a group-based model, replacing the proposed IPFS proxy with NEAR smart contracts and adding a team of AI agents in charge for the most efficient file uploading.

### System Entities
- **Owners**: NEAR account holders who create content groups and upload files. 
- **Users**: Token holders authorized to access group-specific files.
- **NEAR Smart Contract**: Manages group keys, access control, and metadata (IPFS CIDs, file hashes).
- **NEAR Blockchain**: Logs transactions and enforces access.
- **IPFS**: Stores encrypted files, pinned for availability.
- **AI Agents**: A team of specialized agents working together:
    - Manager Agent: Chats with users, routes tasks (e.g., uploads, NFT actions).
    - Upload Agent: Receives files, and delegates feature extraction.
    - Feature Extraction Agents: Extract features from files using dedicated pre-trained models (e.g. tempo detection).
    - Storage Agent: Encrypts files, pins them to IPFS, and updates NEAR metadata.

### Next Steps:
- ~~Set up Near AI & Cargo Near~~.
- ~~Set up IPFS & Pinata~~.
- ~~Create & Deploy a minimal smart contract to testnet~~.
- Create & Deploy a minimal Storage Agent on NEAR AI registry.
- ~~Test file Upload to IPFS with 1. NEAR CLI~~, 2. AI Agent, 3. Smart Contract.
- Grow the team of AI Agents and the smart contract with more features.

-----------------------------------------------------
## Literature review: Designing a Decentralized File Storage Manager for IPFS.
Centralized storages struggle with single points of failure and scalability, driving the shift to decentralized systems [2],[3]. IPFS provides a content-addressed, peer-to-peer file system, ideal for large data, enhanced by blockchain for security and access control [1],[3],[4]. This review leverages key research [1],[4] to design an AI agent that streamlines file management on IPFS with NEAR smart contracts.

#### IPFS: The Foundation of Decentralized Storage
IPFS uses a Merkle DAG to split files into hashed blocks, enabling deduplication, integrity, and retrieval via a Distributed Hash Table (DHT) [1]. BitSwap incentivizes caching, ensuring availability [1]. Content-addressing eliminates redundancy and supports permanent links, outpacing HTTP [1],[2].

#### Blockchain Integration: Security and Incentives
Blockchain adds incentives and access control to IPFS [2],[3]. Filecoin’s storage market and proofs (PoRep, PoSt) exemplify secure, verifiable storage [4]. NEAR adapts these principles: immutability, encryption, and fault tolerance for decentralized management [3],[4].

#### Challenges & Solutions
IPFS retrieval slows with scale [2]; geo-distributed pinning and erasure coding mitigate this [4]. Privacy risks are addressed with off-chain metadata and encryption [3]. Mutable updates use IPNS [2]; NEAR penalizes unreliable nodes [4].

IPFS’s content-addressed model [1], enhanced by blockchain [3],[4], empowers an AI agent for decentralized storage. It ensures secure uploads, smart indexing, and fast retrieval, refined further in the strategy below.

### Bibliographical References
- [1]: 2014 [IPFS - Content Addressed, Versioned, P2P File System](https://arxiv.org/abs/1407.3561)
- [2]: 2020 [When Blockchain Meets Distributed File Systems:
An Overview, Challenges, and Open Issues](https://www.researchgate.net/publication/339067478_When_Blockchain_Meets_Distributed_File_Systems_An_Overview_Challenges_and_Open_Issues)
- [3]: 2023 [A Comprehensive Survey on Blockchain-Based
Decentralized Storage Networks](https://ieeexplore.ieee.org/document/10026822)
- [4]: 2017 [Filecoin: A Decentralized Storage Network](https://filecoin.io/filecoin.pdf)
- [5]: 2022 [A Secure File Sharing System Based on IPFS and Blockchain](https://www.researchgate.net/publication/360383364_A_Secure_File_Sharing_System_Based_on_IPFS_and_Blockchain)