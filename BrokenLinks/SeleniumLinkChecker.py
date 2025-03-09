import csv
import time
import random
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
]

LOGIN_KEYWORDS = ["login", "sign-in", "authenticate", "session"]

def setup_driver():
    """Initialize Edge WebDriver with options."""
    options = Options()
    options.add_argument("--headless=new")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    
    return webdriver.Edge(options=options)

def detect_login_page(driver):
    """Detect if the page is a login page."""
    current_url = driver.current_url.lower()
    page_source = driver.page_source.lower()
    return any(keyword in current_url for keyword in LOGIN_KEYWORDS) or "password" in page_source

def login(driver, login_url, username, password):
    """Perform login and maintain session."""
    try:
        driver.get(login_url)
        time.sleep(2)  # Allow time for redirection

        if detect_login_page(driver):
            username_field = driver.find_element(By.NAME, "userIdLogin")
            password_field = driver.find_element(By.NAME, "passwordLogin")

            username_field.send_keys(username)
            password_field.send_keys(password)
            password_field.send_keys(Keys.RETURN)

            time.sleep(3)  # Wait for login processing

            if detect_login_page(driver):
                print("Login failed. Please check credentials.")
                return False
        return True
    except Exception as e:
        print(f"Error during login: {e}")
        return False

def get_all_links(driver, main_url):
    """Extract all hyperlinks from the webpage."""
    try:
        driver.get(main_url)
        time.sleep(2)  # Allow page to load

        if detect_login_page(driver):
            return [(main_url, main_url, "Redirected to login page", "Skipped")]

        links = [(a.get_attribute("href"), a.text.strip() or "[No Text]") for a in driver.find_elements(By.TAG_NAME, "a") if a.get_attribute("href")]
        return [(main_url, link, text, "Pending") for link, text in set(links)]
    except Exception as e:
        return [(main_url, main_url, f"Main page error: {str(e)}", "N/A")]

def check_url(driver, data):
    """Check if a link is accessible and return its status."""
    main_url, url, anchor_text, _ = data
    try:
        driver.get(url)
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        if detect_login_page(driver):
            return main_url, url, anchor_text, "Skipped (Login)"
        
        return main_url, url, anchor_text, "200 OK"
    except Exception as e:
        return main_url, url, anchor_text, f"Error: {str(e)}"

def read_main_urls(file_path):
    """Read main URLs and credentials from CSV."""
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header
        return [(row[0], row[1], row[2], row[3], row[4]) for row in reader if len(row) >= 5]  # (Name, Login URL, Username, Password, Target URL)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", type=str, help="Username for login")
    parser.add_argument("--password", type=str, help="Password for login")
    parser.add_argument("--broken-only", action="store_true", help="Generate report only for broken links (errors)")
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
        checked_links = [link for link in checked_links if "Error" in link[3] or link[3] != "200 OK"]

    with open(output_csv, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Main URL", "Link", "Anchor Text", "Status Code"])
        writer.writerows(checked_links)

    print(f"Report generated: {output_csv}")
    driver.quit()

if __name__ == "__main__":
    main()
