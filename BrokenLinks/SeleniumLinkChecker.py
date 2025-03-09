import csv
import time
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm


def setup_driver():
    """Setup Selenium WebDriver with Chrome."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver


def login(driver, login_url, username, password):
    """Perform login and return True if successful."""
    try:
        driver.get(login_url)
        time.sleep(2)
        
        username_field = driver.find_element(By.NAME, "userIdLogin")
        password_field = driver.find_element(By.NAME, "passwordLogin")
        login_button = driver.find_element(By.TAG_NAME, "button")
        
        username_field.send_keys(username)
        password_field.send_keys(password)
        login_button.click()
        time.sleep(3)
        
        if "login" in driver.current_url.lower():
            print("Login failed.")
            return False
        return True
    except Exception as e:
        print(f"Error during login: {e}")
        return False


def get_all_links(driver, main_url):
    """Extract all links from the page."""
    try:
        driver.get(main_url)
        time.sleep(2)
        
        links = driver.find_elements(By.TAG_NAME, "a")
        return [(main_url, link.get_attribute("href"), link.text or "[No Text]", "Pending") for link in links if link.get_attribute("href")]
    except Exception as e:
        print(f"Error fetching links from {main_url}: {e}")
        return [(main_url, main_url, "Error", "N/A")]


def check_url(driver, main_url, url, anchor_text):
    """Check link status."""
    try:
        driver.get(url)
        time.sleep(2)
        status_code = driver.execute_script("return document.readyState")
        return main_url, url, anchor_text, "Loaded" if status_code == "complete" else "Failed"
    except Exception as e:
        print(f"Error checking URL {url}: {e}")
        return main_url, url, anchor_text, "N/A"


def read_main_urls(file_path):
    """Read main URLs and credentials from CSV."""
    try:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            return [(row[0], row[1], row[2], row[3], row[4]) for row in reader if len(row) >= 5]
    except Exception as e:
        print(f"Error reading CSV file {file_path}: {e}")
        return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--broken-only", action="store_true", help="Report only broken links.")
    args = parser.parse_args()

    input_csv = "urls.csv"
    output_csv = "broken_links_report.csv" if args.broken_only else "all_links_report.csv"
    main_data = read_main_urls(input_csv)
    driver = setup_driver()
    
    all_links = []
    for data in main_data:
        if not login(driver, data[1], data[2], data[3]):
            print(f"Skipping {data[4]} due to login failure.")
            continue
        all_links.extend(get_all_links(driver, data[4]))
    
    checked_links = []
    for link in tqdm(all_links, desc="Checking Links"):
        checked_links.append(check_url(driver, *link))
    
    if args.broken_only:
        checked_links = [link for link in checked_links if link[3] != "Loaded"]
    
    try:
        with open(output_csv, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Main URL", "Link", "Anchor Text", "Status"])
            writer.writerows(checked_links)
        print(f"Report generated: {output_csv}")
    except Exception as e:
        print(f"Error writing output CSV: {e}")
    
    driver.quit()


if __name__ == "__main__":
    main()
