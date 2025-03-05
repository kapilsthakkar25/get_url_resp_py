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

def get_all_links(main_url):
    """Extract all hyperlinks and their anchor text from the given webpage."""
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        response = requests.get(main_url, headers=headers, timeout=10, allow_redirects=True)
        if response.status_code != 200:
            return [(main_url, main_url, "Main page inaccessible", response.status_code)]

        soup = BeautifulSoup(response.text, "html.parser")
        links = [(urljoin(main_url, a['href']), a.get_text(strip=True) or "[No Text]") for a in soup.find_all("a", href=True)]
        return [(main_url, link, text, "Pending") for link, text in set(links)]
    except requests.RequestException:
        return [(main_url, main_url, "Main page inaccessible", "N/A")]

def check_url(data):
    """Check if a link is accessible and return its status code."""
    main_url, url, anchor_text, _ = data
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        response = requests.head(url, headers=headers, allow_redirects=True, timeout=10)
        
        if response.status_code >= 400:
            response = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
        
        return main_url, url, anchor_text, response.status_code
    except requests.RequestException:
        return main_url, url, anchor_text, "N/A"

def read_main_urls(file_path):
    """Read main URLs from CSV."""
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header
        return [(row[0], row[1]) for row in reader if len(row) >= 2]  # (Name, URL)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--broken-only", action="store_true", help="Generate report only for broken links (status 300-500)")
    args = parser.parse_args()
    
    input_csv = "urls.csv"
    output_csv = "broken_links_report.csv" if args.broken_only else "all_links_report.csv"
    main_urls = read_main_urls(input_csv)
    
    all_links = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(get_all_links, url_data[1]): url_data[1] for url_data in main_urls}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Extracting Links"):
            all_links.extend(future.result())
    
    checked_links = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_url, link): link for link in all_links}
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
