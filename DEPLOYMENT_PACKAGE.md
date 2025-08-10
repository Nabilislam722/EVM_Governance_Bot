# Hemi Network Discord Governance Bot - Complete Code Package

## Project Structure
```
hemi-discord-bot/
├── main.py                     # Entry point
├── requirements.txt            # Python dependencies
├── .env.example               # Environment configuration template
├── README.md                  # Setup instructions
├── bot/                       # Main bot code directory
│   ├── __init__.py
│   ├── main.py               # Bot main logic
│   ├── governance_monitor.py # Governance monitoring
│   └── utils/                # Utility modules
│       ├── __init__.py
│       ├── config.py         # Configuration management
│       ├── hemi_network.py   # Hemi Network integration
│       ├── logger.py         # Logging setup
│       ├── button_handler.py # Discord voting buttons
│       ├── embed_config.py   # Discord embed formatting
│       ├── data_processing.py# Data processing utilities
│       ├── task_handler.py   # Task management
│       ├── permission_check.py # Permission system
│       ├── argument_parser.py # Command line arguments
│       ├── gov2.py           # Legacy governance (unused)
│       └── subquery.py       # Legacy substrate (unused)
└── data/                      # Data storage
    ├── vote_counts.json      # Discord voting data
    ├── governance_cache.json # Proposal cache
    ├── onchain_votes.json    # Blockchain votes
    └── backup/               # Automated backups
```

## Quick Setup Instructions

1. **Install Python 3.11+**
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Configure environment**: Copy `.env.example` to `.env` and update values
4. **Set Discord API key**: Get from Discord Developer Portal
5. **Run the bot**: `python main.py`

## Key Features
- ✅ **Hemi Network Integration** - Monitors Ethereum-compatible blockchain
- ✅ **Discord Forum Threads** - Auto-creates proposal discussions
- ✅ **Community Voting** - 👍 AYE, 👎 NAY, ⚪ RECUSE buttons
- ✅ **Slash Commands** - `/thread` and `/vote` commands
- ✅ **Real-time Monitoring** - Checks for new governance proposals
- ✅ **Role-based Permissions** - Admin, voter, and notification roles
- ✅ **Data Persistence** - JSON-based storage with backups

## Network Configuration
- **Hemi Testnet**: ChainID 743111, RPC: https://testnet.rpc.hemi.network/rpc
- **Hemi Mainnet**: ChainID 43111, RPC: https://rpc.hemi.network/rpc

Bot is currently configured for Testnet by default.

---
*Generated from working Replit deployment - August 2025*