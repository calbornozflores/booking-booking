from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import time
import csv
import re
from tools.io import ask_for_place, ask_for_dates
from tools.selector import select_lang, set_date_range, set_place, get_next_page_button, get_property_number
from tools.validator import clean_property_card
from config.config import webpage_url
from config.xpaths import searchButtonXPATH, hotelPageElementsXPATH


def run():
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.maximize_window()
    driver.get(webpage_url)
    time.sleep(2)

    file = open('output/research.csv', 'a+', newline ='')
    write = csv.writer(file, delimiter=';')

    selected_lang = select_lang(driver)
    print(f"Selected Lang: {selected_lang}")

    input_place = ask_for_place()
    set_place(driver, input_place)

    arrivalDate, departureDate = ask_for_dates()
    set_date_range(driver, arrivalDate, departureDate)

    searchButton = driver.find_element(By.XPATH, searchButtonXPATH)
    searchButton.click()
    time.sleep(8)

    totalProperties = get_property_number(driver)
    print(totalProperties)
    availablePage = True
    while availablePage:
        # Get all Property Card elements in the Hotel Page
        hotelPageElements = driver.find_elements(By.XPATH, hotelPageElementsXPATH)
        time.sleep(3)
        hotelPageElements = [clean_property_card(hpe.text) for hpe in hotelPageElements if hpe.text != ""]

        resortsInfo_list = []
        for hpe in hotelPageElements:
            resortsInfo_list.append(
                hpe.split("\n")
            )
        write.writerows(resortsInfo_list)

        nextPageButton = get_next_page_button(driver)
        availablePage = nextPageButton.is_enabled()
        if availablePage:
            nextPageButton.click()
            time.sleep(8)

    file.close()
    driver.close()

