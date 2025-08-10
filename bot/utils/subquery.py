"""
Hemi Network API utilities for connecting to Ethereum-compatible networks.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from substrateinterface.base import SubstrateInterface
try:
    from substrateinterface.exceptions import SubstrateRequestException
except ImportError:
    # Fallback for older versions of substrateinterface
    class SubstrateRequestException(Exception):
        pass


class SubstrateAPI:
    """Handle Substrate blockchain interactions."""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.substrate = None
        self._connection_lock = asyncio.Lock()
    
    async def connect(self):
        """Connect to the Substrate network."""
        async with self._connection_lock:
            if self.substrate is None:
                try:
                    self.logger.info(f"Connecting to Hemi Network")
                    self.substrate = SubstrateInterface(
                        url=self.config.SUBSTRATE_WSS,
                        ss58_format=0 if self.config.NETWORK_NAME.lower() == 'polkadot' else 2,
                        type_registry_preset=self.config.NETWORK_NAME.lower()
                    )
                    self.logger.info("Successfully connected to Hemi Network")
                except Exception as e:
                    self.logger.error(f"Failed to connect to Substrate: {e}")
                    raise
    
    async def close(self):
        """Close the Substrate connection."""
        if self.substrate:
            try:
                self.substrate.close()
                self.substrate = None
                self.logger.info("Hemi Network connection closed")
            except Exception as e:
                self.logger.error(f"Error closing Substrate connection: {e}")
    
    async def _ensure_connected(self):
        """Ensure we have an active connection."""
        if self.substrate is None:
            await self.connect()
    
    async def ongoing_referendums(self) -> Dict:
        """Get all ongoing referendums."""
        await self._ensure_connected()
        
        try:
            # Query referendum info for all referendums
            referendums = {}
            
            # Get referendum count first
            referendum_count = await self._get_referendum_count()
            
            for ref_id in range(referendum_count):
                try:
                    ref_info = await self.get_referendum_info(ref_id)
                    if ref_info and 'Ongoing' in ref_info:
                        referendums[ref_id] = ref_info
                except:
                    # Skip referendums that don't exist or are not ongoing
                    continue
            
            return referendums
            
        except Exception as e:
            self.logger.error(f"Error getting ongoing referendums: {e}")
            return {}
    
    async def ongoing_referendums_idx(self) -> List[int]:
        """Get list of ongoing referendum indices."""
        ongoing_refs = await self.ongoing_referendums()
        return list(ongoing_refs.keys())
    
    async def get_referendum_info(self, ref_id: int) -> Optional[Dict]:
        """Get information for a specific referendum."""
        await self._ensure_connected()
        
        try:
            result = self.substrate.query(
                module='Referenda',
                storage_function='ReferendumInfoFor',
                params=[ref_id]
            )
            
            if result.value:
                return result.value
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting referendum info for {ref_id}: {e}")
            return None
    
    async def _get_referendum_count(self) -> int:
        """Get the total number of referendums."""
        await self._ensure_connected()
        
        try:
            result = self.substrate.query(
                module='Referenda',
                storage_function='ReferendumCount'
            )
            return result.value if result.value else 0
        except Exception as e:
            self.logger.error(f"Error getting referendum count: {e}")
            return 100  # Fallback to check first 100
    
    async def referendum_call_data(self, index: int, gov1: bool = False, call_data: bool = False) -> tuple:
        """Get call data for a referendum."""
        await self._ensure_connected()
        
        try:
            # Get referendum info
            ref_info = await self.get_referendum_info(index)
            if not ref_info or 'Ongoing' not in ref_info:
                return None, None
            
            ongoing_info = ref_info['Ongoing']
            proposal = ongoing_info.get('proposal')
            
            if not proposal:
                return None, None
            
            # Extract call data based on proposal type
            if isinstance(proposal, dict):
                if 'Inline' in proposal:
                    call_bytes = proposal['Inline']
                    # Decode the call
                    try:
                        call = self.substrate.decode_scale(
                            type_string='Call',
                            scale_bytes=call_bytes
                        )
                        return call, None
                    except:
                        return proposal, None
                elif 'Lookup' in proposal:
                    preimage_hash = proposal['Lookup']['hash']
                    preimage_len = proposal['Lookup']['len']
                    
                    # Try to get preimage
                    preimage = await self._get_preimage(preimage_hash)
                    if preimage:
                        return preimage, preimage_hash
                    
                    return {'hash': preimage_hash, 'len': preimage_len}, preimage_hash
            
            return proposal, None
            
        except Exception as e:
            self.logger.error(f"Error getting call data for referendum {index}: {e}")
            return None, None
    
    async def _get_preimage(self, preimage_hash: str) -> Optional[Dict]:
        """Get preimage data by hash."""
        try:
            result = self.substrate.query(
                module='Preimage',
                storage_function='PreimageFor',
                params=[preimage_hash]
            )
            
            if result.value:
                # Try to decode the preimage
                try:
                    call = self.substrate.decode_scale(
                        type_string='Call',
                        scale_bytes=result.value
                    )
                    return call
                except:
                    return {'data': result.value}
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting preimage {preimage_hash}: {e}")
            return None
    
    async def get_block_timestamp(self, block_number: int) -> str:
        """Get timestamp for a specific block."""
        await self._ensure_connected()
        
        try:
            block_hash = self.substrate.get_block_hash(block_number)
            if block_hash:
                block = self.substrate.get_block(block_hash)
                if block and 'block' in block:
                    extrinsics = block['block']['extrinsics']
                    # Look for timestamp in extrinsics
                    for ext in extrinsics:
                        if hasattr(ext, 'call') and ext.call.get('call_module') == 'Timestamp':
                            timestamp = ext.call.get('call_args', {}).get('now', 0)
                            # Convert to ISO format
                            from datetime import datetime, timezone
                            dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
                            return dt.isoformat()
            
            # Fallback to current time
            from datetime import datetime, timezone
            return datetime.now(timezone.utc).isoformat()
            
        except Exception as e:
            self.logger.error(f"Error getting block timestamp: {e}")
            from datetime import datetime, timezone
            return datetime.now(timezone.utc).isoformat()
    
    async def get_block_epoch(self, block_number: int) -> int:
        """Get epoch timestamp for a block."""
        timestamp_str = await self.get_block_timestamp(block_number)
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return int(dt.timestamp())
        except:
            import time
            return int(time.time())
    
    async def get_account_balance(self, address: str) -> Dict:
        """Get account balance information."""
        await self._ensure_connected()
        
        try:
            result = self.substrate.query(
                module='System',
                storage_function='Account',
                params=[address]
            )
            
            if result.value:
                return {
                    'free': result.value['data']['free'],
                    'reserved': result.value['data']['reserved'],
                    'frozen': result.value['data']['frozen']
                }
            
            return {'free': 0, 'reserved': 0, 'frozen': 0}
            
        except Exception as e:
            self.logger.error(f"Error getting balance for {address}: {e}")
            return {'free': 0, 'reserved': 0, 'frozen': 0}
    
    async def submit_vote(self, referendum_id: int, vote: str, conviction: str, balance: int, keypair) -> Optional[str]:
        """Submit a vote for a referendum."""
        await self._ensure_connected()
        
        try:
            # Prepare vote call
            vote_call = self.substrate.compose_call(
                call_module='ConvictionVoting',
                call_function='vote',
                call_params={
                    'poll_index': referendum_id,
                    'vote': {
                        'Standard': {
                            'vote': vote,
                            'balance': balance
                        }
                    }
                }
            )
            
            # Create and submit extrinsic
            extrinsic = self.substrate.create_signed_extrinsic(
                call=vote_call,
                keypair=keypair
            )
            
            receipt = self.substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
            
            if receipt.is_success:
                self.logger.info(f"Vote submitted successfully for referendum {referendum_id}")
                return receipt.extrinsic_hash
            else:
                self.logger.error(f"Vote submission failed: {receipt.error_message}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error submitting vote: {e}")
            return None
