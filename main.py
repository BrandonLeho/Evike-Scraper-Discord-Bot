import discord
from discord.ext import commands

bot = commands.Bot(command_prefix = ".", intents = discord.Intents.all())

@bot.event
async def on_ready():
    print("Bot ready!")
    
@bot.command()
async def JohnEvike(ctx):
    await ctx.send(f"{ctx.author.mention} I'm John Evike")

@bot.command()
async def sendembed(ctx):
    embeded_msg = discord.Embed(title="Title of Embed", description="Desription od Embed", color=discord.Color.random())
    embeded_msg.set_author(name="Author Text", icon_url=ctx.author.avatar)
    embeded_msg.set_thumbnail(url=ctx.author.avatar)
    embeded_msg.add_field(name="Name of Field", value="Value of Field", inline=False)
    embeded_msg.set_image(url=ctx.guild.icon)
    embeded_msg.set_footer(text="Footer Text", icon_url=ctx.author.avatar)
    await ctx.send(embed=embeded_msg)
    
@bot.command()
async def ping(ctx):
    ping_embed = discord.Embed(title="Ping", description="Latency in ms", color=discord.Color.yellow())
    ping_embed.add_field(name=f"{bot.user.name}'s Latency (ms): ", value=f"{round(bot.latency * 1000)}ms.", inline=False)
    ping_embed.set_footer(text=f"Requested by {ctx.author.name}.", icon_url=ctx.author.avatar)
    await ctx.send(embed=ping_embed)
    
@bot.command()
async def test(ctx):
    embeded_msg = discord.Embed(title="EMG F-1 Firearms UDR-15 AR15 Edge II Full Metal Airsoft AEG Training Rifle (Model: Black / RS3 Stock / Gun Only) https://www.evike.com/products/110655/", description="Discounted Price: **$293.25**", color=discord.Color.red())
    embeded_msg.set_thumbnail(url=bot.user.display_avatar.url)
    embeded_msg.add_field(name="15% OFF", value="Regular Price: $345.00\nID: 110655", inline=False)
    embeded_msg.set_image(url="https://www.evike.com/images/emg-11654a-sm.jpg")
    embeded_msg.set_footer(text="Discount Ends In: 2:49:05")
    await ctx.send(embed=embeded_msg)

with open("token.txt") as file:
    token = file.read()

bot.run(token)