# Decentralized File Storage Manager - Team of AI Agents

The Decentralized File Storage Manager (DFS Manager) is a team of AI Agents, built with NEAR AI and integrated with NEAR smart contracts, in charge for handling decentralized file storage on IPFS. It is a standalone solution made for any app builder willing to move from central databases to decentralized storage networks. The DFS manager automates the file processing: from the file collection through a drag-and-drop window, the file is passed through a funnel of dedicated agents specialized in file analysis, tagging, indexing, including metadata extraction with AI, until a final file storage optimized for fast retrieval. 

![DFS Manager architecture](DFS_manager.jpg)

> **Why Decentralized Storage ?**
> Centralized storages struggle with single points of failure and scalability, while content-addressed, peer-to-peer file systems enhanced by blockchain offer security and access control. Using a team of AI agents to handle the technicity of Decentralized Storage Networks make it easy and accessible to everyone.

### Architecture
Inspired by [A Secure File Sharing System Based on IPFS and Blockchain](https://www.researchgate.net/publication/360383364_A_Secure_File_Sharing_System_Based_on_IPFS_and_Blockchain) (2022), the DFS Manager adopts a group-based model, where NEAR Protocol smart contracts are used for access control and transaction recording, while various Hugging Face-hosted AI models are called on-demand to process file analysis and metadata extraction.

### System Entities
- **Owner**: NEAR accounts holding a dApp or content data to provide access to. 
- **Users**: Token holders authorized to access group-specific files.
- **Smart Contract**: Manages group keys, access control, and metadata (IPFS CIDs, file hashes).
- **NEAR Blockchain**: Logs transactions and enforces access.
- **IPFS**: Stores encrypted files, pinned for availability.
- **AI Agents**: A team of specialized agents working together:
    - Manager Agent: Chats with users, routes tasks (e.g., uploads, NFT actions).
    - Upload Agent: Receives files, and delegates feature extraction.
    - Feature Extraction Agents: Extract features from files using dedicated pre-trained models (e.g. tempo detection).
    - Blockchain Tracking Agent: Automates the integration with the blockchain layer.
    - Storage Agent: Encrypts files, pins them to IPFS, and updates NEAR metadata.

### Next Steps:
- Set up Near AI & Cargo Near.
- Set up IPFS & Pinata.
- Create & Deploy a minimal smart contract to testnet.
- Create & Deploy a minimal Storage Agent on NEAR AI registry.
- Test file Upload to IPFS with 1. NEAR CLI, 2. AI Agent, 3. Token-Gate Contract.
- Grow the team of AI Agents and the smart contract with more features.

### Repository content:
- **agents folder**: contains each individual agents' code generated using NEAR AI CLI. Each agent has its own sub-folder with the agents.py and metadata.json files.
- **contract folder**: contains the smart contract generated with Cargo Near and the wasm build artifacts. The smart contract is written in Rust. 
- **scripts folder**: contains all necessary execution scripts.