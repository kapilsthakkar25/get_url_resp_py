from selenium import webdriver
from selenium.webdriver.common.keys import Keys

# Set up the Chrome driver
driver = webdriver.Chrome()

# Load the Google homepage
driver.get("https://www.google.com")

# Search for "seleniumhq"
search_box = driver.find_element("name", "q")
search_box.send_keys("seleniumhq")
search_box.send_keys(Keys.RETURN)

# Close the browser
driver.quit()
