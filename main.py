import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup

# Discord bot setup
bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())

# Function to scrape deals from Evike
def scrape_evike_deals():
    # URL of the Epic Deals page
    url = "https://www.evike.com/epic-deals/"
    response = requests.get(url)
    response.raise_for_status()  # Ensure the request was successful
    soup = BeautifulSoup(response.text, 'lxml')

    # List to store scraped deals
    deals = []

    # Find all deal containers
    deal_containers = soup.find_all('div', class_='dealcontainer')

    # Extract information for each deal
    for deal in deal_containers[:5]:  # Limit to first 5 deals
        product_name = deal.find('h3', id=lambda x: x and x.startswith('pname')).text.strip() if deal.find('h3') else 'N/A'
        price = deal.find('h4').text.strip() if deal.find('h4') else 'N/A'
        discount = deal.find('p', class_='discount').text.strip() if deal.find('p', class_='discount') else 'N/A'
        image_tag = deal.find('img', class_='pthumb')
        image_url = image_tag['src'] if image_tag else None
        link_tag = deal.find('a')
        product_link = link_tag['href'] if link_tag else None

        # Append deal to list
        deals.append({
            "name": product_name,
            "price": price,
            "discount": discount,
            "image_url": image_url,
            "link": product_link,
        })

    return deals

@bot.event
async def on_ready():
    print("Bot ready!")

@bot.command()
async def deals(ctx):
    # Scrape deals from Evike
    evike_deals = scrape_evike_deals()

    # Create embedded messages for each deal
    for deal in evike_deals:
        embeded_msg = discord.Embed(
            title=f"{deal['name']} - [View Deal]({deal['link']})",
            description=f"Discounted Price: **{deal['price']}**",
            color=discord.Color.red()
        )
        embeded_msg.set_thumbnail(url=bot.user.display_avatar.url)  # Bot avatar as thumbnail
        embeded_msg.add_field(name=f"{deal['discount']}", value=f"Link: {deal['link']}", inline=False)
        if deal['image_url']:
            embeded_msg.set_image(url=deal['image_url'])
        embeded_msg.set_footer(text="Grab it before it's gone!")
        await ctx.send(embed=embeded_msg)

with open("token.txt") as file:
    token = file.read()

bot.run(token)























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