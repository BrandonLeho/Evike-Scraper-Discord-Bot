import discord
from discord.ext import commands, tasks
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time

# Discord bot setup
bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())

last_seen_ids = set()

# Selenium setup
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service("D:\VSCode Projects\chromedriver-win64\chromedriver.exe")  # Replace with your ChromeDriver path
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scrape_evike_deals():
    driver = setup_driver()
    url = "https://www.evike.com/epic-deals/"
    driver.get(url)

    # Wait for JavaScript to load (adjust delay as necessary)
    time.sleep(3)

    # Get the page source after rendering
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

        # Extract countdown timer
        countdown_div = deal.find('div', class_='epiccountdown')
        deal_end_timestamp = None

        if countdown_div:
            try:
                days = int(countdown_div.find('span', string="DAYS").find_previous('span').text.strip())
                hours = int(countdown_div.find('span', string="HRS").find_previous('span').text.strip())
                minutes = int(countdown_div.find('span', string="MIN").find_previous('span').text.strip())
                seconds = int(countdown_div.find('span', string="SEC").find_previous('span').text.strip())

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

@tasks.loop(minutes=1)
async def update_deals():
    global last_seen_ids
    channel_id = 1301969132178374737
    channel = bot.get_channel(channel_id)

    if channel is not None:
        evike_deals = scrape_evike_deals()
        new_deals = [deal for deal in evike_deals if deal['product_id'] not in last_seen_ids]

        if new_deals:
            last_seen_ids.update(deal['product_id'] for deal in new_deals)

            for deal in new_deals:
                embeded_msg = discord.Embed(
                    title=f"{deal['name']} - ({deal['link']})",
                    description=f"Discounted Price: ```diff - {deal['price']}```",
                    color=discord.Color.red()
                )
                embeded_msg.set_thumbnail(url=bot.user.display_avatar.url)
                embeded_msg.add_field(name=f"{deal['discount']}", value=f" Regular Price: ~~{deal['og_price']}~~\nProduct ID: {deal['product_id']}", inline=False)

                if deal['image_url']:
                    embeded_msg.set_image(url=deal['image_url'])
                    
                if deal['end_time']:
                    embeded_msg.add_field(name="Deal Ends:", value=f"<t:{deal['end_time']}:F>")

                await channel.send(embed=embeded_msg, silent=True)
        else:
            print("No new deals found.")

@bot.event
async def on_ready():
    print("Bot ready!")
    update_deals.start()

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

with open("token.txt") as file:
    token = file.read()

bot.run(token)
