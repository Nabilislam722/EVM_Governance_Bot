"""
Discord embed configuration and vote scheme utilities.
"""

import discord
from typing import Dict, List


class EmbedVoteScheme:
    """Handle Discord embed voting schemes and colors."""
    
    # Color scheme for different vote types
    COLORS = {
        'aye': 0x00FF00,      # Green
        'nay': 0xFF0000,      # Red
        'abstain': 0xFFFF00,  # Yellow
        'info': 0x0099FF,     # Blue
        'warning': 0xFF9900,  # Orange
        'error': 0xFF0000,    # Red
        'neutral': 0x808080   # Gray
    }
    
    # Emoji mappings
    EMOJIS = {
        'aye': '👍',
        'nay': '👎',
        'abstain': '⚪',
        'recuse': '⚪',
        'info': 'ℹ️',
        'warning': '⚠️',
        'error': '❌',
        'success': '✅'
    }
    
    @classmethod
    def get_vote_color(cls, vote_type: str) -> int:
        """Get color for a vote type."""
        return cls.COLORS.get(vote_type.lower(), cls.COLORS['neutral'])
    
    @classmethod
    def get_vote_emoji(cls, vote_type: str) -> str:
        """Get emoji for a vote type."""
        return cls.EMOJIS.get(vote_type.lower(), '❓')
    
    @classmethod
    def create_vote_results_embed(cls, vote_counts: Dict, title: str = "Vote Results") -> discord.Embed:
        """Create an embed showing vote results."""
        embed = discord.Embed(title=title, color=cls.COLORS['info'])
        
        aye_count = vote_counts.get('aye', 0)
        nay_count = vote_counts.get('nay', 0)
        recuse_count = vote_counts.get('recuse', 0)
        total_votes = aye_count + nay_count + recuse_count
        
        embed.add_field(
            name=f"{cls.EMOJIS['aye']} AYE",
            value=str(aye_count),
            inline=True
        )
        embed.add_field(
            name=f"{cls.EMOJIS['nay']} NAY",
            value=str(nay_count),
            inline=True
        )
        embed.add_field(
            name=f"{cls.EMOJIS['recuse']} RECUSE",
            value=str(recuse_count),
            inline=True
        )
        embed.add_field(
            name="Total Votes",
            value=str(total_votes),
            inline=False
        )
        
        # Add percentage breakdown if there are votes
        if total_votes > 0:
            aye_pct = (aye_count / total_votes) * 100
            nay_pct = (nay_count / total_votes) * 100
            recuse_pct = (recuse_count / total_votes) * 100
            
            embed.add_field(
                name="Breakdown",
                value=f"AYE: {aye_pct:.1f}%\nNAY: {nay_pct:.1f}%\nRECUSE: {recuse_pct:.1f}%",
                inline=False
            )
        
        return embed
    
    @classmethod
    def create_proposal_info_embed(cls, proposal_data: Dict) -> discord.Embed:
        """Create an embed with proposal information."""
        embed = discord.Embed(
            title=f"Referendum #{proposal_data.get('index', 'Unknown')}",
            color=cls.COLORS['info']
        )
        
        if 'title' in proposal_data:
            embed.add_field(
                name="Title",
                value=proposal_data['title'][:1024],  # Discord field limit
                inline=False
            )
        
        if 'origin' in proposal_data:
            origin = proposal_data['origin']
            if isinstance(origin, list) and origin:
                embed.add_field(
                    name="Origin",
                    value=origin[0],
                    inline=True
                )
        
        if 'created_at' in proposal_data:
            embed.add_field(
                name="Created",
                value=proposal_data['created_at'],
                inline=True
            )
        
        return embed
    
    @classmethod
    def create_voting_instructions_embed(cls, read_only: bool = False) -> discord.Embed:
        """Create an embed with voting instructions."""
        if read_only:
            embed = discord.Embed(
                title="Proposal Information",
                description="This is a read-only bot. Use the external links to view proposal details.",
                color=cls.COLORS['info']
            )
        else:
            embed = discord.Embed(
                title="How to Vote",
                color=cls.COLORS['info']
            )
            
            embed.add_field(
                name=f"{cls.EMOJIS['aye']} Vote AYE",
                value="Click if you want this proposal to pass",
                inline=False
            )
            embed.add_field(
                name=f"{cls.EMOJIS['nay']} Vote NAY",
                value="Click if you want this proposal to fail",
                inline=False
            )
            embed.add_field(
                name=f"{cls.EMOJIS['recuse']} Vote RECUSE",
                value="Click ONLY if you have a conflict of interest",
                inline=False
            )
        
        return embed
    
    @classmethod
    def create_error_embed(cls, error_message: str, title: str = "Error") -> discord.Embed:
        """Create an error embed."""
        embed = discord.Embed(
            title=f"{cls.EMOJIS['error']} {title}",
            description=error_message,
            color=cls.COLORS['error']
        )
        return embed
    
    @classmethod
    def create_success_embed(cls, message: str, title: str = "Success") -> discord.Embed:
        """Create a success embed."""
        embed = discord.Embed(
            title=f"{cls.EMOJIS['success']} {title}",
            description=message,
            color=cls.COLORS['aye']
        )
        return embed
    
    @classmethod
    def create_warning_embed(cls, message: str, title: str = "Warning") -> discord.Embed:
        """Create a warning embed."""
        embed = discord.Embed(
            title=f"{cls.EMOJIS['warning']} {title}",
            description=message,
            color=cls.COLORS['warning']
        )
        return embed
