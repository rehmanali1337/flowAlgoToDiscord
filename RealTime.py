from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common import exceptions as seleniumExceptions
import discord
import re
import asyncio
import logging
import threading


logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)
# logging.disable(logging.WARNING)


class RealTime(threading.Thread):
    def __init__(
        self,
        thread_id,
        thread_name,
        driver_path,
        url,
        username,
        password,
        token,
        target_channels_names,
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
        self.target_channels_names = target_channels_names
        self.target_channels = {
            "no_color": None,
            "purple": None,
            "golden": None,
            "black": None,
        }
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

    async def send(self, desc, item_type):
        if item_type == "no_color":
            embd = discord.Embed(
                title="Contract Selection",
                type="rich",
                description=desc,
                color=discord.Color.green(),
            )
        if item_type == "purple":
            embd = discord.Embed(
                title="Contract Selection",
                type="rich",
                description=desc,
                color=discord.Color.purple(),
            )
        if item_type == "golden":
            embd = discord.Embed(
                title="Contract Selection",
                type="rich",
                description=desc,
                color=discord.Color.gold(),
            )
        if item_type == "black":
            embd = discord.Embed(
                title="Contract Selection",
                type="rich",
                description=desc,
                color=discord.Color(000000),
            )
        if not self.target_channel:
            channels = self.client.guilds[0].text_channels
            for channel in channels:
                if self.deEmojify(channel.name) == self.deEmojify(self.target_channel_name):
                    self.target_channel = channel
                    break
        await self.target_channels[item_type].send(embed=embd)

    async def type_of(self, item):
        unusual = item.get_attribute("data-unusual")
        agsweep = item.get_attribute("data-agsweep")
        sizelot = item.get_attribute("data-sizelot")
        logging.info(f"data-ususual : {unusual}")
        logging.info(f"data-agweep : {agsweep}")
        logging.info(f"data-sizelot : {sizelot}")
        if unusual == "true":
            return "purple"
        if agsweep == "true":
            return "golden"
        if sizelot == "true":
            return "black"
        return "no_color"

    async def wait_until_login(self):
        while not self.FLOW_LOGIN:
            await asyncio.sleep(1)

    # This is the main scraper function ...
    async def run_scraper(self):
        if self.FLOW_LOGIN:
            self.driver.refresh()
        else:
            self.FLOW_LOGIN = False
            await self.login()
        await self.wait_until_login()
        await self.client.wait_until_ready()
        self.driver.set_window_size(2048, 1536)
        try:
            logging.info("Waiting for elements...")
            # chat_btn = WebDriverWait(self.driver, 20).until(
            #     EC.presence_of_element_located(
            #         (By.XPATH, '//*[@id="chat"]/div[1]/div/i[2]')
            #     )
            # )
            ai_btn = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="close-aai"]'))
            )

            darkpool_btn = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="darkflow"]/div[1]/div[1]/i[2]')
                )
            )
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="optionflow"]/div[2]/div[1]')
                )
            )

            fullscreen_btn = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="app-controls"]/div/i')
                )
            )
        except seleniumExceptions.TimeoutException:
            self.get_flow_options_data()
            return
        finally:
            try:
                pass
            except seleniumExceptions.ElementNotInteractableException:
                self.get_flow_options_data()
            ai_btn.click()
            darkpool_btn.click()
            fullscreen_btn.click()
            self.driver.fullscreen_window()
        all_items = self.driver.find_elements_by_class_name("option-flow")
        try:
            recent_id = self.data_file["flow_options_id"]
        except KeyError:
            logging.info("No cache found!")
            recent_id = all_items[0].get_attribute("data-flowid")
            self.data_file["flow_options_id"] = recent_id
            self.data_file.sync()

        # Control here means id is already cached.
        while not self.KILL:
            logging.info("Checking for new flow options data ...")
            all_items = self.driver.find_elements_by_class_name("option-flow")
            recent_id = self.data_file["flow_options_id"]
            if int(all_items[0].get_attribute("data-flowid")) > int(recent_id):
                for item in all_items:
                    logging.info(
                        f'Cached id: {recent_id} Network id: {item.get_attribute("data-flowid")}'
                    )
                    if int(item.get_attribute("data-flowid")) > int(recent_id):
                        text = item.text
                        data = text.split("\n")
                        logging.info(len(data))
                        if len(data) >= 9:
                            sector = item.get_attribute("data-sector")
                            desc = f"Time\n{data[0]}\nTicker\n{data[1]}\nExpiry\n{data[2]}\nStrike\n{data[3]}\nC/P\n{data[4]}\nSpot Price\n{data[5]}\nDetails\n{data[6]}\nType\n{data[7]}\nPrem\n{data[8]}\nSection\n{sector}"
                            logging.info(f"Desc: {desc}")
                            item_type = await self.type_of(item)
                            logging.info(f"Type found : {item_type}")
                            await self.send(desc, item_type)
                            await asyncio.sleep(1)
                            continue

                    break

                self.data_file["flow_options_id"] = all_items[0].get_attribute(
                    "data-flowid"
                )
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
