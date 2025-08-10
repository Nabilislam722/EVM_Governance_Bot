"""
Discord button handlers for voting and external links.
"""

import discord
import logging
from typing import Optional


class ButtonHandler(discord.ui.View):
    """Handle voting buttons in Discord."""
    
    def __init__(self, client, thread_id: str):
        super().__init__(timeout=None)
        self.client = client
        self.thread_id = thread_id
        self.logger = logging.getLogger(__name__)
    
    @discord.ui.button(label="AYE", emoji="👍", style=discord.ButtonStyle.success)
    async def vote_aye(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle AYE vote."""
        await self._handle_vote(interaction, "aye")
    
    @discord.ui.button(label="NAY", emoji="👎", style=discord.ButtonStyle.danger)
    async def vote_nay(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle NAY vote."""
        await self._handle_vote(interaction, "nay")
    
    @discord.ui.button(label="RECUSE", emoji="⚪", style=discord.ButtonStyle.secondary)
    async def vote_recuse(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle RECUSE vote."""
        await self._handle_vote(interaction, "recuse")
    
    async def _handle_vote(self, interaction: discord.Interaction, vote_type: str):
        """Handle a vote interaction."""
        try:
            # Check if user has voting permissions
            if not await self._check_voting_permissions(interaction.user, interaction.guild):
                await interaction.response.send_message(
                    "You don't have permission to vote on this proposal.",
                    ephemeral=True
                )
                return
            
            # Check if thread exists in vote counts
            if self.thread_id not in self.client.vote_counts:
                await interaction.response.send_message(
                    "This voting thread is no longer active.",
                    ephemeral=True
                )
                return
            
            vote_data = self.client.vote_counts[self.thread_id]
            user_id = str(interaction.user.id)
            
            # Remove previous vote if exists
            previous_vote = vote_data.get('users', {}).get(user_id)
            if previous_vote:
                vote_data[previous_vote] = max(0, vote_data.get(previous_vote, 0) - 1)
            
            # Add new vote
            if 'users' not in vote_data:
                vote_data['users'] = {}
            
            vote_data['users'][user_id] = vote_type
            vote_data[vote_type] = vote_data.get(vote_type, 0) + 1
            
            # Save vote counts
            await self.client.save_vote_counts()
            
            # Update vote display
            await self._update_vote_display(interaction)
            
            # Send confirmation
            await interaction.response.send_message(
                f"Your {vote_type.upper()} vote has been recorded!",
                ephemeral=True
            )
            
        except Exception as e:
            self.logger.error(f"Error handling vote: {e}")
            await interaction.response.send_message(
                "An error occurred while processing your vote.",
                ephemeral=True
            )
    
    async def _check_voting_permissions(self, user: discord.Member, guild: discord.Guild) -> bool:
        """Check if user has permission to vote."""
        # If no voter role is configured, allow anyone to vote
        if not self.client.config.DISCORD_VOTER_ROLE:
            return True
        
        # Check if user has the voter role
        voter_role = discord.utils.get(guild.roles, name=self.client.config.DISCORD_VOTER_ROLE)
        if voter_role and voter_role in user.roles:
            return True
        
        # Check if user has admin role
        admin_role = discord.utils.get(guild.roles, name=self.client.config.DISCORD_ADMIN_ROLE)
        if admin_role and admin_role in user.roles:
            return True
        
        return False
    
    async def _update_vote_display(self, interaction: discord.Interaction):
        """Update the vote count display."""
        try:
            vote_data = self.client.vote_counts[self.thread_id]
            aye_count = vote_data.get('aye', 0)
            nay_count = vote_data.get('nay', 0)
            recuse_count = vote_data.get('recuse', 0)
            
            # Find the results message to update
            channel = interaction.channel
            if channel:
                async for message in channel.history(limit=10):
                    if message.author == self.client.user and "AYE:" in message.content:
                        new_content = f"👍 AYE: {aye_count}    |    👎 NAY: {nay_count}    |    ⛔️ RECUSE: {recuse_count}"
                        await message.edit(content=new_content)
                        break
                        
        except Exception as e:
            self.logger.error(f"Error updating vote display: {e}")


class ExternalLinkButton(discord.ui.View):
    """Handle external link buttons for proposal viewing."""
    
    def __init__(self, referendum_id: int, network: str):
        super().__init__(timeout=None)
        self.referendum_id = referendum_id
        self.network = network.lower()
        
        # Add buttons for external links
        self._add_polkassembly_button()
        self._add_polkadot_js_button()
        self._add_subsquare_button()
    
    def _add_polkassembly_button(self):
        """Add Polkassembly link button."""
        if self.network == 'polkadot':
            url = f"https://polkadot.polkassembly.io/referenda/{self.referendum_id}"
        elif self.network == 'kusama':
            url = f"https://kusama.polkassembly.io/referenda/{self.referendum_id}"
        else:
            return
        
        button = discord.ui.Button(
            label="Polkassembly",
            url=url,
            style=discord.ButtonStyle.link,
            emoji="🗳️"
        )
        self.add_item(button)
    
    def _add_polkadot_js_button(self):
        """Add Polkadot.js Apps link button."""
        if self.network == 'polkadot':
            url = f"https://polkadot.js.org/apps/?rpc=wss%3A%2F%2Frpc.polkadot.io#/referenda/{self.referendum_id}"
        elif self.network == 'kusama':
            url = f"https://polkadot.js.org/apps/?rpc=wss%3A%2F%2Fkusama-rpc.polkadot.io#/referenda/{self.referendum_id}"
        else:
            return
        
        button = discord.ui.Button(
            label="Polkadot.js",
            url=url,
            style=discord.ButtonStyle.link,
            emoji="⚙️"
        )
        self.add_item(button)
    
    def _add_subsquare_button(self):
        """Add Subsquare link button."""
        if self.network == 'polkadot':
            url = f"https://polkadot.subsquare.io/referenda/{self.referendum_id}"
        elif self.network == 'kusama':
            url = f"https://kusama.subsquare.io/referenda/{self.referendum_id}"
        else:
            return
        
        button = discord.ui.Button(
            label="Subsquare",
            url=url,
            style=discord.ButtonStyle.link,
            emoji="📊"
        )
        self.add_item(button)
