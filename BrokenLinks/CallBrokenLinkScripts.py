import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import argparse
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
]

LOGIN_KEYWORDS = ["login", "sign-in", "authenticate", "session"]

def detect_login_page(response):
    """Detect if the response page is a login page."""
    return any(keyword in response.url.lower() for keyword in LOGIN_KEYWORDS) or "password" in response.text.lower()

def login(session, login_url, username, password):
    """Perform login and maintain session."""
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        response = session.get(login_url, headers=headers, timeout=10, verify=False)
        soup = BeautifulSoup(response.text, "html.parser")
        
        form = soup.find("form")
        if not form:
            return False
        
        login_data = {tag.get("name"): tag.get("value", "") for tag in form.find_all("input")}
        login_data.update({"username": username, "password": password})
        
        post_url = urljoin(login_url, form.get("action", login_url))
        session.post(post_url, data=login_data, headers=headers, timeout=10, verify=False)
        return True
    except requests.RequestException:
        return False

def get_all_links(session, main_url):
    """Extract all hyperlinks and their anchor text from the given webpage."""
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        response = session.get(main_url, headers=headers, timeout=10, allow_redirects=True, verify=False)
        
        if detect_login_page(response):
            return [(main_url, main_url, "Redirected to login page", "Skipped")]
        
        if response.status_code != 200:
            return [(main_url, main_url, "Main page inaccessible", response.status_code)]

        soup = BeautifulSoup(response.text, "html.parser")
        links = [(urljoin(main_url, a['href']), a.get_text(strip=True) or "[No Text]") for a in soup.find_all("a", href=True)]
        return [(main_url, link, text, "Pending") for link, text in set(links)]
    except requests.RequestException:
        return [(main_url, main_url, "Main page inaccessible", "N/A")]

def check_url(session, data):
    """Check if a link is accessible and return its status code."""
    main_url, url, anchor_text, _ = data
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        response = session.head(url, headers=headers, allow_redirects=True, timeout=10, verify=False)
        
        if detect_login_page(response):
            return main_url, url, anchor_text, "Skipped (Login)"
        
        if response.status_code >= 400:
            response = session.get(url, headers=headers, allow_redirects=True, timeout=10, verify=False)
        
        return main_url, url, anchor_text, response.status_code
    except requests.RequestException:
        return main_url, url, anchor_text, "N/A"

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
    parser.add_argument("--broken-only", action="store_true", help="Generate report only for broken links (status 300-500)")
    args = parser.parse_args()
    
    input_csv = "urls.csv"
    output_csv = "broken_links_report.csv" if args.broken_only else "all_links_report.csv"
    main_data = read_main_urls(input_csv)
    
    all_links = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        session = requests.Session()
        futures = {executor.submit(get_all_links, session, data[4]): data[4] for data in main_data}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Extracting Links"):
            all_links.extend(future.result())
    
    checked_links = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        session = requests.Session()
        futures = {executor.submit(check_url, session, link): link for link in all_links}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Checking Links"):
            checked_links.append(future.result())
    
    if args.broken_only:
        checked_links = [link for link in checked_links if isinstance(link[3], int) and 300 <= link[3] <= 500]
    
    with open(output_csv, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Main URL", "Link", "Anchor Text", "Status Code"])
        writer.writerows(checked_links)
    
    print(f"Report generated: {output_csv}")

if __name__ == "__main__":
    main()
