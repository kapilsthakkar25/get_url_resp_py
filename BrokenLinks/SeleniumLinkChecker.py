import csv
import time
import random
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Edge/119.0.0.0 Safari/537.36",
]

LOGIN_KEYWORDS = ["login", "sign-in", "authenticate", "session"]

def setup_driver():
    """Setup Edge WebDriver without using subprocess.Popen."""
    edge_options = Options()
    edge_options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    edge_options.add_argument("--headless")  # Run in headless mode
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver_path = "C:/temp/msedgedriver.exe"  # Ensure this path is correct
    
    # Start WebDriver without using subprocess
    try:
        service = Service(driver_path)
        driver = webdriver.Edge(service=service, options=edge_options)
        return driver
    except WebDriverException as e:
        print(f"Error initializing Edge WebDriver: {e}")
        exit(1)

def login(driver, login_url, username, password):
    """Perform login and return driver session."""
    try:
        driver.get(login_url)
        time.sleep(2)

        if any(keyword in driver.current_url.lower() for keyword in LOGIN_KEYWORDS) or "password" in driver.page_source.lower():
            try:
                user_field = driver.find_element(By.NAME, "userIdLogin")
                pass_field = driver.find_element(By.NAME, "passwordLogin")
            except NoSuchElementException:
                print("Login fields not found.")
                return False
            
            user_field.send_keys(username)
            pass_field.send_keys(password)
            pass_field.send_keys(Keys.RETURN)  # Press Enter
            time.sleep(3)

            if any(keyword in driver.current_url.lower() for keyword in LOGIN_KEYWORDS) or "password" in driver.page_source.lower():
                print("Login failed.")
                return False
        return True
    except TimeoutException:
        print("Timeout error during login.")
        return False
    except Exception as e:
        print(f"Unexpected error during login: {e}")
        return False

def get_all_links(driver, main_url):
    """Extract all hyperlinks from a webpage."""
    try:
        driver.get(main_url)
        time.sleep(2)

        if any(keyword in driver.current_url.lower() for keyword in LOGIN_KEYWORDS):
            return [(main_url, main_url, "Redirected to login page", "Skipped")]

        links = driver.find_elements(By.TAG_NAME, "a")
        result = [(main_url, link.get_attribute("href"), link.text.strip() or "[No Text]", "Pending") for link in links if link.get_attribute("href")]
        return result
    except Exception as e:
        print(f"Error extracting links: {e}")
        return [(main_url, main_url, "Main page inaccessible", "N/A")]

def check_url(driver, data):
    """Check if a link is accessible."""
    main_url, url, anchor_text, _ = data
    if not url:
        return main_url, url, anchor_text, "N/A"
    
    try:
        driver.get(url)
        time.sleep(2)
        
        if any(keyword in driver.current_url.lower() for keyword in LOGIN_KEYWORDS):
            return main_url, url, anchor_text, "Skipped (Login Required)"
        return main_url, url, anchor_text, "Accessible"
    except Exception:
        return main_url, url, anchor_text, "N/A"

def read_main_urls(file_path):
    """Read URLs and credentials from CSV."""
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        return [(row[0], row[1], row[2], row[3], row[4]) for row in reader if len(row) >= 5]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", type=str, help="Username for login")
    parser.add_argument("--password", type=str, help="Password for login")
    parser.add_argument("--broken-only", action="store_true", help="Generate report only for broken links")
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

    checked_links = [check_url(driver, link) for link in all_links]

    if args.broken_only:
        checked_links = [link for link in checked_links if link[3] == "N/A"]

    with open(output_csv, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Main URL", "Link", "Anchor Text", "Status"])
        writer.writerows(checked_links)

    driver.quit()
    print(f"Report generated: {output_csv}")

if __name__ == "__main__":
    main()
