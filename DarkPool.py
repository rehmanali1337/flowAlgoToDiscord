from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common import exceptions as seleniumExceptions
import discord
import asyncio
import logging
import threading


logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO
)
# logging.disable(logging.WARNING)


class DarkPool(threading.Thread):
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

    async def send(self, desc):
        embd = discord.Embed(
            title="Dark Pool & Equity Blocks",
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
            darkpool_block = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="darkflow"]/div[2]/div[1]')
                )
            )
            fullscreen_btn = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="app-controls"]/div/i')
                )
            )
        finally:
            fullscreen_btn.click()
            self.driver.fullscreen_window()
            all_items = darkpool_block.find_elements_by_class_name("dark-flow")
            logging.info(f"Number of items : {len(all_items)}")
        try:
            recent_id = self.data_file["darkpool_id"]
        except KeyError:
            logging.info("No cache found!")
            recent_id = all_items[0].get_attribute("data-flowid")
            self.data_file["darkpool_id"] = recent_id
            self.data_file.sync()

        # Control here means id is already cached.
        while not self.KILL:
            logging.info("Checking for new darkpool data ...")
            all_items = self.driver.find_elements_by_class_name("dark-flow")
            recent_id = self.data_file["darkpool_id"]
            if int(all_items[0].get_attribute("data-flowid")) > int(recent_id):
                for item in all_items:
                    logging.info(
                        f'Cached id: {recent_id} Network id: {item.get_attribute("data-flowid")}'
                    )
                    if int(item.get_attribute("data-flowid")) > int(recent_id):
                        text = item.text
                        data = text.split("\n")
                        logging.info(len(data))
                        if len(data) == 5:
                            mm = item.find_element_by_class_name(
                                "notional").text
                            desc = f"Time\n{data[0]}\nTicker\n{data[1]}\nQuantity\n{data[2]}\nSpot Price\n{data[3]}\nMM\n{mm}"
                            logging.info(f"Desc: {desc}")
                            logging.info("Description is ready!")
                            await self.send(desc)
                            await asyncio.sleep(1)
                            continue
                    break

                self.data_file["darkpool_id"] = all_items[0].get_attribute(
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
