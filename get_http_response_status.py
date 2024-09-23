import csv
import urllib.request
import urllib.error
import ssl
from datetime import datetime

# Input file path
input_csv = 'url_lists.csv'

# Create output file with date stamp
date_stamp = datetime.now().strftime('%Y%m%d')
output_csv = f'results_{date_stamp}.csv'

# Create an unverified SSL context (similar to verify=False in requests)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Open the input CSV and read the URLs and names
with open(input_csv, mode='r') as infile, open(output_csv, mode='w', newline='') as outfile:
    reader = csv.DictReader(infile)
    fieldnames = ['Date', 'Name', 'URL', 'Status Code', 'Results']
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    
    # Write the header to the output file
    writer.writeheader()

    # Iterate over the input rows
    for row in reader:
        name = row['Name']
        url = row['URL']
        
        try:
            # Perform the request with SSL verification disabled
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, context=ssl_context) as response:
                status_code = response.getcode()
                results = 'Pass'
        except urllib.error.URLError as e:
            if isinstance(e.reason, ssl.SSLError):
                status_code = 'N/A'
                results = 'SSL Failed'
            else:
                status_code = 'Error'
                results = str(e.reason)
        except Exception as e:
            status_code = 'Error'
            results = str(e)
        
        # Print the limited result to the screen
        print(f"Name: {name}, Status Code: {status_code}")
        
        # Write detailed results with the current date to both output and central log files
        result_row = {'Date': date_stamp, 'Name': name, 'URL': url, 'Status Code': status_code, 'Results': results}
        writer.writerow(result_row)

print(f'Output file created here: {output_csv}')
