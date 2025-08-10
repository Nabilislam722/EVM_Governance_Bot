"""
Permission checking utilities for Discord roles and user access.
"""

import discord
import logging
from typing import Optional


class PermissionCheck:
    """Handle Discord permission checking for roles and users."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @staticmethod
    def has_role(member: discord.Member, role_name: str) -> bool:
        """Check if member has a specific role by name."""
        if not member or not role_name:
            return False
        
        return any(role.name.lower() == role_name.lower() for role in member.roles)
    
    @staticmethod
    def has_role_id(member: discord.Member, role_id: str) -> bool:
        """Check if member has a specific role by ID."""
        if not member or not role_id:
            return False
        
        try:
            role_id_int = int(role_id)
            return any(role.id == role_id_int for role in member.roles)
        except ValueError:
            return False
    
    @staticmethod
    def has_admin_role(member: discord.Member, admin_role_name: str) -> bool:
        """Check if member has admin permissions."""
        if not member:
            return False
        
        # Check for admin permissions
        if member.guild_permissions.administrator:
            return True
        
        # Check for specific admin role
        if admin_role_name:
            return PermissionCheck.has_role(member, admin_role_name)
        
        return False
    
    @staticmethod
    def has_voter_role(member: discord.Member, voter_role_name: str) -> bool:
        """Check if member can vote on proposals."""
        if not member:
            return False
        
        # If no voter role is specified, everyone can vote
        if not voter_role_name:
            return True
        
        # Check for voter role (can be name or ID)
        if voter_role_name.isdigit():
            return PermissionCheck.has_role_id(member, voter_role_name)
        else:
            return PermissionCheck.has_role(member, voter_role_name)
    
    @staticmethod
    async def can_manage_threads(member: discord.Member, channel: discord.abc.GuildChannel) -> bool:
        """Check if member can manage threads in a channel."""
        if not member or not channel:
            return False
        
        # Check permissions in the channel
        permissions = channel.permissions_for(member)
        return permissions.manage_threads or permissions.administrator
    
    @staticmethod
    async def can_create_threads(member: discord.Member, channel: discord.abc.GuildChannel) -> bool:
        """Check if member can create threads in a channel."""
        if not member or not channel:
            return False
        
        permissions = channel.permissions_for(member)
        return permissions.create_public_threads or permissions.administrator