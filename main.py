import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup

# Discord bot setup
bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())

# Global variable to store the last seen product ID
last_seen_id = None

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
        id_span = deal.find('span', id=lambda x: x and x.startswith('pid'))
        product_id = id_span.text.strip() if id_span else 'N/A'

        # Append deal to list
        deals.append({
            "name": product_name,
            "price": price,
            "discount": discount,
            "image_url": image_url,
            "link": product_link,
            "product_id": product_id,
        })

    return deals

# Task to periodically scrape and send updates
@tasks.loop(minutes=1)
async def update_deals():
    global last_seen_id  # Access the global variable
    channel_id = 123456789012345678  # Replace with your channel ID
    channel = bot.get_channel(channel_id)

    if channel is not None:
        evike_deals = scrape_evike_deals()

        # Check if the first deal's product ID matches the last seen ID
        if evike_deals and evike_deals[0]['product_id'] != last_seen_id:
            # Update the last seen ID to the current first deal's ID
            last_seen_id = evike_deals[0]['product_id']

            # Post new deals
            for deal in evike_deals:
                embeded_msg = discord.Embed(
                    title=f"{deal['name']} - [View Deal]({deal['link']})",
                    description=f"Discounted Price: **{deal['price']}**",
                    color=discord.Color.red()
                )
                embeded_msg.set_thumbnail(url=bot.user.display_avatar.url)  # Bot avatar as thumbnail
                embeded_msg.add_field(name=f"{deal['discount']}", value=f"Product ID: {deal['product_id']}", inline=False)

                if deal['image_url']:
                    embeded_msg.set_image(url=deal['image_url'])

                await channel.send(embed=embeded_msg)
        else:
            print("No new deals found.")

@bot.event
async def on_ready():
    print("Bot ready!")
    update_deals.start()  # Start the periodic task when the bot is ready

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
        embeded_msg.add_field(name=f"{deal['discount']}", value=f"Product ID: {deal['product_id']}", inline=False)

        if deal['image_url']:
            embeded_msg.set_image(url=deal['image_url'])

        await ctx.send(embed=embeded_msg)

with open("token.txt") as file:
    token = file.read()

bot.run(token)
