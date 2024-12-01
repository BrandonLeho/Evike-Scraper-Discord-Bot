import discord
from discord.ext import commands, tasks
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from collections import defaultdict
from urllib.parse import urlparse
import asyncio
import time

bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())

last_seen_ids = set()

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service("D:\VSCode Projects\chromedriver-win64\chromedriver.exe") 
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scrape_evike_deals():
    driver = setup_driver()
    url = "https://www.evike.com/epic-deals/"
    driver.get(url)

    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, 'lxml')
    driver.quit()

    deals = []
    deal_items = soup.find_all('div', class_='dealitem')

    for deal in deal_items[:10]:
        product_name = deal.find('h3').text.strip() if deal.find('h3') else 'N/A'
        price = deal.find('h4').text.strip() if deal.find('h4') else 'N/A'
        og_price = deal.find('s').text.strip() if deal.find('s') else 'N/A'
        discount = deal.find('p', class_='discount').text.strip() if deal.find('p', class_='discount') else 'N/A'
        image_tag = deal.find('img', class_='pthumb')
        image_url = image_tag['src'] if image_tag else None
        link_tag = deal.find('a', href=True)
        product_link = link_tag['href'] if link_tag else None
        id_span = deal.find('span', id=lambda x: x and x.startswith('pid'))
        product_id = id_span.text.strip() if id_span else 'N/A'

        countdown_div = deal.find('div', class_='epiccountdown')
        deal_end_timestamp = None

        if countdown_div:
            try:
                days, hours, minutes, seconds = 0, 0, 0, 0

                days_span = countdown_div.find('span', string="DAYS")
                if days_span:
                    days_amount = days_span.find_previous('span', class_='countdown_amount')
                    days = int(days_amount.text.strip()) if days_amount else 0

                hours_span = countdown_div.find('span', string="HRS")
                if hours_span:
                    hours_amount = hours_span.find_previous('span', class_='countdown_amount')
                    hours = int(hours_amount.text.strip()) if hours_amount else 0

                minutes_span = countdown_div.find('span', string="MIN")
                if minutes_span:
                    minutes_amount = minutes_span.find_previous('span', class_='countdown_amount')
                    minutes = int(minutes_amount.text.strip()) if minutes_amount else 0

                seconds_span = countdown_div.find('span', string="SEC")
                if seconds_span:
                    seconds_amount = seconds_span.find_previous('span', class_='countdown_amount')
                    seconds = int(seconds_amount.text.strip()) if seconds_amount else 0

                now = datetime.now()
                deal_end_time = now + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
                deal_end_timestamp = int(deal_end_time.timestamp())
            except Exception as e:
                print(f"Error extracting countdown: {e}")

        deals.append({
            "name": product_name,
            "price": price,
            "og_price": og_price,
            "discount": discount,
            "image_url": image_url,
            "link": product_link,
            "product_id": product_id,
            "end_time": deal_end_timestamp,
        })

    return deals

active_loops = defaultdict(bool)



def is_valid_url(url):
    """
    Validates that a URL is well-formed and uses HTTP/HTTPS.
    """
    if not url:
        return False
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme) and parsed.scheme in ["http", "https"]

async def send_deals_to_channel(channel):
    global last_seen_ids
    while active_loops[channel.id]:
        evike_deals = scrape_evike_deals()
        new_deals = [deal for deal in evike_deals if deal['product_id'] not in last_seen_ids]

        if new_deals:
            last_seen_ids.update(deal['product_id'] for deal in new_deals)

            for deal in new_deals:
                embeded_msg = discord.Embed(
                    title=f"{deal['name']} - ({deal['link']})",
                    description=f"Discounted Price: **{deal['price']}**",
                    color=discord.Color.red()
                )
                embeded_msg.set_thumbnail(url=bot.user.display_avatar.url)
                embeded_msg.add_field(
                    name=f"{deal['discount']}",
                    value=f" Regular Price: ~~{deal['og_price']}~~\nProduct ID: {deal['product_id']}",
                    inline=False,
                )

                if is_valid_url(deal['image_url']):
                    embeded_msg.set_image(url=deal['image_url'])
                else:
                    print(f"Invalid or missing image URL for product: {deal['product_id']}")

                if deal['end_time']:
                    embeded_msg.add_field(name="Deal Ends:", value=f"<t:{deal['end_time']}:F>")

                try:
                    await channel.send(embed=embeded_msg)
                except discord.errors.HTTPException as e:
                    print(f"Error sending message: {e}")

        else:
            print(f"No new deals found for channel {channel.id}.")

        await asyncio.sleep(60)



@bot.command()
async def start_deals(ctx):
    """
    Starts a loop for the current channel to post deals every 10 seconds.
    """
    channel = ctx.channel

    if active_loops[channel.id]:
        await ctx.send("The deal loop is already running in this channel!")
    else:
        active_loops[channel.id] = True
        await ctx.send("Starting the deal loop in this channel!")
        await send_deals_to_channel(channel)


@bot.command()
async def stop_deals(ctx):
    """
    Stops the loop for the current channel.
    """
    channel = ctx.channel

    if not active_loops[channel.id]:
        await ctx.send("The deal loop is not running in this channel!")
    else:
        active_loops[channel.id] = False
        await ctx.send("Stopped the deal loop in this channel.")




@bot.command()
async def deals(ctx):
    evike_deals = scrape_evike_deals()

    for deal in evike_deals:
        embeded_msg = discord.Embed(
            title=f"{deal['name']} - [View Deal]({deal['link']})",
            description=f"Discounted Price: **{deal['price']}**",
            color=discord.Color.red()
        )
        embeded_msg.set_thumbnail(url=bot.user.display_avatar.url)
        embeded_msg.add_field(name=f"{deal['discount']}", value=f"Product ID: {deal['product_id']}", inline=False)

        if deal['image_url']:
            embeded_msg.set_image(url=deal['image_url'])
            
        if deal['end_time']:
            embeded_msg.add_field(name="Deal Ends:", value=f"<t:{deal['end_time']}:F>")

        await ctx.send(embed=embeded_msg)
        
        
        
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.reactions = True
intents.guild_reactions = True
intents.members = True
emoji_to_role = {
    "👍": "Evike Deals",
}

@bot.command()
async def rr(ctx):
    """Command to send a message for role assignment."""
    message = await ctx.send(
        "React to this message to get a role:\n" +
        "\n".join([f"{emoji}: {role}" for emoji, role in emoji_to_role.items()])
    )
    for emoji in emoji_to_role.keys():
        await message.add_reaction(emoji)

@bot.event
async def on_raw_reaction_add(payload):
    """Event to handle reaction adds."""
    if payload.member.bot:
        return

    guild = bot.get_guild(payload.guild_id)
    role_name = emoji_to_role.get(payload.emoji.name)
    if role_name:
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            await payload.member.add_roles(role)
            print(f"Assigned {role.name} to {payload.member.display_name}")

@bot.event
async def on_raw_reaction_remove(payload):
    """Event to handle reaction removals."""
    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if not member.bot:
        role_name = emoji_to_role.get(payload.emoji.name)
        if role_name:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                await member.remove_roles(role)
                print(f"Removed {role.name} from {member.display_name}")



        
        
        


@bot.event
async def on_ready():
    print("Bot ready!")

with open("token.txt") as file:
    token = file.read()

bot.run(token)