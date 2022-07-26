import csv
import logging
import progressbar
import re
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from tools.selector import select_lang, set_date_range, set_place, get_next_page_button, get_property_number
from tools.validator import clean_property_card
from config.config import webpage_url
from config.xpaths import searchButtonXPATH, hotelPageElementsXPATH
from tools.format import formatting


def run(input_place, arrivalDate, departureDate, displayed_city):
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.maximize_window()
    driver.get(webpage_url)
    time.sleep(2)

    file = open('output/research.csv', 'a+', newline ='')
    write = csv.writer(file, delimiter=';')

    selected_lang = select_lang(driver)
    print(f"Selected Lang: {selected_lang}")

    set_place(driver, input_place, displayed_city)

    set_date_range(driver, arrivalDate, departureDate)

    searchButton = driver.find_element(By.XPATH, searchButtonXPATH)
    searchButton.click()
    time.sleep(8)

    single_run(driver, file, write, arrivalDate, departureDate)

    file.close()
    driver.close()
    formatting()


def single_run(driver, file, write, arrivalDate, departureDate):
    totalProperties = get_property_number(driver)

    bar = progressbar.ProgressBar(maxval = totalProperties, \
    widgets=[progressbar.Bar(u"█", '[', ']'), ' ', progressbar.Percentage()])
    bar.start()

    availablePage = True
    hotelCount = 0
    while availablePage:
        # Get all Property Card elements in the Hotel Page
        hotelPageElements = driver.find_elements(By.XPATH, hotelPageElementsXPATH)
        time.sleep(3)
        hotelPageElements = [clean_property_card(hpe.text) for hpe in hotelPageElements if hpe.text != ""]

        resortsInfo_list = []
        for hpe in hotelPageElements:
            hpe_content = hpe.split("\n")
            hpe_content = hpe_content + [arrivalDate, departureDate]
            resortsInfo_list.append(
                hpe_content
            )
        write.writerows(resortsInfo_list)
        hotelCount = hotelCount + len(resortsInfo_list)
        try:
            assert hotelCount <= totalProperties
            bar.update(hotelCount)
        except:
            bar.update(totalProperties)
            logging.warn(f"Mismatch number of properties found [Initial Number - Actual Number]: {totalProperties - hotelCount}")

        nextPageButton = get_next_page_button(driver)
        availablePage = nextPageButton.is_enabled()
        if availablePage:
            nextPageButton.click()
            time.sleep(8)
    
    bar.finish()
