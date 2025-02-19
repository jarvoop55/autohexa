import os
import re
import asyncio
import random
import logging
from dotenv import load_dotenv
from collections import deque
from telethon import TelegramClient, events
from telethon.errors import MessageIdInvalidError
from flask import Flask

app = Flask(__name__)

@app.route('/health')
def health_check():
    return "OK", 200

if __name__ == "__main__":
    import threading
    flask_thread = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000))
    flask_thread.start()

API_ID = 20061115
API_HASH = "c30d56d90d59b3efc7954013c580e076"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

SESSION_FILE = "your_session_file.session"
BOT_CHAT_ID = 572621020
NOTIFICATION_CHAT_ID = -1002235680545  # Change if needed
HUNT_COOLDOWN = random.randint(3, 4)  # Randomized for anti-detection

LEGENDARY_POKS = {"Aerodactyl", "Charizard", "Basculin", "Voltorb", "Gallade", "Metagross", "Camerupt", "Munchlax", "Sliggoo"}
REGULAR_BALL = {"Dialga","Magikarp","Darumaka", "Darmanitan", "Wishiwashi", "Drakloak", "Duraludon", "Rotom", "Tentacruel", "Snorlax", "Overqwil", "Munchlax", "Kleavor", "Fennekin", "Delphox", "Braixen", "Axew", "Fraxure", "Haxorus", "Floette", "Flabebe", "Rufflet", "Porygon", "Porygon2", "Mankey", "Primeape", "Dratini", "Shellder", "Gible", "Gabite", "Dragonair", "Golett", "Goomy", "Vikavolt", "Vullaby", "Litwick", "Lampent", "Wimpod", "Buneary", "Ursaring", "Teddiursa", "Hawlucha", "Abra", "Kadabra", "Turtonator", "Jolteon", "Dwebble", "Crustle", "Starly", "Stantler", "Rhyhorn", "Staryu", "Starmie", "Tauros", "Lapras", "Vaporeon", "Cyndaquil", "Quilava", "Typhlosion", "Totodile", "Croconaw", "Feraligatr", "Espeon", "Slakoth", "Vigoroth", "Lotad", "Lombre", "Ludicolo", "Treecko", "Grovyle", "Electrike", "Manectric", "Growlithe", "Monferno", "Piplup", "Prinplup", "Chimchar", "Sirfetch'd", "Staravia", "Bagon", "Shelgon", "Salamence", "Tepig", "Pignite", "Spiritomb", "Togekiss", "Skorupi", "Drilbur", "Timburr", "Gurdurr", "Scraggy", "Scrafty",  "Cofagrigus", "Zorua", "Zoroark", "Cinccino", "Frillish", "Jellicent", "Karrablast", "Escavalier", "Ferroseed", "Mienfoo", "Mienshao", "Cryogonal", "Shelmet", "Accelgor", "Helioptile", "Heliolisk", "Tyrunt", "Tyrantrum", "Sylveon", "Litleo", "Pyroar", "Chespin", "Quilladin", "Chesnaught", "Durant", "Deino", "Phantump", "Trevenant", "Pumpkaboo", "Gourgeist", "Popplio", "Brionne", "Litten", "Torracat", "Rowlet", "Dartrix", "Grookey", "Thwackey", "Rillaboom", "Scorbunny", "Raboot", "Orbeetle", "Rookidee", "Corvisquire", "Sobble", "Drizzile", "Inteleon", "Dracozolt", "Dracovish", "Morpeko", "Sneasler", "Toxapex", "Mareanie", "Volcarona", "Tentacool", "Larvesta", "Charmeleon", "Charmander", "Togetic", "Togepi", "Druddigon", "Dhelmise","Runerigus", "Lucario", "Unfezant", "Tranquill", "Pidove", "Barraskewda", "Arrokuda", "Zubat", "Golbat", "Gastly", "Haunter", "Clauncher", "Clawitzer", "Froslass", "Cutiefly", "Ribombee","Arctozolt","Arctovish","Chewtle","Cufant","Impidimp","Morgrem","Hatenna","Hattrem","Trumbeak","Charjabug","Rockruff","Wishiwashi","Mudbray","Bounsweet","Steenee","Sliggoo","Squirtle","Wartortle","Mantine","Mantyke","Gligar","Gliscor"}
REPEAT_BALL = LEGENDARY_POKS

low_lvl = False
last_two_messages = deque(maxlen=2)
hunting_active = True  # Control whether hunting is active

client = TelegramClient(SESSION_FILE, API_ID, API_HASH)

async def send_hunt():
    """Sends /hunt command every 2 minutes if hunting is active."""
    while client.is_connected():
        if hunting_active:
            await client.send_message(BOT_CHAT_ID, "/hunt")
            logging.info("Sent /hunt command")
        await asyncio.sleep(120)  # 2-minute delay

@client.on(events.NewMessage(pattern="/strh"))
async def start_hunt(event):
    global hunting_active
    hunting_active = True
    await event.reply("✅ Hunting started!")

@client.on(events.NewMessage(pattern="!stoh"))
async def stop_hunt(event):
    global hunting_active
    hunting_active = False
    await event.reply("⏹ Hunting stopped!")

@client.on(events.NewMessage(from_users=BOT_CHAT_ID))
async def message_handler(event):
    global low_lvl

    msg = event.raw_text

    if "Daily hunt limit reached" in msg:
        await client.disconnect()
        return

    if "✨ Shiny Pokémon found!" in msg:
        await client.send_message(NOTIFICATION_CHAT_ID, "4mar shiny aaya Whatsapp kar")
        await client.disconnect()
        return

    if "A wild" in msg:
        pok_name = re.search(r"A wild (\w+) ", msg)
        if pok_name:
            pok_name = pok_name.group(1)
            logging.info(f"Wild Pokémon encountered: {pok_name}")

            if pok_name in REGULAR_BALL or pok_name in REPEAT_BALL:
                await asyncio.sleep(HUNT_COOLDOWN)
                await try_click(event, 0, 0)
            else:
                await asyncio.sleep(HUNT_COOLDOWN)
                await client.send_message(BOT_CHAT_ID, "/hunt")
        return

    if "Battle begins!" in msg:
        match = re.search(r"Wild (\w+) .*?\nLv\. \d+  •  HP (\d+)/(\d+)", msg)
        if match:
            pok_name, current_hp, max_hp = match.groups()
            max_hp = int(max_hp)

            if max_hp <= 50:
                low_lvl = True
                logging.info(f"Low-level Pokémon detected: {pok_name}")
                await asyncio.sleep(HUNT_COOLDOWN)
                await try_click(event, text="Poke Balls")
            else:
                await asyncio.sleep(2)
                await try_click(event, 0, 0)
        return

    if "An expert trainer" in msg:
        await asyncio.sleep(HUNT_COOLDOWN)
        await client.send_message(BOT_CHAT_ID, "/hunt")
        return

    if "Choose your next pokemon." in msg:
        switch_options = ["Sceptile", "Snorlax", "Sliggoo", "Scizor", "Solgaleo"]
        for option in switch_options:
            await try_click(event, text=option)
        return

@client.on(events.MessageEdited(from_users=BOT_CHAT_ID))
async def battle_update(event):
    global low_lvl

    msg = event.raw_text

    if any(x in msg for x in ["fled", "💵", "You caught", "fainted"]):
        low_lvl = False
        await asyncio.sleep(HUNT_COOLDOWN)
        await client.send_message(BOT_CHAT_ID, "/hunt")
        return

    match = re.search(r"Wild (\w+) .*?\nLv\. \d+  •  HP (\d+)/(\d+)", msg)
    if match:
        pok_name, current_hp, max_hp = match.groups()
        current_hp, max_hp = int(current_hp), int(max_hp)
        health_percentage = (current_hp / max_hp) * 100
        logging.info(f"{pok_name} Health: {health_percentage:.2f}%")

        if low_lvl or health_percentage <= 50:
            await asyncio.sleep(HUNT_COOLDOWN)
            await try_click(event, text="Poke Balls")
            if pok_name in REGULAR_BALL:
                await asyncio.sleep(1)
                await try_click(event, text="Regular")
            elif pok_name in REPEAT_BALL:
                await asyncio.sleep(1)
                await try_click(event, text="Repeat")
        else:
            await asyncio.sleep(1)
            await try_click(event, 0, 0)

async def try_click(event, row=None, col=None, text=None, retries=3):
    """Tries to click a button with retries."""
    for attempt in range(retries):
        try:
            if text:
                await event.click(text=text)
            else:
                await event.click(row, col)
            logging.info(f"Clicked button: {text if text else f'Row {row}, Col {col}'}")
            return
        except MessageIdInvalidError:
            logging.warning(f"Failed to click button {text if text else f'Row {row}, Col {col}'} (Attempt {attempt + 1})")
            await asyncio.sleep(1)
    logging.error(f"Button click failed after {retries} attempts: {text if text else f'Row {row}, Col {col}'}")

client.start()

# Run Telegram bot in an asyncio loop
async def run_bot():
    await send_hunt()
    await client.run_until_disconnected()

# Run both Flask and the Telegram bot in parallel
import asyncio
loop = asyncio.get_event_loop()
loop.run_until_complete(run_bot())
