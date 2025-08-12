# EVM layer 2 Network Discord Governance Bot - Local Deployment

##  Complete Working Code Package

This is the complete Hemi Network Discord Governance Bot code, successfully migrated from Polkadot and tested on Replit.

##  Setup Instructions

### 1. Install Dependencies
```bash
pip install -r local_requirements.txt
```

### 2. Environment Configuration
Create a `.env` file with your Discord bot token:
```bash
# Required
DISCORD_API_KEY=your_discord_bot_token_here

# Optional - Update if needed
DISCORD_SERVER_ID=887298825193152572
DISCORD_FORUM_CHANNEL_ID=1402941602221129728
NETWORK_NAME=hemi
SYMBOL=ETH
HEMI_RPC=https://testnet.rpc.hemi.network/rpc
SOLO_MODE=True
READ_ONLY=False
```

### 3. Create Data Directory
```bash
mkdir -p data/backup
mkdir -p data/vote_periods
echo '{}' > data/vote_counts.json
echo '{}' > data/governance_cache.json
echo '{}' > data/onchain_votes.json
```

### 4. Run the Bot
```bash
python main.py
```

##  Features Working

 **Hemi Network Connection** - Connects to Hemi Testnet (ChainID: 743111)  
 **Discord Integration** - Creates forum threads for proposals  
 **Voting Buttons** - 👍 AYE, 👎 NAY, ⚪ RECUSE  
 **Slash Commands** - `/thread` and `/vote`  
 **Real-time Monitoring** - Checks for new proposals every 3 hours  
 **Role Management** - Admin, voter, notification roles  
 **Data Backup** - Automatic rotating backups  

## 🔧 Network Configuration

**Current Setup (Testnet):**
- RPC: https://testnet.rpc.hemi.network/rpc  
- ChainID: 743111  
- Explorer: https://testnet.explorer.hemi.xyz  

**Switch to Mainnet:**
Update your `.env` file:
```bash
HEMI_RPC=https://rpc.hemi.network/rpc
HEMI_EXPLORER=https://explorer.hemi.xyz/api/v2/
```

## File Structure
```
your-project/
├── main.py                    # Entry point (provided below)
├── local_requirements.txt     # Dependencies (provided below)
├── .env                      # Your configuration
├── bot/                      # Main bot directory
│   ├── main.py              # Bot logic
│   ├── governance_monitor.py # Proposal monitoring  
│   └── utils/               # Utilities
│       ├── config.py        # Configuration
│       ├── hemi_network.py  # Hemi integration
│       ├── button_handler.py # Voting buttons
│       ├── logger.py        # Logging
│       ├── embed_config.py  # Discord embeds
│       ├── data_processing.py # Data management
│       ├── task_handler.py  # Background tasks
│       ├── permission_check.py # Permissions
│       └── argument_parser.py # CLI args
└── data/                    # Data storage
    ├── vote_counts.json     # Voting data
    ├── governance_cache.json # Proposal cache
    └── backup/             # Auto backups
```

## Discord Setup

1. **Create Discord Application**: https://discord.com/developers/applications
2. **Create Bot**: In your application, go to "Bot" section
3. **Get Token**: Copy the bot token to your `.env` file
4. **Invite Bot**: Use OAuth2 URL generator with these permissions:
   - Send Messages
   - Use Slash Commands  
   - Manage Threads
   - Create Public Threads
   - Embed Links
   - Attach Files
   - Read Message History
   - Add Reactions

## Testing

Once running, test in your Discord server:
- Type `/thread` or `/vote` slash commands
- Check for auto-created proposal threads  
- Try the voting buttons: 👍 AYE, 👎 NAY, ⚪ RECUSE

## Logs

Bot will show in console:
```
2025-08-10 15:13:58 - utils.hemi_network - INFO - Connecting to Hemi Network
2025-08-10 15:13:58 - utils.hemi_network - INFO - Successfully connected to Hemi Network (Chain ID: 743111)
2025-08-10 15:13:59 - utils.hemi_network - INFO - Found 2 active Hemi Network proposals
```

---
**Status**: Fully tested and working on Hemi Network  
**Migration**: Successfully converted from Polkadot to Hemi  
**Last Updated**: August 10, 2025
**Author**: Nabil
