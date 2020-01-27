import os
import time
import random
from decouple import config
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys


def download_file_options(opts):

    # Value 0 = Save file on users desktop.
    # Value 1 = Save file in users downloads folder.
    # Value 2 = Save file to given directory.
    opts.set_preference("browser.download.folderList", 2)

    # Save the file in this directory.
    opts.set_preference("browser.download.dir",
                        config("TEMP_DATA_DIR"));

    # Download manager should not open window when file starts downloading.
    opts.set_preference("browser.download.manager.showWhenStarting", False)

    # Set the MIME type of file we're downloading.
    opts.set_preference("browser.helperApps.neverAsk.saveToDisk",
                        "text/plain")


def configure_browser():
    opts = Options()
    opts.headless = True

    browser = Firefox(options=opts)

    # Max wait is 5 seconds for page to load on each get() request
    browser.wait = WebDriverWait(browser, 5)

    return browser


def browser_sleep(start, stop):
    # Get a random number between the given values,
    # then sleep for that many seconds.
    time.sleep(random.randint(3, 10))


# browser.page_source does not work for huge HTML pages.
# Out HTML pages will be huge sometimes, since it's the text
# of all the company filing data.
# Instead,
#   - download the file to a local directory,
#   - read it to get the data,
#   - delete it to make sure disk space is not getting full, and
#   - return the read data.
#
# Found out that this does not work for links.
# There a way to right-click (context_click),
# but there is no way to access the browser's
# context menu.
# This will only work if you have a context menu
# inside your HTML page.
def get_filing(browser, element, filename):

    element.click()

    # Investigate a better way to do this.
    browser_sleep(10, 10)

    full_filename = os.path.join(config('TEMP_DATA_DIR'), filename)
    print(f'Getting full_filename: {full_filename}')
    with open(full_filename, 'r') as f:
        data = f.read()

    os.remove(full_filename)

    return data
