import csv
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
import time

# Path to Edge WebDriver
edge_driver_path = "C:\\temp\\msedgedriver.exe"
service = Service(edge_driver_path)

# Read CSV file
csv_file = "urls.csv"
with open(csv_file, newline='', encoding='utf-8') as file:
    reader = csv.reader(file)
    next(reader)  # Skip header row if present
    
    # Start WebDriver
    driver = webdriver.Edge(service=service)
    
    for row in reader:
        name, url = row
        print(f"Opening {name}: {url}")
        driver.get(url)
        time.sleep(3)  # Wait for the page to load
        print(f"Title: {driver.title}")
    
    driver.quit()
