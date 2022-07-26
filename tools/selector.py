from selenium.webdriver.common.by import By
import time


def select_lang(driver):
    """
    Function to select any Lang from the displayed ones.
    Currently has been fixed at US.
    """
    driver.find_element(By.XPATH, '//*[@id="b2indexPage"]/header/nav[1]/div[2]/div[2]/button').click()
    time.sleep(2)
    langs = driver.find_element(By.XPATH, '//*[@id="language-selection"]/div/div/div/div/div/div[2]/div/div[2]/div/div').text
    lang_list = langs.split("\n")
    if True:
        us_lang = [x for x in lang_list if "US" in x][0]
        input_lang_idx = lang_list.index(us_lang) + 1
    else:
        for idx, lang in enumerate(lang_list):
            print(f"[{idx + 1}] {lang}")
        try:
            input_lang_idx = int(input("Lang Idx: "))
            assert len(lang_list) >= input_lang_idx
        except:
            input_lang_idx = 2
    lang_idx = input_lang_idx - 1
    lang_row = lang_idx // 4
    lang_col = 1 + lang_idx - 4 * lang_row
    lang_row = lang_row + 1

    # Click on the Lang Buttom
    lang = driver.find_element(By.XPATH, f'//*[@id="language-selection"]/div/div/div/div/div/div[2]/div/div[2]/div/div/div[{lang_row}]/ul/li[{lang_col}]/a/div/div[2]')
    selected_lang = lang.text
    lang.click()
    return selected_lang


def set_date_range(driver, arrivalDate, departureDate):
    """
    Function to select arrivalDate and departureDate
    on a displayed calendar with the possibility
    to switch calendar sheets for further dates.
    """
    pickedlDates = [False, False]
    while not all(pickedlDates):
        # Left Displayed Calendar
        for i in range(1,7):
            for j in range(1,8):
                try:
                    dayButtom = driver.find_element(By.XPATH, f'//*[@id="frm"]/div[1]/div[2]/div[2]/div/div/div[3]/div[1]/table/tbody/tr[{i}]/td[{j}]')
                    day = dayButtom.get_attribute("data-date")
                    if day == arrivalDate and pickedlDates[0] == False:
                        print(day)
                        pickedlDates[0] = True
                        dayButtom.click()
                    elif day == departureDate and pickedlDates[1] == False:
                        print(day)
                        pickedlDates[1] = True
                        dayButtom.click()
                except:
                    pass
        # Right Displayed Calendar
        for i in range(1,7):
            for j in range(1,8):
                try:
                    dayButtom = driver.find_element(By.XPATH, f'//*[@id="frm"]/div[1]/div[2]/div[2]/div/div/div[3]/div[2]/table/tbody/tr[{i}]/td[{j}]')
                    day = dayButtom.get_attribute("data-date")
                    if day == arrivalDate and pickedlDates[0] == False:
                        print(day)
                        pickedlDates[0] = True
                        dayButtom.click()
                    elif day == departureDate and pickedlDates[1] == False:
                        print(day)
                        pickedlDates[1] = True
                        dayButtom.click()
                except:
                    pass
        # Next Calendar Page
        if not all(pickedlDates):
            driver.find_element(By.XPATH, f'//*[@id="frm"]/div[1]/div[2]/div[2]/div/div/div[2]').click()


def set_place(driver, input_place):
    """
    Funtion to insert the trip place and click over
    any suggested option given by the webpage.
    """    
    # Inserting place
    driver.find_element(By.XPATH, f'//*[@id="ss"]').send_keys(input_place)
    time.sleep(2)
    # Click over a displayed option
    displayedPlaces = driver.find_element(By.XPATH, '//*[@id="frm"]/div[1]/div[1]/div[1]/div[1]/ul[1]').text
    displayedPlaces_list = displayedPlaces.split("\n")
    displayedPlaces_list_titles = [x for idx, x in enumerate(displayedPlaces_list) if idx % 2 == 0]
    displayedPlaces_list_subtitles = [x for idx, x in enumerate(displayedPlaces_list) if idx % 2 == 1]
    displayedPlaces_arrange = [f"{x} ({y})" for x,y in zip(displayedPlaces_list_titles, displayedPlaces_list_subtitles)]

    for idx, place in enumerate(displayedPlaces_arrange):
        print(f"[{idx + 1}] {place}")

    try:
        input_place_idx = int(input("Place Idx: "))
        assert len(displayedPlaces_arrange) >= input_place_idx
    except:
        input_place_idx = 1

    driver.find_element(By.XPATH, f'//*[@id="frm"]/div[1]/div[1]/div[1]/div[1]/ul[1]/li[{input_place_idx}]').click()


def get_next_page_button(driver):
    """
    Funtion to get in a lazy and non parametrical way the button nextPage.
    Looking for the Next Page button into all the page buttons.
    """
    allButtons = driver.find_elements(By.XPATH, "//*[@type='button']")
    allButtons_label = [singleButton.get_attribute("aria-label") for singleButton in allButtons]
    try:
        nextPageIdx = allButtons_label.index("Next page")
        nextPageButton = allButtons[nextPageIdx]
    except:
        nextPageButton = None
    return nextPageButton
