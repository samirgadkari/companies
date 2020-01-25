import time
import random
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait


def configure_browser():
    opts = Options()
    opts.headless = True

    browser = Firefox(options=opts)
    browser.wait = WebDriverWait(browser, 5)  # Wait for 5 seconds
                                              # on each get() request.
    return browser


def browser_sleep(start, stop):
    # Get a random number between the given values,
    # then sleep for that many seconds.
    time.sleep(random.randint(3, 10))


