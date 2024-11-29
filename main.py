import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup

bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())

last_seen_ids = set()

def scrape_evike_deals():
    url = "https://www.evike.com/epic-deals/"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')

    deals = []

    deal_items = soup.find_all('div', class_='dealitem')

    for deal in deal_items[:10]:
        product_name = deal.find('h3').text.strip() if deal.find('h3') else 'N/A'
        price = deal.find('h4').text.strip() if deal.find('h4') else 'N/A'
        discount = deal.find('p', class_='discount').text.strip() if deal.find('p', class_='discount') else 'N/A'
        image_tag = deal.find('img', class_='pthumb')
        image_url = image_tag['src'] if image_tag else None
        link_tag = deal.find('a', href=True)
        product_link = link_tag['href'] if link_tag else None
        id_span = deal.find('span', id=lambda x: x and x.startswith('pid'))
        product_id = id_span.text.strip() if id_span else 'N/A'

        deals.append({
            "name": product_name,
            "price": price,
            "discount": discount,
            "image_url": image_url,
            "link": product_link,
            "product_id": product_id,
        })

    return deals

@tasks.loop(minutes = 1)
async def update_deals():
    global last_seen_ids
    channel_id = 1301969132178374737
    channel = bot.get_channel(channel_id)
    print(last_seen_ids)

    if channel is not None:
        evike_deals = scrape_evike_deals()

        new_deals = [deal for deal in evike_deals if deal['product_id'] not in last_seen_ids]

        if new_deals:
            last_seen_ids.update(deal['product_id'] for deal in new_deals)

            for deal in new_deals:
                embeded_msg = discord.Embed(
                    title=f"{deal['name']} - [View Deal]({deal['link']})",
                    description=f"Discounted Price: **{deal['price']}**",
                    color=discord.Color.red()
                )
                embeded_msg.set_thumbnail(url=bot.user.display_avatar.url)
                embeded_msg.add_field(name=f"{deal['discount']}", value=f"Product ID: {deal['product_id']}", inline=False)

                if deal['image_url']:
                    embeded_msg.set_image(url=deal['image_url'])

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

        await ctx.send(embed=embeded_msg)

with open("token.txt") as file:
    token = file.read()

bot.run(token)
