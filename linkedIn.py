from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import parameters, csv, os.path, time
from datetime import datetime
import random

short_random = random.randint(5, 20)
medium_random = random.randint(20, 60)
long_random = random.randint(60, 100)
compteur = 0

def open_profile(profile_link):   
    driver.execute_script("window.open('', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(profile_link)
    time.sleep(short_random)
    html = driver.find_element(By.TAG_NAME, 'html')
    html.send_keys(Keys.END)
    time.sleep(short_random)
    # Incrémenter la variable globale
    global compteur   
    compteur += 1
    print(compteur)
    driver.close()  
    driver.switch_to.window(driver.window_handles[0])  

# Functions
def search_and_send_request(keywords, till_page, writer, ignore_list=[]):
    with open(file_name, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=';')
        for page in range(1, till_page + 1):
            print('\nINFO: Checking on page %s' % (page))
            query_url = 'https://www.linkedin.com/search/results/people/?keywords=' + keywords + '&origin=GLOBAL_SEARCH_HEADER&page=' + str(page)
            driver.get(query_url)
            time.sleep(medium_random)
            html = driver.find_element(By.TAG_NAME, 'html')
            html.send_keys(Keys.END)
            time.sleep(medium_random)
            linkedin_urls = driver.find_elements(By.CLASS_NAME, 'reusable-search__result-container')
            print('INFO: %s connections found on page %s' % (len(linkedin_urls), page))
            for index, result in enumerate(linkedin_urls, start=1):
                text = result.text.split('\n')[0]
                if text in ignore_list or text.strip() in ignore_list:
                    print("%s ) IGNORED: %s" % (index, text))
                    continue
                connection_action = result.find_elements(By.CLASS_NAME, 'artdeco-button__text')
                if connection_action:
                    connection = connection_action[0]
                else:
                    print("%s ) CANT: %s" % (index, text))
                    continue
                if connection.text == 'Connect':
                    try:
                        coordinates = connection.location_once_scrolled_into_view  # returns dict of X, Y coordinates
                        driver.execute_script("window.scrollTo(%s, %s);" % (coordinates['x'], coordinates['y']))
                        time.sleep(medium_random)
                        connection.click()
                        time.sleep(medium_random)
                        if driver.find_elements(By.CLASS_NAME, 'artdeco-button--primary')[0].is_enabled():
                            driver.find_elements(By.CLASS_NAME, 'artdeco-button--primary')[0].click()
                            date_actuelle = datetime.now().strftime("%Y-%m-%d")
                            writer.writerow([text, date_actuelle])
                            print("%s ) SENT: %s" % (index, text))
                            profile_link = result.find_element(By.TAG_NAME, 'a').get_attribute('href')
                            open_profile(profile_link)
                        
                        else:
                            driver.find_elements(By.CLASS_NAME, 'artdeco-modal__dismiss')[0].click()
                            print("%s ) CANT: %s" % (index, text))
                    except Exception as e:
                        print('%s ) ERROR: %s' % (index, text))
                    time.sleep(medium_random)
                elif connection.text == 'Pending':
                    print("%s ) PENDING: %s" % (index, text))
                else:
                    if text:
                        print("%s ) CANT: %s" % (index, text))
                    else:
                        print("%s ) ERROR: You might have reached limit" % (index))


try:
    # Login
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get('https://www.linkedin.com/login')
    driver.find_element('id', 'username').send_keys(parameters.linkedin_username)
    driver.find_element('id', 'password').send_keys(parameters.linkedin_password)
    driver.find_element('xpath', '//*[@type="submit"]').click()
    time.sleep(10)
    # CSV file loging
    file_name = parameters.file_name
    file_exists = os.path.isfile(file_name)
    writer = csv.writer(open(file_name, 'a'))
    if not file_exists: writer.writerow(['Connection Summary'])
    ignore_list = parameters.ignore_list
    if ignore_list:
        ignore_list = [i.strip() for i in ignore_list.split(',') if i]
    else:
        ignore_list = []
    # Search
    search_and_send_request(keywords=parameters.keywords, till_page=parameters.till_page, writer=writer,
                            ignore_list=ignore_list)
except KeyboardInterrupt:
    print("\n\nINFO: User Canceled\n")
except Exception as e:
    print('ERROR: Unable to run, error - %s' % (e))
finally:
    # Close browser
    driver.quit()