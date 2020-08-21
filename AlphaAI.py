from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common import exceptions as seleniumExceptions
import discord
import asyncio
import re
import logging
import threading


logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)
# logging.disable(logging.WARNING)


class AlphaAI(threading.Thread):
    def __init__(
        self,
        thread_id,
        thread_name,
        driver_path,
        url,
        username,
        password,
        token,
        target_channel_name,
        data_file,
    ):
        threading.Thread.__init__(self)
        self.token = token
        self.loop = asyncio.get_event_loop()
        self.thread_name = thread_name
        self.url = url
        self.password = password
        self.username = username
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(driver_path, options=chrome_options)
        self.data_file = data_file
        self.target_channel_name = target_channel_name
        self.target_channel = None
        self.KILL = False
        self.FLOW_LOGIN = False

    async def login(self):
        logging.info("Logging-in to flowalgo!")
        self.driver.get(self.url)
        username_input = self.driver.find_element_by_xpath(
            '//*[@id="login"]/input[1]')
        password_input = self.driver.find_element_by_xpath(
            '//*[@id="login"]/input[2]')
        login_button = self.driver.find_element_by_xpath(
            '//*[@id="login"]/input[3]')

        username_input.send_keys(self.username)
        password_input.send_keys(self.password)
        login_button.click()
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="optionflow"]/div[2]/div[1]')
                )
            )
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="close-aai"]'))
            )
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="app-controls"]/div/i')
                )
            )
        except seleniumExceptions.TimeoutException:
            pass
        self.FLOW_LOGIN = True

    # Remove emojies from strings
    @staticmethod
    def deEmojify(text):
        regrex_pattern = re.compile(
            pattern="["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "]+",
            flags=re.UNICODE,
        )
        return regrex_pattern.sub(r"", text)

    async def send(self, desc, signal_type):
        if signal_type == "long":
            clr = discord.Color.blue()
        else:
            clr = discord.Color.red()
        embd = discord.Embed(title="Alpha AI", type="rich",
                             description=desc, color=clr)
        if not self.target_channel:
            channels = self.client.guilds[0].text_channels
            for channel in channels:
                if self.deEmojify(channel.name) == self.deEmojify(self.target_channel_name):
                    self.target_channel = channel
                    break
        await self.target_channel.send(embed=embd)

    async def wait_until_login(self):
        while not self.FLOW_LOGIN:
            await asyncio.sleep(1)

    # This is the main scraper function ...
    async def run_scraper(self):
        await self.login()
        await self.wait_until_login()
        await self.client.wait_until_ready()
        self.driver.set_window_size(2048, 1536)
        try:
            logging.info("Waiting for elements...")
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "aai_signal"))
            )
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="fa_aai"]/div[1]'))
            )
            fullscreen_btn = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="app-controls"]/div/i')
                )
            )
        finally:
            fullscreen_btn.click()
            self.driver.fullscreen_window()
        all_items = self.driver.find_elements_by_class_name("aai_signal")
        try:
            recent_id = self.data_file["ai_id"]
        except KeyError:
            logging.info("No cache found!")
            recent_id = all_items[0].get_attribute("data-flowid")
            self.data_file["ai_id"] = recent_id
            self.data_file.sync()

        # Control here means id is already cached.
        while not self.KILL:
            logging.info("Checking for new AI data ...")
            all_items = self.driver.find_elements_by_class_name("aai_signal")
            recent_id = self.data_file["ai_id"]
            if int(all_items[0].get_attribute("data-flowid")) > int(recent_id):
                for item in all_items:
                    logging.info(
                        f'Cached id: {recent_id} Network id: {item.get_attribute("data-flowid")}'
                    )
                    if int(item.get_attribute("data-flowid")) > int(recent_id):
                        text = item.text
                        data = text.split("\n")
                        logging.info(len(data))
                        if len(data) >= 4:
                            desc = f"Date\n{data[0]}\nSymbol\n{data[1]}\nRef\n{data[2]}\nSignal\n{data[3]}"
                            logging.info(f"Desc: {desc}")
                            await self.send(desc, data[3].lower())
                            await asyncio.sleep(1)
                            continue
                    break

                self.data_file["ai_id"] = all_items[0].get_attribute(
                    "data-flowid")
                self.data_file.sync()
            await asyncio.sleep(5)

    async def start_bot(self):
        client = discord.Client()
        self.client = client
        client.loop.create_task(self.run_scraper())
        await client.start(self.token)

    def run(self):
        self.loop.create_task(self.start_bot())
        try:
            self.loop.run_forever()
        except RuntimeError:
            pass
