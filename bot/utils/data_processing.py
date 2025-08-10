"""
Data processing utilities for caching, formatting, and call data processing.
"""

import json
import os
import shutil
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import discord


class CacheManager:
    """Handle data caching and backup operations."""
    
    @staticmethod
    def rotating_backup_file(source_path: str, backup_dir: str, max_backups: int = 5):
        """Create rotating backups of a file."""
        try:
            os.makedirs(backup_dir, exist_ok=True)
            
            if not os.path.exists(source_path):
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{os.path.basename(source_path)}_{timestamp}.bak"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            shutil.copy2(source_path, backup_path)
            
            # Clean up old backups
            CacheManager._cleanup_old_backups(backup_dir, max_backups)
            
            logging.info(f"Created backup: {backup_path}")
            
        except Exception as e:
            logging.error(f"Error creating backup: {e}")
    
    @staticmethod
    def _cleanup_old_backups(backup_dir: str, max_backups: int):
        """Remove old backup files, keeping only the most recent ones."""
        try:
            backup_files = []
            for filename in os.listdir(backup_dir):
                if filename.endswith('.bak'):
                    filepath = os.path.join(backup_dir, filename)
                    backup_files.append((filepath, os.path.getmtime(filepath)))
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Remove old backups
            for filepath, _ in backup_files[max_backups:]:
                os.remove(filepath)
                logging.info(f"Removed old backup: {filepath}")
                
        except Exception as e:
            logging.error(f"Error cleaning up backups: {e}")
    
    @staticmethod
    def delete_executed_keys_and_archive(json_file_path: str, active_proposals: List[int], 
                                       archive_filename: str) -> List[str]:
        """Delete executed proposals from active file and archive them."""
        try:
            # Load current vote counts
            with open(json_file_path, 'r') as f:
                vote_counts = json.load(f)
            
            # Load existing archive
            archived_votes = {}
            if os.path.exists(archive_filename):
                with open(archive_filename, 'r') as f:
                    archived_votes = json.load(f)
            
            threads_to_lock = []
            keys_to_remove = []
            
            for thread_id, vote_data in vote_counts.items():
                proposal_index = vote_data.get('index')
                if proposal_index is not None and proposal_index not in active_proposals:
                    # This proposal is no longer active
                    threads_to_lock.append(thread_id)
                    keys_to_remove.append(thread_id)
                    
                    # Archive the vote data
                    archived_votes[thread_id] = {
                        **vote_data,
                        'archived_at': datetime.now(timezone.utc).isoformat(),
                        'final_status': 'completed'
                    }
            
            # Remove from active votes
            for key in keys_to_remove:
                vote_counts.pop(key, None)
            
            # Save updated files
            with open(json_file_path, 'w') as f:
                json.dump(vote_counts, f, indent=2)
            
            with open(archive_filename, 'w') as f:
                json.dump(archived_votes, f, indent=2)
            
            if threads_to_lock:
                logging.info(f"Archived {len(threads_to_lock)} completed proposals")
            
            return threads_to_lock
            
        except Exception as e:
            logging.error(f"Error archiving proposals: {e}")
            return []


class DiscordFormatting:
    """Handle Discord message and embed formatting."""
    
    @staticmethod
    async def add_fields_to_embed(embed: discord.Embed, referendum_info: Dict) -> discord.Embed:
        """Add fields to an embed based on referendum information."""
        try:
            if 'Ongoing' in referendum_info:
                ongoing_info = referendum_info['Ongoing']
                
                # Add submission block
                if 'submitted' in ongoing_info:
                    embed.add_field(
                        name="Submitted Block",
                        value=str(ongoing_info['submitted']),
                        inline=True
                    )
                
                # Add track/origin information
                if 'origin' in ongoing_info:
                    origin = ongoing_info['origin']
                    if isinstance(origin, dict):
                        origin_name = list(origin.keys())[0] if origin else 'Unknown'
                        embed.add_field(
                            name="Track",
                            value=origin_name,
                            inline=True
                        )
                
                # Add tally information
                if 'tally' in ongoing_info:
                    tally = ongoing_info['tally']
                    if isinstance(tally, dict):
                        ayes = tally.get('ayes', 0)
                        nays = tally.get('nays', 0)
                        support = tally.get('support', 0)
                        
                        embed.add_field(
                            name="On-chain Tally",
                            value=f"Ayes: {ayes}\nNays: {nays}\nSupport: {support}",
                            inline=False
                        )
                
                # Add deciding information
                if 'deciding' in ongoing_info and ongoing_info['deciding']:
                    deciding_info = ongoing_info['deciding']
                    if isinstance(deciding_info, dict) and 'since' in deciding_info:
                        embed.add_field(
                            name="Deciding Since Block",
                            value=str(deciding_info['since']),
                            inline=True
                        )
            
            return embed
            
        except Exception as e:
            logging.error(f"Error adding fields to embed: {e}")
            return embed
    
    @staticmethod
    def format_vote_results(vote_counts: Dict, anonymous: bool = False) -> str:
        """Format vote results as a string."""
        try:
            aye_count = vote_counts.get('aye', 0)
            nay_count = vote_counts.get('nay', 0)
            recuse_count = vote_counts.get('recuse', 0)
            
            result = f"👍 AYE: {aye_count}    |    👎 NAY: {nay_count}    |    ⛔️ RECUSE: {recuse_count}"
            
            if not anonymous and 'users' in vote_counts:
                # Add user breakdown
                users = vote_counts['users']
                if users:
                    result += "\n\n**Vote Breakdown:**"
                    for vote_type in ['aye', 'nay', 'recuse']:
                        voters = [user for user, vote in users.items() if vote == vote_type]
                        if voters:
                            result += f"\n{vote_type.upper()}: {', '.join(voters)}"
            
            return result
            
        except Exception as e:
            logging.error(f"Error formatting vote results: {e}")
            return "Vote count unavailable"
    
    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to a maximum length."""
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix


class ProcessCallData:
    """Process and format blockchain call data."""
    
    def __init__(self, price: Dict = None, substrate = None):
        self.price = price or {}
        self.substrate = substrate
        self.logger = logging.getLogger(__name__)
    
    async def consolidate_call_args(self, call_data: Any) -> Dict:
        """Consolidate call arguments into a structured format."""
        try:
            if isinstance(call_data, dict):
                return call_data
            elif hasattr(call_data, '__dict__'):
                return call_data.__dict__
            else:
                return {'raw_data': str(call_data)}
                
        except Exception as e:
            self.logger.error(f"Error consolidating call args: {e}")
            return {'error': str(e)}
    
    async def find_and_collect_values(self, call_data: Dict, preimage_hash: Optional[str] = None) -> discord.Embed:
        """Create an embed with call data information."""
        try:
            embed = discord.Embed(
                title="Call Data",
                color=0x0099FF
            )
            
            if preimage_hash:
                embed.add_field(
                    name="Preimage Hash",
                    value=f"`{preimage_hash}`",
                    inline=False
                )
            
            # Process call data
            if isinstance(call_data, dict):
                # Add call module and function
                if 'call_module' in call_data:
                    embed.add_field(
                        name="Module",
                        value=call_data['call_module'],
                        inline=True
                    )
                
                if 'call_function' in call_data:
                    embed.add_field(
                        name="Function",
                        value=call_data['call_function'],
                        inline=True
                    )
                
                # Add arguments
                if 'call_args' in call_data:
                    args = call_data['call_args']
                    if isinstance(args, dict):
                        args_text = self._format_call_args(args)
                        if args_text:
                            embed.add_field(
                                name="Arguments",
                                value=args_text[:1024],  # Discord field limit
                                inline=False
                            )
            
            # Add price information if available
            if self.price and 'price' in self.price:
                price_info = f"${self.price['price']:.2f}"
                if 'change' in self.price:
                    change = self.price['change']
                    price_info += f" ({change:+.2f}%)"
                
                embed.add_field(
                    name="Current Price",
                    value=price_info,
                    inline=True
                )
            
            return embed
            
        except Exception as e:
            self.logger.error(f"Error creating call data embed: {e}")
            error_embed = discord.Embed(
                title="Call Data Error",
                description=f"Error processing call data: {e}",
                color=0xFF0000
            )
            return error_embed
    
    def _format_call_args(self, args: Dict) -> str:
        """Format call arguments for display."""
        try:
            formatted_args = []
            
            for key, value in args.items():
                if isinstance(value, (str, int, float, bool)):
                    formatted_args.append(f"**{key}**: {value}")
                elif isinstance(value, dict):
                    # Nested dictionary
                    nested = ", ".join([f"{k}: {v}" for k, v in value.items()][:3])
                    if len(value) > 3:
                        nested += "..."
                    formatted_args.append(f"**{key}**: {{{nested}}}")
                elif isinstance(value, list):
                    # List
                    if len(value) <= 3:
                        list_str = ", ".join([str(v) for v in value])
                    else:
                        list_str = ", ".join([str(v) for v in value[:3]]) + "..."
                    formatted_args.append(f"**{key}**: [{list_str}]")
                else:
                    formatted_args.append(f"**{key}**: {str(value)[:50]}")
            
            return "\n".join(formatted_args)
            
        except Exception as e:
            self.logger.error(f"Error formatting call args: {e}")
            return "Error formatting arguments"
