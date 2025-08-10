"""
Configuration management for the Discord Governance Bot.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for bot settings."""
    
    def __init__(self):
        # Discord Settings
        self.DISCORD_API_KEY = os.getenv('DISCORD_API_KEY', '')
        self.DISCORD_SERVER_ID = int(os.getenv('DISCORD_SERVER_ID', '887298825193152572'))
        self.DISCORD_FORUM_CHANNEL_ID = int(os.getenv('DISCORD_FORUM_CHANNEL_ID', '1402941602221129728'))
        self.DISCORD_SUMMARIZER_CHANNEL_ID = int(os.getenv('DISCORD_SUMMARIZER_CHANNEL_ID', '887298825193152575'))
        self.DISCORD_SUMMARY_ROLE = os.getenv('DISCORD_SUMMARY_ROLE', 'King')
        self.DISCORD_VOTER_ROLE = os.getenv('DISCORD_VOTER_ROLE', '1301051676555350036')
        self.DISCORD_ADMIN_ROLE = os.getenv('DISCORD_ADMIN_ROLE', 'admin')
        self.DISCORD_NOTIFY_ROLE = os.getenv('DISCORD_NOTIFY_ROLE', 'DOT-GOV')
        self.DISCORD_EXTRINSIC_ROLE = os.getenv('DISCORD_EXTRINSIC_ROLE', 'The role you want to use to notify when a vote has been cast onchain')
        self.DISCORD_ANONYMOUS_MODE = os.getenv('DISCORD_ANONYMOUS_MODE', 'True').lower() == 'true'
        self.DISCORD_TITLE_MAX_LENGTH = int(os.getenv('DISCORD_TITLE_MAX_LENGTH', '95'))
        self.DISCORD_BODY_MAX_LENGTH = int(os.getenv('DISCORD_BODY_MAX_LENGTH', '2000'))
        
        # Network Settings
        self.NETWORK_NAME = os.getenv('NETWORK_NAME', 'hemi')
        self.SYMBOL = os.getenv('SYMBOL', 'ETH')
        self.TOKEN_DECIMAL = float(os.getenv('TOKEN_DECIMAL', '1e18'))
        self.HEMI_RPC = os.getenv('HEMI_RPC', 'https://testnet.rpc.hemi.network/rpc')
        self.HEMI_EXPLORER = os.getenv('HEMI_EXPLORER', 'https://testnet.explorer.hemi.xyz/api/v2/')
        
        # Wallet Settings
        self.SOLO_MODE = os.getenv('SOLO_MODE', 'True').lower() == 'true'
        self.PROXIED_ADDRESS = os.getenv('PROXIED_ADDRESS', '')
        self.PROXY_ADDRESS = os.getenv('PROXY_ADDRESS', '')
        self.MNEMONIC = os.getenv('MNEMONIC', '')
        self.VOTE_WITH_BALANCE = float(os.getenv('VOTE_WITH_BALANCE', '1'))
        self.CONVICTION = os.getenv('CONVICTION', 'Locked4x')
        self.DISCORD_PROXY_BALANCE_ALERT = int(os.getenv('DISCORD_PROXY_BALANCE_ALERT', '0'))
        self.PROXY_BALANCE_ALERT = float(os.getenv('PROXY_BALANCE_ALERT', '1.1'))
        self.MIN_PARTICIPATION = int(os.getenv('MIN_PARTICIPATION', '0'))
        self.THRESHOLD = float(os.getenv('THRESHOLD', '0'))
        self.READ_ONLY = os.getenv('READ_ONLY', 'False').lower() == 'true'
        
        # Derived settings
        self.TAG_ROLE_NAME = self.DISCORD_NOTIFY_ROLE
        
        # Validate required settings
        self._validate_config()
    
    def _validate_config(self):
        """Validate required configuration values."""
        if not self.DISCORD_API_KEY:
            raise ValueError("DISCORD_API_KEY is required - please set it in Replit secrets")
        
        # Other validations are warnings now, not fatal errors
        if self.DISCORD_SERVER_ID == 0:
            print("Warning: DISCORD_SERVER_ID not set, using default")
        
        if self.DISCORD_FORUM_CHANNEL_ID == 0:
            print("Warning: DISCORD_FORUM_CHANNEL_ID not set, using default")
        
        if not self.HEMI_RPC:
            print("Warning: HEMI_RPC not set, using default")
        
        # Validate network name
        if self.NETWORK_NAME.lower() not in ['hemi', 'ethereum']:
            print(f"Warning: NETWORK_NAME '{self.NETWORK_NAME}' is not 'hemi' or 'ethereum'")
    
    def get_network_config(self):
        """Get network-specific configuration."""
        return {
            'name': self.NETWORK_NAME,
            'symbol': self.SYMBOL,
            'decimals': self.TOKEN_DECIMAL,
            'rpc': self.HEMI_RPC,
            'explorer': self.HEMI_EXPLORER
        }
    
    def is_voting_enabled(self):
        """Check if voting is enabled."""
        return not (self.SOLO_MODE or self.READ_ONLY)
    
    def __str__(self):
        """String representation of config (without sensitive data)."""
        return f"Config(network={self.NETWORK_NAME}, read_only={self.READ_ONLY}, solo_mode={self.SOLO_MODE})"
