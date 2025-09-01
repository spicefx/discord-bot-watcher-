"""
Discord Security Bot - Main Bot Logic
Created by: spice.efx
Version: 2.0
Description: Advanced Discord security bot with PostgreSQL logging
Handles bot detection, approval system, and comprehensive moderation actions
"""

import asyncio
import logging
import discord
from discord.ext import commands
from datetime import datetime, timezone
from typing import Dict, Set
from config import BotConfig
from utils import is_moderator, send_safe_dm, format_countdown
from database import db

class SecurityBot(commands.Bot):
    def __init__(self):
        # Configure bot intents
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        
        super().__init__(
            command_prefix=BotConfig.COMMAND_PREFIX,
            intents=intents,
            help_command=None
        )
        
        self.logger = logging.getLogger(__name__)
        self.pending_bots: Dict[int, Dict] = {}  # bot_id -> {guild_id, task, moderators_notified}
        self.approved_bots: Set[int] = set()  # Set of approved bot IDs
        
    async def on_ready(self):
        """Called when the bot is ready"""
        self.logger.info(f'{self.user} has connected to Discord!')
        self.logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Initialize database
        await db.initialize()
        
        # Set bot status with creator attribution
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="for new bots | by spice.efx"
        )
        await self.change_presence(activity=activity)
        
        # Log startup message with branding
        self.logger.info("Discord Security Bot v2.0 by spice.efx - Fully operational!")
        
    async def on_member_join(self, member):
        """Handle new member joins - detect and process bot additions"""
        if not member.bot:
            return  # Not a bot, ignore
            
        guild = member.guild
        self.logger.info(f"Bot detected joining {guild.name}: {member.name} (ID: {member.id})")
        
        # Check if bot is already approved
        if member.id in self.approved_bots:
            self.logger.info(f"Bot {member.name} (ID: {member.id}) is pre-approved")
            return
            
        # Log bot detection
        await self.log_bot_detection(member)
        
        # Start approval process
        await self.process_bot_addition(member)
        
    async def process_bot_addition(self, bot_member):
        """Process a new bot addition with approval system"""
        guild = bot_member.guild
        bot_id = bot_member.id
        
        # Check if bot is already pending
        if bot_id in self.pending_bots:
            self.logger.warning(f"Bot {bot_member.name} is already pending approval")
            return
            
        # Find moderators to notify
        moderators = await self.get_moderators(guild)
        if not moderators:
            self.logger.warning(f"No moderators found in {guild.name} - auto-rejecting bot")
            await self.reject_bot(bot_member, "No moderators available")
            return
            
        # Store pending bot info
        self.pending_bots[bot_id] = {
            'guild_id': guild.id,
            'member': bot_member,
            'start_time': datetime.now(timezone.utc),
            'moderators_notified': set()
        }
        
        # Notify moderators
        await self.notify_moderators(bot_member, moderators)
        
        # Start countdown timer
        countdown_task = asyncio.create_task(self.countdown_timer(bot_member))
        self.pending_bots[bot_id]['task'] = countdown_task

    async def log_bot_detection(self, bot_member):
        """Log bot detection to database"""
        try:
            # Get who invited the bot from audit logs
            invited_by_id = None
            invited_by_name = "Unknown"
            
            try:
                async for entry in bot_member.guild.audit_logs(action=discord.AuditLogAction.bot_add, limit=10):
                    if entry.target and entry.target.id == bot_member.id:
                        invited_by_id = entry.user.id
                        invited_by_name = entry.user.name
                        break
            except discord.Forbidden:
                pass  # No audit log access
            
            # Calculate account age
            account_age = (datetime.now(timezone.utc) - bot_member.created_at).days
            
            action_data = {
                'action_type': 'detected',
                'bot_id': bot_member.id,
                'bot_name': bot_member.name,
                'guild_id': bot_member.guild.id,
                'guild_name': bot_member.guild.name,
                'moderator_id': None,
                'moderator_name': None,
                'invited_by_id': invited_by_id,
                'invited_by_name': invited_by_name,
                'reason': 'Bot detected joining server',
                'bot_permissions': bot_member.guild_permissions.value,
                'account_age_days': account_age
            }
            
            await db.log_bot_action(action_data)
        except Exception as e:
            self.logger.error(f"Failed to log bot detection: {e}")

    async def log_bot_action(self, bot_member, action_type, moderator=None, reason=None):
        """Log bot action to database"""
        try:
            # Get who invited the bot from audit logs
            invited_by_id = None
            invited_by_name = "Unknown"
            
            try:
                async for entry in bot_member.guild.audit_logs(action=discord.AuditLogAction.bot_add, limit=10):
                    if entry.target and entry.target.id == bot_member.id:
                        invited_by_id = entry.user.id
                        invited_by_name = entry.user.name
                        break
            except discord.Forbidden:
                pass  # No audit log access
            
            # Calculate account age
            account_age = (datetime.now(timezone.utc) - bot_member.created_at).days
            
            action_data = {
                'action_type': action_type,
                'bot_id': bot_member.id,
                'bot_name': bot_member.name,
                'guild_id': bot_member.guild.id,
                'guild_name': bot_member.guild.name,
                'moderator_id': moderator.id if moderator else None,
                'moderator_name': moderator.name if moderator else None,
                'invited_by_id': invited_by_id,
                'invited_by_name': invited_by_name,
                'reason': reason or f'Bot {action_type}',
                'bot_permissions': bot_member.guild_permissions.value,
                'account_age_days': account_age
            }
            
            await db.log_bot_action(action_data)
        except Exception as e:
            self.logger.error(f"Failed to log bot action: {e}")
        
    async def get_moderators(self, guild):
        """Get list of moderators in the guild"""
        moderators = []
        target_role_id = BotConfig.TARGET_ROLE_ID
        
        # Find the specific role
        target_role = guild.get_role(target_role_id)
        if not target_role:
            self.logger.warning(f"Target role ID {target_role_id} not found in guild {guild.name}")
            return moderators
        
        # Get members with the specific role
        for member in target_role.members:
            if not member.bot:
                moderators.append(member)
                
        return moderators
        
    async def notify_moderators(self, bot_member, moderators):
        """Send DM notifications to moderators about pending bot"""
        guild = bot_member.guild
        bot_id = bot_member.id
        
        embed = discord.Embed(
            title="🚨 New Bot Detected",
            description=f"A new bot has joined **{guild.name}** and requires approval.",
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name="Bot Information",
            value=f"**Name:** {bot_member.name}\n**ID:** {bot_member.id}\n**Account Created:** {bot_member.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            inline=False
        )
        
        embed.add_field(
            name="Actions",
            value=f"React with ✅ to approve or ❌ to reject\n⏰ **Auto-reject in {BotConfig.APPROVAL_TIMEOUT} seconds**",
            inline=False
        )
        
        embed.set_thumbnail(url=bot_member.display_avatar.url)
        embed.set_footer(text=f"Guild: {guild.name}")
        
        # Send DMs to moderators
        for moderator in moderators:
            try:
                dm_message = await send_safe_dm(moderator, embed=embed)
                if dm_message:
                    # Add reaction buttons
                    await dm_message.add_reaction("✅")
                    await dm_message.add_reaction("❌")
                    
                    self.pending_bots[bot_id]['moderators_notified'].add(moderator.id)
                    self.logger.info(f"Notified moderator {moderator.name} about bot {bot_member.name}")
                    
            except Exception as e:
                self.logger.error(f"Failed to notify moderator {moderator.name}: {e}")
                
        # Log the notification
        notified_count = len(self.pending_bots[bot_id]['moderators_notified'])
        self.logger.info(f"Notified {notified_count}/{len(moderators)} moderators about bot {bot_member.name}")
        
    async def countdown_timer(self, bot_member):
        """Handle countdown timer for bot approval"""
        bot_id = bot_member.id
        
        try:
            # Wait for timeout period
            await asyncio.sleep(BotConfig.APPROVAL_TIMEOUT)
            
            # Check if bot is still pending
            if bot_id in self.pending_bots:
                await self.reject_bot(bot_member, "Timeout - no approval received")
                
        except asyncio.CancelledError:
            # Timer was cancelled (approval/rejection received)
            pass
        except Exception as e:
            self.logger.error(f"Error in countdown timer for bot {bot_member.name}: {e}")
            
    async def approve_bot(self, bot_member, approved_by):
        """Approve a bot and add to approved list"""
        bot_id = bot_member.id
        guild = bot_member.guild
        
        if bot_id not in self.pending_bots:
            return False
            
        # Cancel countdown timer
        task = self.pending_bots[bot_id].get('task')
        if task and not task.done():
            task.cancel()
            
        # Remove from pending
        del self.pending_bots[bot_id]
        
        # Add to approved list
        self.approved_bots.add(bot_id)
        
        # Log approval
        self.logger.info(f"Bot {bot_member.name} (ID: {bot_id}) approved by {approved_by.name} in {guild.name}")
        await self.log_bot_action(bot_member, 'approved', approved_by, "Approved by moderator")
        
        # Send confirmation DM
        embed = discord.Embed(
            title="✅ Bot Approved",
            description=f"Bot **{bot_member.name}** has been approved in **{guild.name}**",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )
        
        await send_safe_dm(approved_by, embed=embed)
        return True
        
    async def reject_bot(self, bot_member, reason="Rejected by moderator"):
        """Reject and kick a bot"""
        bot_id = bot_member.id
        guild = bot_member.guild
        
        if bot_id in self.pending_bots:
            # Cancel countdown timer
            task = self.pending_bots[bot_id].get('task')
            if task and not task.done():
                task.cancel()
                
            # Remove from pending
            del self.pending_bots[bot_id]
            
        try:
            # Kick the bot
            await bot_member.kick(reason=f"Security Bot: {reason}")
            self.logger.info(f"Bot {bot_member.name} (ID: {bot_id}) kicked from {guild.name} - {reason}")
            
            # Log the rejection/kick
            action_type = 'auto_kicked' if 'Timeout' in reason else 'rejected'
            moderator = None
            if 'Rejected by' in reason:
                moderator_name = reason.split('Rejected by ')[1]
                # Try to find the moderator user object
                for member in guild.members:
                    if member.name == moderator_name:
                        moderator = member
                        break
            await self.log_bot_action(bot_member, action_type, moderator, reason)
            
        except discord.Forbidden:
            self.logger.error(f"Permission denied: Cannot kick bot {bot_member.name}. Bot needs 'Kick Members' permission.")
            
            # Try to notify moderators about the permission issue
            embed = discord.Embed(
                title="⚠️ Permission Error",
                description=f"Cannot kick bot **{bot_member.name}** - Security bot needs 'Kick Members' permission!",
                color=discord.Color.red()
            )
            
            # Find moderators to notify about permission issue
            moderators = await self.get_moderators(guild)
            for moderator in moderators:
                try:
                    await send_safe_dm(moderator, embed=embed)
                except:
                    pass
                    
        except discord.NotFound:
            self.logger.warning(f"Bot {bot_member.name} not found (may have already left)")
        except Exception as e:
            self.logger.error(f"Error kicking bot {bot_member.name}: {e}")
            
    async def on_reaction_add(self, reaction, user):
        """Handle moderator reactions to approval messages"""
        if user.bot:
            return
            
        # Check if reaction is on a DM
        if not isinstance(reaction.message.channel, discord.DMChannel):
            return
            
        # Check if user has the target role in any guild where bot is present
        has_target_role = False
        for guild in self.guilds:
            member = guild.get_member(user.id)
            if member and is_moderator(member):
                has_target_role = True
                break
                
        if not has_target_role:
            return
            
        # Check if this is a response to a bot approval request
        if reaction.message.embeds:
            embed = reaction.message.embeds[0]
            if "New Bot Detected" in embed.title:
                # Extract bot ID from embed
                bot_id = None
                for field in embed.fields:
                    if "Bot Information" in field.name and "ID:" in field.value:
                        try:
                            lines = field.value.split('\n')
                            for line in lines:
                                if line.startswith("**ID:**"):
                                    bot_id = int(line.split('**ID:** ')[1])
                                    break
                        except (ValueError, IndexError):
                            continue
                            
                if bot_id and bot_id in self.pending_bots:
                    pending_info = self.pending_bots[bot_id]
                    bot_member = pending_info['member']
                    
                    # Check if user can moderate this bot's guild
                    guild = self.get_guild(pending_info['guild_id'])
                    if guild:
                        member = guild.get_member(user.id)
                        if member and is_moderator(member):
                            if str(reaction.emoji) == "✅":
                                await self.approve_bot(bot_member, user)
                            elif str(reaction.emoji) == "❌":
                                await self.reject_bot(bot_member, f"Rejected by {user.name}")

# Add the commands as separate functions that can be properly registered
async def bot_status_command(bot, ctx):
    """Show current bot approval status"""
    if not is_moderator(ctx.author):
        await ctx.send("❌ You don't have permission to use this command.")
        return
        
    embed = discord.Embed(
        title="🤖 Bot Security Status",
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc)
    )
    
    pending_count = len(bot.pending_bots)
    approved_count = len(bot.approved_bots)
    
    embed.add_field(
        name="Statistics",
        value=f"**Pending Approvals:** {pending_count}\n**Approved Bots:** {approved_count}",
        inline=False
    )
    
    if bot.pending_bots:
        pending_info = []
        for bot_id, info in bot.pending_bots.items():
            bot_member = info['member']
            elapsed = (datetime.now(timezone.utc) - info['start_time']).seconds
            remaining = max(0, BotConfig.APPROVAL_TIMEOUT - elapsed)
            pending_info.append(f"• {bot_member.name} (ID: {bot_id}) - {remaining}s remaining")
            
        embed.add_field(
            name="Pending Bots",
            value='\n'.join(pending_info[:5]),  # Limit to 5 entries
            inline=False
        )
        
    await ctx.send(embed=embed)

async def manual_approve_command(bot, ctx, bot_id: int):
    """Manually approve a bot by ID"""
    if not is_moderator(ctx.author):
        await ctx.send("❌ You don't have permission to use this command.")
        return
        
    if bot_id in bot.pending_bots:
        bot_member = bot.pending_bots[bot_id]['member']
        if await bot.approve_bot(bot_member, ctx.author):
            await ctx.send(f"✅ Bot {bot_member.name} has been approved.")
        else:
            await ctx.send("❌ Failed to approve bot.")
    else:
        await ctx.send("❌ Bot not found in pending list.")

async def manual_reject_command(bot, ctx, bot_id: int):
    """Manually reject a bot by ID"""
    if not is_moderator(ctx.author):
        await ctx.send("❌ You don't have permission to use this command.")
        return
        
    if bot_id in bot.pending_bots:
        bot_member = bot.pending_bots[bot_id]['member']
        await bot.reject_bot(bot_member, f"Manually rejected by {ctx.author.name}")
        await ctx.send(f"❌ Bot {bot_member.name} has been rejected and kicked.")
    else:
        await ctx.send("❌ Bot not found in pending list.")

async def view_logs_command(bot, ctx, limit: int = 20):
    """View recent bot addition/rejection logs"""
    if not is_moderator(ctx.author):
        await ctx.send("❌ You don't have permission to use this command.")
        return
        
    if limit > 50:
        limit = 50  # Limit to prevent spam
        
    try:
        # Get recent logs
        logs = await db.get_recent_logs(ctx.guild.id, limit)
        stats = await db.get_stats(ctx.guild.id)
        
        if not logs:
            embed = discord.Embed(
                title="📋 Bot Action Logs",
                description="No bot actions recorded yet.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        
        # Create main embed with stats and branding
        embed = discord.Embed(
            title="📋 Bot Action Logs",
            description="*Discord Security Bot v2.0 by spice.efx*",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Add statistics
        embed.add_field(
            name="📊 Overall Statistics",
            value=f"**Total Actions:** {stats.get('total_actions', 0)}\n"
                  f"**Approved:** {stats.get('approved_count', 0)}\n"
                  f"**Rejected:** {stats.get('rejected_count', 0)}\n"
                  f"**Auto-kicked:** {stats.get('auto_kicked_count', 0)}",
            inline=True
        )
        
        embed.add_field(
            name="📈 Last 24 Hours",
            value=f"**Total:** {stats.get('recent_total', 0)}\n"
                  f"**Approved:** {stats.get('recent_approved', 0)}\n"
                  f"**Rejected:** {stats.get('recent_rejected', 0)}\n"
                  f"**Auto-kicked:** {stats.get('recent_auto_kicked', 0)}",
            inline=True
        )
        
        # Add recent actions
        log_entries = []
        for log in logs[:10]:  # Show last 10 entries in embed
            action_emoji = {
                'detected': '🔍',
                'approved': '✅',
                'rejected': '❌',
                'auto_kicked': '⏰'
            }.get(log['action_type'], '❓')
            
            timestamp = log['timestamp'].strftime('%m/%d %H:%M')
            moderator = log['moderator_name'] or 'System'
            invited_by = log['invited_by_name'] or 'Unknown'
            
            entry = f"{action_emoji} **{log['bot_name']}** ({log['action_type']})\n"
            entry += f"   └ {timestamp} by {moderator}"
            if log['action_type'] == 'detected':
                entry += f" | Invited by: {invited_by}"
            
            log_entries.append(entry)
        
        if log_entries:
            embed.add_field(
                name=f"🕒 Recent Actions (showing {len(log_entries)} of {len(logs)})",
                value='\n'.join(log_entries),
                inline=False
            )
        
        embed.set_footer(text=f"Use !logs {limit} to see more entries (max 50)")
        await ctx.send(embed=embed)
        
    except Exception as e:
        bot.logger.error(f"Error retrieving logs: {e}")
        await ctx.send("❌ Error retrieving logs. Please try again later.")

async def bot_history_command(bot, ctx, bot_id: int):
    """View action history for a specific bot"""
    if not is_moderator(ctx.author):
        await ctx.send("❌ You don't have permission to use this command.")
        return
        
    try:
        history = await db.get_bot_history(bot_id)
        
        if not history:
            await ctx.send(f"❌ No history found for bot ID: {bot_id}")
            return
            
        bot_name = history[0]['bot_name']
        
        embed = discord.Embed(
            title=f"🤖 Bot History: {bot_name}",
            description=f"**Bot ID:** {bot_id}",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Add bot details from most recent entry
        recent = history[0]
        embed.add_field(
            name="Bot Information",
            value=f"**Account Age:** {recent['account_age_days']} days\n"
                  f"**Invited By:** {recent['invited_by_name'] or 'Unknown'}\n"
                  f"**Permissions Value:** {recent['bot_permissions'] or 'Unknown'}",
            inline=False
        )
        
        # Add history entries
        history_entries = []
        for entry in history:
            action_emoji = {
                'detected': '🔍',
                'approved': '✅',
                'rejected': '❌',
                'auto_kicked': '⏰'
            }.get(entry['action_type'], '❓')
            
            timestamp = entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC')
            moderator = entry['moderator_name'] or 'System'
            
            history_entry = f"{action_emoji} **{entry['action_type'].title()}**\n"
            history_entry += f"   └ {timestamp} by {moderator}\n"
            if entry['reason']:
                history_entry += f"   └ Reason: {entry['reason']}"
            
            history_entries.append(history_entry)
        
        embed.add_field(
            name=f"📜 Action History ({len(history_entries)} entries)",
            value='\n\n'.join(history_entries[:5]),  # Show last 5 entries
            inline=False
        )
        
        if len(history_entries) > 5:
            embed.set_footer(text=f"Showing 5 most recent of {len(history_entries)} total entries")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        bot.logger.error(f"Error retrieving bot history: {e}")
        await ctx.send("❌ Error retrieving bot history. Please try again later.")

# Register commands properly
def setup_commands(bot):
    """Setup bot commands"""
    
    @bot.command(name='botstatus')
    async def botstatus(ctx):
        await bot_status_command(bot, ctx)
    
    @bot.command(name='approve')
    async def approve(ctx, bot_id: int):
        await manual_approve_command(bot, ctx, bot_id)
    
    @bot.command(name='reject')
    async def reject(ctx, bot_id: int):
        await manual_reject_command(bot, ctx, bot_id)
    
    @bot.command(name='logs')
    async def logs(ctx, limit: int = 20):
        await view_logs_command(bot, ctx, limit)
    
    @bot.command(name='bothistory')
    async def bothistory(ctx, bot_id: int):
        await bot_history_command(bot, ctx, bot_id)