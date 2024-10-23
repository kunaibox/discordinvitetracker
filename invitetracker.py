import discord
from discord.ext import commands
from collections import defaultdict


TOKEN = ''

intents = discord.Intents.default()
intents.members = True 
intents.guilds = True  
bot = commands.Bot(command_prefix='/', intents=intents)
@bot.event
async def on_ready():
    print(f'{bot.user.name} running')

async def fetch_all_invites(guild):
    invites = await guild.invites()
    inviter_counts = defaultdict(int)
    for invite in invites:
        if invite.inviter:
            inviter_counts[invite.inviter.id] += invite.uses
    return inviter_counts

async def get_audit_log_invites(guild):
    inviter_counts = defaultdict(int)
    async for entry in guild.audit_logs(action=discord.AuditLogAction.invite_create):
        if entry.target and isinstance(entry.target, discord.Invite):
            inviter_id = entry.user.id
            inviter_counts[inviter_id] += entry.target.uses
    return inviter_counts

@bot.tree.command(name='leaderboard', description='Display the top inviters')
async def leaderboard(interaction: discord.Interaction):
    guild = interaction.guild
    current_invites = await fetch_all_invites(guild)
    audit_log_invites = await get_audit_log_invites(guild)
    total_invites = defaultdict(int)
    for inviter_id, count in current_invites.items():
        total_invites[inviter_id] += count
    for inviter_id, count in audit_log_invites.items():
        total_invites[inviter_id] += count
    non_zero_invites = {user_id: invites for user_id, invites in total_invites.items() if invites > 0}
    if not non_zero_invites:
        await interaction.response.send_message("No invites tracked yet.")
        return
    sorted_invites = sorted(non_zero_invites.items(), key=lambda x: x[1], reverse=True)
    top_invites = sorted_invites[:10]  
    embed = discord.Embed(title="Top Inviters Leaderboard", color=discord.Color.green())
    for rank, (user_id, invites) in enumerate(top_invites, start=1):
        user = bot.get_user(user_id)
        if user:
            embed.add_field(name=f"#{rank} {user.name}", value=f"{invites} invites", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='invites', description='Check how many invites a user has made')
async def invites(interaction: discord.Interaction, user: discord.User):
    guild = interaction.guild
    current_invites = await fetch_all_invites(guild)
    audit_log_invites = await get_audit_log_invites(guild)
    total_invites_by_user = current_invites.get(user.id, 0) + audit_log_invites.get(user.id, 0)
    await interaction.response.send_message(f"{user.name} has invited {total_invites_by_user} members!")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'{bot.user.name} is now running!')

bot.run(TOKEN)
