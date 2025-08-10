"""
Governance monitoring for Hemi Network proposals.
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from pathlib import Path


class GovernanceMonitor:
    """Monitor governance proposals and manage proposal lifecycle."""
    
    def __init__(self, config, hemi_network):
        self.config = config
        self.hemi_network = hemi_network
        self.logger = logging.getLogger(__name__)
        
        # Data file paths
        self.cache_file = Path("../data/governance_cache.json")
        self.vote_periods_file = Path("../data/vote_periods")
        
        # Ensure data directories exist
        self.cache_file.parent.mkdir(exist_ok=True)
        self.vote_periods_file.mkdir(exist_ok=True)
    
    async def monitor_new_proposals(self, active_proposals: Dict) -> List[int]:
        """Monitor for new proposals and return list of new proposal IDs."""
        try:
            # Load existing cache
            cached_proposals = self._load_cache()
            
            new_proposals = []
            
            for proposal_id in active_proposals.keys():
                proposal_id_int = int(proposal_id)
                if proposal_id_int not in cached_proposals:
                    new_proposals.append(proposal_id_int)
                    
                    # Add to cache
                    cached_proposals[proposal_id_int] = {
                        'id': proposal_id_int,
                        'discovered_at': datetime.now(timezone.utc).isoformat(),
                        'status': 'new',
                        'title': active_proposals[proposal_id].get('title', f'Proposal #{proposal_id}')
                    }
            
            # Save updated cache
            self._save_cache(cached_proposals)
            
            if new_proposals:
                self.logger.info(f"Found {len(new_proposals)} new Hemi Network proposals")
            
            return new_proposals
            
        except Exception as e:
            self.logger.error(f"Error monitoring new proposals: {e}")
            return []
    
    async def get_asset_price_v2(self, symbol: str) -> Dict:
        """Get asset price information (placeholder for Hemi Network)."""
        try:
            # For Hemi Network, ETH price would be relevant
            # This is a placeholder - in production you'd use a price API
            return {
                'symbol': symbol,
                'price': 3200.00,  # Placeholder ETH price
                'change': 2.5,
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting asset price: {e}")
            return {}
    
    def _load_cache(self) -> Dict:
        """Load proposal cache from file."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Error loading proposal cache: {e}")
            return {}
    
    def _save_cache(self, cache_data: Dict):
        """Save proposal cache to file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving proposal cache: {e}")
    
    async def update_proposal_status(self, proposal_id: int, status: str):
        """Update the status of a proposal in cache."""
        try:
            cached_proposals = self._load_cache()
            
            if proposal_id in cached_proposals:
                cached_proposals[proposal_id]['status'] = status
                cached_proposals[proposal_id]['updated_at'] = datetime.now(timezone.utc).isoformat()
                
                self._save_cache(cached_proposals)
                self.logger.info(f"Updated proposal #{proposal_id} status to: {status}")
                
        except Exception as e:
            self.logger.error(f"Error updating proposal status: {e}")
    
    async def get_proposal_info(self, proposal_id: int) -> Optional[Dict]:
        """Get cached information about a proposal."""
        try:
            cached_proposals = self._load_cache()
            return cached_proposals.get(proposal_id)
        except Exception as e:
            self.logger.error(f"Error getting proposal info: {e}")
            return None
    
    async def cleanup_old_proposals(self, days: int = 30):
        """Clean up old proposals from cache."""
        try:
            cached_proposals = self._load_cache()
            current_time = datetime.now(timezone.utc)
            
            proposals_to_remove = []
            
            for proposal_id, proposal_info in cached_proposals.items():
                if 'discovered_at' in proposal_info:
                    discovered_time = datetime.fromisoformat(proposal_info['discovered_at'].replace('Z', '+00:00'))
                    age_days = (current_time - discovered_time).days
                    
                    if age_days > days and proposal_info.get('status') in ['completed', 'expired']:
                        proposals_to_remove.append(proposal_id)
            
            # Remove old proposals
            for proposal_id in proposals_to_remove:
                del cached_proposals[proposal_id]
            
            if proposals_to_remove:
                self._save_cache(cached_proposals)
                self.logger.info(f"Cleaned up {len(proposals_to_remove)} old proposals")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old proposals: {e}")