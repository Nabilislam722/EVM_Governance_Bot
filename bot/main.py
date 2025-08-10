import time
import json
import discord
import asyncio
import logging
import os
from datetime import datetime, timezone
from discord import app_commands, Embed
from discord.ext import tasks
from pathlib import Path
from typing import List

# Import custom modules
from utils.config import Config
from utils.logger import Logger

from utils.hemi_network import HemiNetwork
from governance_monitor import GovernanceMonitor
from utils.embed_config import EmbedVoteScheme
from utils.data_processing import CacheManager, ProcessCallData, DiscordFormatting
from utils.button_handler import ButtonHandler, ExternalLinkButton
from utils.task_handler import TaskHandler
from utils.argument_parser import ArgumentParser
from utils.permission_check import PermissionCheck

# Global variables
config = None
hemi_network = None
client = None
task_handler = None
discord_format = None
logging = None

class GovernanceBot(discord.Client):
    """Discord bot for governance monitoring and voting."""
    
    def __init__(self, config):
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(intents=intents)
        
        self.config = config
        self.vote_counts = {}
        self.onchain_votes = {}
        self.governance_cache = {}
        self.vote_periods = {}
        
        # Set up command tree
        self.tree = app_commands.CommandTree(self)
        
    async def setup_hook(self):
        """Set up the bot when it's ready."""
        await self.tree.sync()
        logging.info("Command tree synced")
    
    async def on_ready(self):
        """Called when the bot is ready."""
        logging.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logging.info("Bot is ready!")
        
        # Load initial data
        await self.load_initial_data()
        
        # Start tasks if not in read-only mode
        if not self.config.READ_ONLY:
            check_governance.start()
            if not self.config.SOLO_MODE:
                autonomous_voting.start()
            sync_embeds.start()
            recheck_proposals.start()
        else:
            logging.info("Bot is in READ_ONLY mode - monitoring only")
            check_governance.start()
    
    async def load_initial_data(self):
        """Load initial data from files."""
        # Load vote counts
        vote_counts_file = Path("../data/vote_counts.json")
        if vote_counts_file.exists():
            with open(vote_counts_file, 'r') as f:
                self.vote_counts = json.load(f)
        
        # Load onchain votes
        onchain_votes_file = Path("../data/onchain_votes.json")
        if onchain_votes_file.exists():
            with open(onchain_votes_file, 'r') as f:
                self.onchain_votes = json.load(f)
        
        # Load governance cache
        governance_cache_file = Path("../data/governance_cache.json")
        if governance_cache_file.exists():
            with open(governance_cache_file, 'r') as f:
                self.governance_cache = json.load(f)
    
    async def save_vote_counts(self):
        """Save vote counts to file."""
        vote_counts_file = Path("../data/vote_counts.json")
        vote_counts_file.parent.mkdir(exist_ok=True)
        
        # Create backup first
        CacheManager.rotating_backup_file(
            str(vote_counts_file), 
            "../data/backup"
        )
        
        with open(vote_counts_file, 'w') as f:
            json.dump(self.vote_counts, f, indent=2)
    
    async def get_thread(self, thread_id: int):
        """Get thread by ID."""
        try:
            return self.get_channel(thread_id)
        except:
            return None
    
    async def create_or_get_role(self, guild: discord.Guild, role_name: str):
        """Create or get role by name."""
        try:
            # Try to find existing role
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                return role
            
            # Create new role if it doesn't exist
            role = await guild.create_role(name=role_name, reason="Auto-created by governance bot")
            logging.info(f"Created new role: {role_name}")
            return role
            
        except Exception as e:
            logging.error(f"Error creating/getting role {role_name}: {e}")
            return None
    
    async def get_or_create_governance_tag(self, channel):
        """Get or create governance tag for forum channel."""
        try:
            if hasattr(channel, 'available_tags'):
                # Check if governance tag exists
                for tag in channel.available_tags:
                    if tag.name.lower() == 'governance':
                        return tag
                
                # Create governance tag if it doesn't exist
                tag = await channel.create_tag(
                    name="Governance",
                    emoji="🗳️",
                    moderated=False
                )
                return tag
            return None
        except Exception as e:
            logging.error(f"Error getting/creating governance tag: {e}")
            return None
    
    async def manage_discord_thread(self, channel, proposal_index, referendum_info, tag=None):
        """Create or manage Discord thread for proposal."""
        try:
            # Extract proposal title
            title = referendum_info.get('title', f'Hemi Network Proposal #{proposal_index}')
            
            # Truncate title to Discord limits
            if len(title) > self.config.DISCORD_TITLE_MAX_LENGTH:
                title = title[:self.config.DISCORD_TITLE_MAX_LENGTH - 3] + "..."
            
            # Create forum thread
            if hasattr(channel, 'create_thread'):
                # Forum channel
                thread_kwargs = {
                    'name': title,
                    'content': referendum_info.get('content', 'New Hemi Network governance proposal')
                }
                
                if tag:
                    thread_kwargs['applied_tags'] = [tag]
                
                thread = await channel.create_thread(**thread_kwargs)
                
                # Initialize vote counting for this thread
                self.vote_counts[str(thread.thread.id)] = {
                    'index': proposal_index,
                    'aye': 0,
                    'nay': 0,
                    'recuse': 0,
                    'users': {},
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                
                # Save vote counts
                await self.save_vote_counts()
                
                return thread
            
            return None
            
        except Exception as e:
            logging.error(f"Error managing Discord thread: {e}")
            return None
    
    async def lock_threads(self, thread_ids: List[str]):
        """Lock specified threads."""
        for thread_id in thread_ids:
            try:
                thread = self.get_channel(int(thread_id))
                if thread and hasattr(thread, 'edit'):
                    await thread.edit(locked=True, archived=True)
                    logging.info(f"Locked thread {thread_id}")
            except Exception as e:
                logging.error(f"Error locking thread {thread_id}: {e}")
    
    async def load_initial_data(self):
        """Load initial data files."""
        self.vote_counts = await self.load_vote_counts()
        self.onchain_votes = await self.load_onchain_votes()
        self.governance_cache = await self.load_governance_cache()
        self.vote_periods = await self.load_vote_periods(self.config.NETWORK_NAME.lower())
    
    async def load_vote_counts(self):
        """Load vote counts from JSON file."""
        try:
            with open('../data/vote_counts.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    async def save_vote_counts(self):
        """Save vote counts to JSON file."""
        with open('../data/vote_counts.json', 'w') as f:
            json.dump(self.vote_counts, f, indent=2)
    
    async def load_onchain_votes(self):
        """Load onchain votes from JSON file."""
        try:
            with open('../data/onchain_votes.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    async def load_governance_cache(self):
        """Load governance cache from JSON file."""
        try:
            with open('../data/governance_cache.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    async def load_vote_periods(self, network):
        """Load vote periods configuration."""
        try:
            with open(f'../data/vote_periods/{network}.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"Vote periods file not found for network: {network}")
            return {}
    
    async def get_or_create_governance_tag(self, available_tags, governance_origin, channel):
        """Get or create a governance tag for the forum."""
        tag_name = governance_origin[0] if governance_origin else "Unknown"
        
        # Check if tag already exists
        for tag in available_tags:
            if tag.name == tag_name:
                return tag
        
        # Create new tag if it doesn't exist
        try:
            new_tag = await channel.create_tag(name=tag_name)
            logging.info(f"Created new tag: {tag_name}")
            return new_tag
        except discord.HTTPException as e:
            logging.error(f"Failed to create tag {tag_name}: {e}")
            return None
    
    async def manage_discord_thread(self, channel, operation, title, index, content, governance_tag, message_id, client):
        """Manage Discord thread creation/editing."""
        if operation == 'create':
            try:
                # Limit content length
                if len(content) > self.config.DISCORD_BODY_MAX_LENGTH:
                    content = content[:self.config.DISCORD_BODY_MAX_LENGTH-3] + "..."
                
                thread = await channel.create_thread(
                    name=f"#{index} {title}",
                    content=content,
                    applied_tags=[governance_tag] if governance_tag else []
                )
                logging.info(f"Created thread for proposal #{index}")
                return thread
            except discord.HTTPException as e:
                logging.error(f"Failed to create thread for proposal #{index}: {e}")
                return None
    
    async def create_or_get_role(self, guild, role_name):
        """Create or get a role by name."""
        if not role_name:
            return None
        
        # Try to find existing role
        for role in guild.roles:
            if role.name == role_name:
                return role
        
        # Create new role if not found
        try:
            role = await guild.create_role(name=role_name)
            logging.info(f"Created new role: {role_name}")
            return role
        except discord.HTTPException as e:
            logging.error(f"Failed to create role {role_name}: {e}")
            return None
    
    async def lock_threads(self, thread_ids, user):
        """Lock specified threads."""
        guild = self.get_guild(self.config.DISCORD_SERVER_ID)
        for thread_id in thread_ids:
            try:
                thread = guild.get_thread(int(thread_id))
                if thread:
                    await thread.edit(locked=True)
                    logging.info(f"Locked thread {thread_id}")
            except Exception as e:
                logging.error(f"Failed to lock thread {thread_id}: {e}")
    
    def get_asset_price_v2(self, asset_id):
        """Get asset price (mock implementation)."""
        # This would typically fetch from an API
        return {"price": 0, "change": 0}
    
    async def get_voting_members(self, guild, role_name, save_records=False):
        """Get members with voting role."""
        if not role_name:
            return []
        
        guild_obj = self.get_guild(guild)
        if not guild_obj:
            return []
        
        role = discord.utils.get(guild_obj.roles, name=role_name)
        if not role:
            return []
        
        return role.members
    
    async def determine_vote_action(self, thread_id, vote_data, origin, proposal_epoch):
        """Determine what vote action to take."""
        # This is a simplified implementation
        # Real implementation would check timing and vote counts
        current_time = int(time.time())
        proposal_age_days = (current_time - proposal_epoch) / 86400
        
        # Check if it's time to vote based on origin settings
        if 'internal_vote_period' in origin:
            if proposal_age_days >= origin['internal_vote_period']:
                # Determine vote based on current counts
                aye_votes = vote_data.get('aye', 0)
                nay_votes = vote_data.get('nay', 0)
                
                if aye_votes > nay_votes:
                    return 1, 'aye'
                elif nay_votes > aye_votes:
                    return 1, 'nay'
                else:
                    return 1, 'abstain'
        
        return 0, 'none'
    
    async def disable_command(self, command_name, guild_id):
        """Disable a specific command."""
        # Implementation for disabling commands
        pass

# Initialize task handler
task_handler = TaskHandler()

@tasks.loop(hours=3)
async def check_governance():
    """Check for new governance proposals."""
    global client, hemi_network, config, discord_format, logging
    
    exception_occurred = False
    try:
        logging.info("Checking for new proposals")
        await client.wait_until_ready()
        await task_handler.evaluate_task_schedule(autonomous_voting)
        await task_handler.stop_tasks(coroutine_task=[sync_embeds, recheck_proposals])
        
        # Backup current data
        CacheManager.rotating_backup_file(
            source_path='../data/vote_counts.json', 
            backup_dir='../data/backup/'
        )

        # Use Hemi Network governance instead of OpenGov2
        governance_monitor = GovernanceMonitor(config, hemi_network)
        # Get new proposals from Hemi Network
        known_proposals = set(client.vote_counts.keys()) if hasattr(client, 'vote_counts') else set()
        new_referendums = await hemi_network.monitor_new_proposals(known_proposals)
        referendum_info_for = new_referendums

        guild = client.get_guild(config.DISCORD_SERVER_ID)

        # Archive old proposals and lock threads
        logging.info(f"Checking active proposals from {config.NETWORK_NAME}")
        active_proposals = await hemi_network.get_governance_proposals()
        threads_to_lock = CacheManager.delete_executed_keys_and_archive(
            json_file_path='../data/vote_counts.json', 
            active_proposals=active_proposals, 
            archive_filename='../data/archived_votes.json'
        )
        
        if threads_to_lock:
            try:
                await client.lock_threads(threads_to_lock, client.user)
            except Exception as e:
                logging.error(f"Failed to lock threads: {threads_to_lock}. Error: {e}")

        if not new_referendums:
            logging.info("No new proposals found")
            return

        logging.info(f"{len(new_referendums)} new proposal(s) found")
        channel = client.get_channel(config.DISCORD_FORUM_CHANNEL_ID)
        current_price = client.get_asset_price_v2(asset_id=config.NETWORK_NAME)

        # Process each new referendum
        for index, values in new_referendums.items():
            try:
                available_channel_tags = []
                if channel is not None:
                    available_channel_tags = [tag for tag in channel.available_tags]

                title = values['title'][:config.DISCORD_TITLE_MAX_LENGTH].strip() if values['title'] else f"Proposal #{index}"
                logging.info(f"Creating thread on Discord: #{index} {title}")

                # Extract governance origin safely
                try:
                    if 'origin' in values['onchain']:
                        governance_origin = [v for i, v in values['onchain']['origin'].items()]
                    else:
                        # Fallback: try to extract origin from other available data
                        governance_origin = ["Unknown Origin"]
                        if 'track' in values['onchain']:
                            governance_origin = [f"Track {values['onchain']['track']}"]
                except Exception as e:
                    logging.warning(f"Could not extract origin for #{index}: {e}")
                    governance_origin = ["Unknown Origin"]

                # Create forum tag
                governance_tag = await client.get_or_create_governance_tag(
                    available_channel_tags, governance_origin, channel
                )
                
                # Create thread
                new_proposal_thread = await client.manage_discord_thread(
                    channel=channel,
                    operation='create',
                    title=title,
                    index=index,
                    content=values['content'],
                    governance_tag=governance_tag,
                    message_id=None,
                    client=client
                )

                if not new_proposal_thread:
                    logging.error(f"Failed to create thread for #{index}")
                    continue

                # Set up voting
                if config.READ_ONLY:
                    initial_results_message = "View proposal details using the links below."
                else:
                    initial_results_message = "👍 AYE: 0    |    👎 NAY: 0    |    ⛔️ RECUSE: 0"
                
                channel_thread = await guild.fetch_channel(new_proposal_thread.message.id)
                
                # Save vote data
                client.vote_counts[str(new_proposal_thread.message.id)] = {
                    "index": index,
                    "title": values['title'][:200].strip() if values['title'] else f"Proposal #{index}",
                    "origin": governance_origin,
                    "aye": 0,
                    "nay": 0,
                    "recuse": 0,
                    "users": {},
                    "epoch": int(time.time())
                }
                
                await client.save_vote_counts()
                
                # Add external links
                external_links = ExternalLinkButton(index, config.NETWORK_NAME)
                results_message = await channel_thread.send(
                    content=initial_results_message, 
                    view=external_links
                )

                # Add voting buttons if not read-only
                if not config.READ_ONLY:
                    voting_buttons = ButtonHandler(client, new_proposal_thread.message.id)
                    await new_proposal_thread.message.edit(view=voting_buttons)

                # Pin messages
                await new_proposal_thread.message.pin()
                await results_message.pin()

                # Clean up pin notifications
                async for message in channel_thread.history(limit=5):
                    if message.type == discord.MessageType.pins_add:
                        await message.delete()

                # Add role notification
                role = await client.create_or_get_role(guild, config.TAG_ROLE_NAME)
                if role:
                    if config.READ_ONLY:
                        instructions = await channel_thread.send(
                            content=f"||<@&{role.id}>||\n**ANNOUNCEMENT:**\nA new proposal has been created."
                        )
                    else:
                        instructions = await channel_thread.send(
                            content=f"||<@&{role.id}>||\n**INSTRUCTIONS:**\n"
                                   f"- Vote **AYE** if you want to see this proposal pass\n"
                                   f"- Vote **NAY** if you want to see this proposal fail\n"
                                   f"- Vote **RECUSE** if you have a conflict of interest"
                        )

                # Add embed with proposal info
                general_info_embed = Embed(
                    title=f"Hemi Network Proposal #{index}",
                    description=values.get('content', 'Proposal details'),
                    color=0x00FF00
                )
                general_info = await discord_format.add_fields_to_embed(
                    general_info_embed, referendum_info_for[index]
                )
                await new_proposal_thread.message.edit(embed=general_info)

                # Add call data
                # For Hemi Network, get proposal details from our custom governance
                proposal_details = await hemi_network.get_proposal_details(str(index))
                call_data = proposal_details.get('description', 'No details available') if proposal_details else 'No details available'
                preimagehash = proposal_details.get('onchain', {}).get('transaction_hash', '0x') if proposal_details else '0x'
                # Process call data for display
                process_call_data = ProcessCallData()
                call_data = await process_call_data.consolidate_call_args(call_data)
                embedded_call_data = await process_call_data.find_and_collect_values(
                    call_data, preimagehash
                )

                # Update with call data embed
                symbol_path = f'../assets/{config.NETWORK_NAME}/{config.NETWORK_NAME}.png'
                if os.path.exists(symbol_path):
                    await instructions.edit(
                        embed=embedded_call_data, 
                        attachments=[discord.File(symbol_path, filename='symbol.png')]
                    )
                else:
                    await instructions.edit(embed=embedded_call_data)

            except Exception as error:
                logging.exception(f"Error processing proposal #{index}: {error}")

    except Exception as error:
        exception_occurred = True
        logging.exception(f"Error in check_governance: {error}")
        await hemi_network.close()
        await asyncio.sleep(30)
        check_governance.restart()
    finally:
        if not exception_occurred:
            await hemi_network.close()
            if config.SOLO_MODE is False and not config.READ_ONLY:
                await task_handler.start_tasks(coroutine_task=[autonomous_voting, sync_embeds, recheck_proposals])
            elif config.SOLO_MODE is True:
                logging.info("Solo mode enabled - automatic voting disabled")
                await task_handler.start_tasks(coroutine_task=[sync_embeds, recheck_proposals])

@tasks.loop(hours=12)
async def autonomous_voting():
    """Handle autonomous voting based on internal results."""
    global client, hemi_network, config, logging
    
    if config.SOLO_MODE or config.READ_ONLY:
        return
    
    exception_occurred = False
    try:
        logging.info("Running autonomous voting task")
        await client.wait_until_ready()
        await task_handler.stop_tasks(coroutine_task=[sync_embeds, recheck_proposals])
        
        # Implementation would go here for actual voting
        # This is a placeholder for the voting logic
        
    except Exception as error:
        exception_occurred = True
        logging.exception(f"Error in autonomous_voting: {error}")
    finally:
        if not exception_occurred:
            await task_handler.start_tasks(coroutine_task=[sync_embeds, recheck_proposals])

@tasks.loop(minutes=30)
async def sync_embeds():
    """Sync embed information."""
    try:
        logging.info("Syncing embeds")
        # Implementation for syncing embeds
    except Exception as error:
        logging.exception(f"Error in sync_embeds: {error}")

@tasks.loop(hours=6)
async def recheck_proposals():
    """Recheck proposal status."""
    try:
        logging.info("Rechecking proposals")
        # Implementation for rechecking proposals
    except Exception as error:
        logging.exception(f"Error in recheck_proposals: {error}")

async def main():
    """Main function to start the bot."""
    global config, hemi_network, client, task_handler, discord_format, logging
    
    # Initialize configuration
    config = Config()
    
    # Initialize logging
    logger = Logger()
    logging = logger.setup_logging()
    
    # Initialize Hemi Network connection
    hemi_network = HemiNetwork(config.get_network_config())
    
    # Initialize Discord formatting
    discord_format = DiscordFormatting()
    
    # Initialize task handler
    task_handler = TaskHandler()
    
    # Initialize bot
    client = GovernanceBot(config)
    
    # Add slash commands
    @client.tree.command(name="thread", description="Manage proposal threads")
    async def thread_command(interaction: discord.Interaction, action: str):
        """Thread management command."""
        try:
            await interaction.response.send_message(f"Thread {action} executed", ephemeral=True)
        except Exception as e:
            logging.error(f"Error in thread command: {e}")
            await interaction.response.send_message("Command failed", ephemeral=True)
    
    @client.tree.command(name="vote", description="Manual voting command")
    async def vote_command(interaction: discord.Interaction, proposal: int, vote_type: str):
        """Manual vote command."""
        try:
            await interaction.response.send_message(f"Vote {vote_type} recorded for proposal {proposal}", ephemeral=True)
        except Exception as e:
            logging.error(f"Error in vote command: {e}")
            await interaction.response.send_message("Command failed", ephemeral=True)
    
    # Start the bot
    try:
        await client.start(config.DISCORD_API_KEY)
    except discord.LoginFailure:
        logging.error("Invalid Discord API key")
    except Exception as e:
        logging.exception(f"Error starting bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
