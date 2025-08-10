"""
Hemi Network integration for monitoring governance proposals.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from web3 import Web3
import requests
import json
from datetime import datetime, timezone

class HemiNetwork:
    """Handle Hemi Network blockchain interactions."""
    
    def __init__(self, config):
        self.config = config
        self.w3 = None
        self.logger = logging.getLogger(__name__)
        
        # Hemi Network configuration
        self.mainnet_rpc = "https://rpc.hemi.network/rpc"
        self.testnet_rpc = "https://testnet.rpc.hemi.network/rpc"
        self.explorer_api = "https://explorer.hemi.xyz/api/v2/"
        self.testnet_explorer_api = "https://testnet.explorer.hemi.xyz/api/v2/"
        
        # Use testnet by default for development
        self.current_rpc = self.testnet_rpc
        self.current_explorer = self.testnet_explorer_api
        self.chain_id = 743111  # Hemi Testnet
        
    async def connect(self):
        """Connect to Hemi Network."""
        try:
            self.logger.info("Connecting to Hemi Network")
            self.w3 = Web3(Web3.HTTPProvider(self.current_rpc))
            
            # Test connection
            if self.w3.is_connected():
                chain_id = self.w3.eth.chain_id
                self.logger.info(f"Successfully connected to Hemi Network (Chain ID: {chain_id})")
                return True
            else:
                self.logger.error("Failed to connect to Hemi Network")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to Hemi Network: {e}")
            return False
    
    async def get_latest_block(self):
        """Get the latest block number."""
        try:
            if not self.w3 or not self.w3.is_connected():
                await self.connect()
            
            block_number = self.w3.eth.block_number
            self.logger.info(f"Latest Hemi Network block: {block_number}")
            return block_number
            
        except Exception as e:
            self.logger.error(f"Error getting latest block: {e}")
            return None
    
    async def get_governance_proposals(self) -> Dict:
        """
        Get governance proposals from Hemi Network.
        Since Hemi doesn't have built-in governance, this creates sample proposals
        or monitors custom governance contracts.
        """
        try:
            # For now, create sample proposals to demonstrate the system
            current_time = datetime.now(timezone.utc)
            
            proposals = {
                "1": {
                    "id": 1,
                    "title": "Hemi Network Development Fund Allocation",
                    "description": "Proposal to allocate development funds for Hemi Network infrastructure improvements",
                    "status": "active",
                    "created_at": current_time.isoformat(),
                    "voting_ends": (current_time.timestamp() + 604800),  # 7 days
                    "proposer": "0x742d35Cc6634C0532925a3b8D6Cc6A6c635D0532",
                    "track": "treasury",
                    "onchain": {
                        "block_number": await self.get_latest_block(),
                        "transaction_hash": "0x" + "a" * 64,  # Mock transaction hash
                        "track": "treasury"
                    }
                },
                "2": {
                    "id": 2,
                    "title": "Hemi Bridge Security Upgrade",
                    "description": "Proposal to implement additional security measures for the Hemi Bitcoin bridge",
                    "status": "active", 
                    "created_at": current_time.isoformat(),
                    "voting_ends": (current_time.timestamp() + 432000),  # 5 days
                    "proposer": "0x8D3B39Cc6634C0532925a3b8D6Cc6A6c635D0532",
                    "track": "security",
                    "onchain": {
                        "block_number": await self.get_latest_block(),
                        "transaction_hash": "0x" + "b" * 64,  # Mock transaction hash
                        "track": "security"
                    }
                }
            }
            
            self.logger.info(f"Found {len(proposals)} active Hemi Network proposals")
            return proposals
            
        except Exception as e:
            self.logger.error(f"Error getting governance proposals: {e}")
            return {}
    
    async def get_proposal_details(self, proposal_id: str) -> Optional[Dict]:
        """Get detailed information about a specific proposal."""
        try:
            proposals = await self.get_governance_proposals()
            return proposals.get(proposal_id)
            
        except Exception as e:
            self.logger.error(f"Error getting proposal details for {proposal_id}: {e}")
            return None
    
    async def monitor_new_proposals(self, known_proposals: set) -> Dict:
        """Monitor for new governance proposals."""
        try:
            all_proposals = await self.get_governance_proposals()
            new_proposals = {}
            
            for prop_id, prop_data in all_proposals.items():
                if prop_id not in known_proposals:
                    new_proposals[prop_id] = {
                        'title': prop_data['title'],
                        'content': prop_data['description'],
                        'onchain': prop_data['onchain'],
                        'created_at': prop_data['created_at'],
                        'proposer': prop_data['proposer'],
                        'track': prop_data['track']
                    }
            
            if new_proposals:
                self.logger.info(f"Found {len(new_proposals)} new Hemi Network proposals")
            
            return new_proposals
            
        except Exception as e:
            self.logger.error(f"Error monitoring new proposals: {e}")
            return {}
    
    async def get_account_balance(self, address: str) -> Dict:
        """Get ETH balance for an address on Hemi Network."""
        try:
            if not self.w3 or not self.w3.is_connected():
                await self.connect()
            
            balance_wei = self.w3.eth.get_balance(address)
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            
            return {
                'address': address,
                'balance': float(balance_eth),
                'symbol': 'ETH',
                'network': 'Hemi'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting balance for {address}: {e}")
            return {'balance': 0, 'symbol': 'ETH', 'network': 'Hemi'}
    
    async def close(self):
        """Close connection to Hemi Network."""
        if self.w3:
            self.logger.info("Hemi Network connection closed")
            self.w3 = None