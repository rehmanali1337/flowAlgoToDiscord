import discord
from discord.ext import tasks
from configparser import ConfigParser
import os
import shelve
import re
import asyncio
import logging
import time
import sys
import threading
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Local Imports
from DarkPool import DarkPool
from RealTime import RealTime
from AlphaAI import AlphaAI
from Image import Image

# Reading data from conf.ini file....
################################################
config = ConfigParser()
config.read("conf.ini")


logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)
# logging.disable(logging.WARNING)

purple_channel_name = config["DISCORD"]["channel_name_for_purple_data"]
golden_channel_name = config["DISCORD"]["channel_name_for_golden_data"]
black_channel_name = config["DISCORD"]["channel_name_for_black_data"]
no_color_channel_name = config["DISCORD"]["channel_name_for_no_color_data"]
ta_channel_name = config["DISCORD"]["channel_name_for_ta_bot"]
ai_channel_name = config["DISCORD"]["channel_name_for_ai_data"]
darkpool_channel_name = config["DISCORD"]["channel_name_for_darkpool_data"]
driver_path = config["CHROME"]["chromedriver_path"]
site_username = config["FLOWALGO"]["username"]
site_password = config["FLOWALGO"]["password"]
token = config["DISCORD"]["bot_token"]

url = "https://app.flowalgo.com/users/login"
data_file = shelve.open("./tmps/data")


target_channels_names = {
    "no_color": no_color_channel_name,
    "purple": purple_channel_name,
    "golden": golden_channel_name,
    "black": black_channel_name,
}

data_file = shelve.open("./tmps/data")

bot = Image(
    1, "image", driver_path, url, site_username, site_password, token, ta_channel_name,
)

try:
    bot.start()
except KeyboardInterrupt:
    bot.KILL = True
    print("Exiting ... Please wait ...")
