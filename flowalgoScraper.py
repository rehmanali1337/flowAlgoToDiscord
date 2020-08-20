from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import os
import shelve


class Scraper:
    def __init__(self, browser, url, username, password):
        self.browser = browser
        self.url = url
        self.username = username
        self.password = password
        self.screen_clear = False

    def login(self):
        self.browser.get(self.url)
        username_input = self.browser.find_element_by_xpath('//*[@id="login"]/input[1]')
        password_input = self.browser.find_element_by_xpath('//*[@id="login"]/input[2]')
        login_button = self.browser.find_element_by_xpath('//*[@id="login"]/input[3]')

        username_input.send_keys(self.username)
        password_input.send_keys(self.password)
        login_button.click()

    def get_source(self):
        print("Getting the source...")
        src = self.browser.page_source
        return src

    def compare_dict(self, dict1, dict2):
        for k, v in dict1.items():
            if k in dict2.keys():
                if dict2[k] == v:
                    continue
                return False
        return True

    def make_data(self, data_type, items_list):
        print("Checking if new data exists...")
        if not items_list:
            print("Data list is empty!")
            return None
        try:
            shelf = shelve.open("./tmps/data")
            purple = shelf[data_type]
        except KeyError:
            print("No previous data found")
            shelf[data_type] = items_list[0]
            shelf.sync()
            shelf.close()
            return None
        for item in items_list:
            succuss = self.compare_dict(purple, item)
            if succuss:
                print("Item matched..")
                index = items_list.index(item)
                if index == 0:
                    print("Matched at index 0")
                    return None
                shelf = shelve.open("./tmps/data")
                shelf[data_type] = item
                shelf.sync()
                shelf.close()
                new_list = items_list[:index].copy()
                return new_list
            continue
        return None

    def get_flow_options_data(self, type_of_data, src):
        print("Getting flow-options data...")
        soup = BeautifulSoup(src, "html.parser")
        self.all_items = soup.findAll("div", "option-flow")

        def create_item(item):
            # print("Creating item...")
            item_list = item.text.split("\n")
            filtered_list = list(filter(None, item_list))
            time = filtered_list[0]
            ticker = filtered_list[1]
            expiry = filtered_list[2].replace("Expiry", "")
            strike = filtered_list[3].replace("Strike", "")
            cp = filtered_list[4].replace("C/P", "")
            spot_price = filtered_list[5].replace("Spot Price", "")
            details = filtered_list[6].replace("Contract Size | Price", "")
            item_type = filtered_list[7]
            prem = filtered_list[8]
            section = filtered_list[9]
            to_append = {
                "time": time,
                "ticker": ticker,
                "expiry": expiry,
                "strike": strike,
                "cp": cp,
                "spot_price": spot_price,
                "details": details,
                "item_type": item_type,
                "prem": prem,
                "section": section,
            }
            return to_append

        new_list = []
        if type_of_data == "purple":
            # Filter the purple list
            print("Generating list for purple...")
            for item in self.all_items:
                attrs = item.attrs
                if attrs["data-unusual"] == "true":
                    # print("Match..")
                    to_append = create_item(item)
                    new_list.append(to_append)

            # Check if there are any new items in the list.
            new_data = self.make_data("purple", new_list)
            if new_data:
                return new_data
            return None

        if type_of_data == "golden":
            # Filter all the golden items
            for item in self.all_items:
                attrs = item.attrs
                if attrs["data-agsweep"] == "true":
                    # print("Match")
                    to_append = create_item(item)
                    new_list.append(to_append)
            # Check if there are any new items in the list.
            new_data = self.make_data("golden", new_list)
            if new_data:
                return new_data
            return None

        if type_of_data == "light_black":
            # Filter all the light black items.
            for item in self.all_items:
                attrs = item.attrs
                if attrs["data-sizelot"] == "true":
                    # print("Match")
                    to_append = create_item(item)
                    new_list.append(to_append)
            # Check if there are any new items in the list.
            new_data = self.make_data("light_black", new_list)
            if new_data:
                return new_data
            return None

        if type_of_data == "no_color":
            # Filter all the no_color items
            for item in self.all_items:
                attrs = item.attrs
                if (
                    attrs["data-unusual"] == ""
                    and attrs["data-agsweep"] == ""
                    and attrs["data-sizelot"] == ""
                ):
                    # print("Match")
                    to_append = create_item(item)
                    new_list.append(to_append)

            # Check if there are any new items in the list.
            new_data = self.make_data("no_color", new_list)
            if new_data:
                return new_data
            return None

    def get_darkpool_data(self, src):
        print("Getting darkpool data...")
        soup = BeautifulSoup(src, "html.parser")
        darkpool_items = soup.findAll("div", "dark-flow")
        new_list = []
        for item in darkpool_items:
            item_list = item.text.split("\n")
            filtered_list = list(filter(None, item_list))
            time = filtered_list[0].replace("\xa0 ", "")
            ticker = filtered_list[1]
            quantity = filtered_list[2].replace("Share Quantity", "")
            spot_price = filtered_list[3].replace("Spot Price", "")
            mm = filtered_list[4]

            to_append = {
                "time": time,
                "ticker": ticker,
                "quantity": quantity,
                "spot_price": spot_price,
                "mm": mm,
            }
            new_list.append(to_append)
        new_data = self.make_data("darkpool", new_list)
        if new_data:
            return new_data
        return None

    def get_alpha_ai_data(self, src):
        print("Filtering alpha ai data..")
        soup = BeautifulSoup(src, "html.parser")
        alpha_ai_signals = soup.findAll("div", "aai_signal")
        new_list = []
        for item in alpha_ai_signals:
            print("Got ai data..")
            item_list = item.text.split("\n")
            filtered_list = list(filter(None, item_list))
            date = filtered_list[0]
            symbol = filtered_list[1]
            ref = filtered_list[2]
            signal = filtered_list[3]
            to_append = {"date": date, "symbol": symbol, "ref": ref, "signal": signal}
            new_list.append(to_append)

        new_data = self.make_data("alpha_ai", new_list)
        if new_data:
            return new_data
        return None

    def get_screenshot(self, location, search_str):
        if self.screen_clear:
            try:
                search_btn = WebDriverWait(self.browser, 20).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//*[@id="filter-flow"]/div/input')
                    )
                )
            finally:
                search_btn.clear()
                search_btn.send_keys(search_str)
                time.sleep(2)
                self.browser.get_screenshot_as_file(location)
                return location

        try:
            print("Waiting for element...")
            chat_btn = WebDriverWait(self.browser, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="chat"]/div[1]/div/i[2]')
                )
            )
            ai_btn = WebDriverWait(self.browser, 20).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="close-aai"]'))
            )
            darkpool_btn = WebDriverWait(self.browser, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="darkflow"]/div[1]/div[1]/i[2]')
                )
            )

            fullscreen_btn = WebDriverWait(self.browser, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="app-controls"]/div/i')
                )
            )
            search_btn = WebDriverWait(self.browser, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="filter-flow"]/div/input')
                )
            )

        finally:
            print("Taking Screenshot....")
            chat_btn.click()
            ai_btn.click()
            darkpool_btn.click()
            fullscreen_btn.click()
            search_btn.send_keys(search_str)
            time.sleep(2)
            self.screen_clear = True
            self.browser.get_screenshot_as_file(location)
        return location

    def refresh_source(self):
        self.browser.refresh()

