import time
import pandas as pd
from selenium import webdriver

# Load the CSV file
df = pd.read_csv('urls.csv')

# Set up the Chrome driver
driver = webdriver.Chrome()

# Iterate through the rows in the CSV
for index, row in df.iterrows():
    name = row['Name']
    url = row['URL']
    
    print(f"Opening {name} - {url}")
    
    # Open the URL
    driver.get(url)
    
    # Keep the page open for 5 seconds
    time.sleep(5)

# Close the browser after opening all pages
driver.quit()
