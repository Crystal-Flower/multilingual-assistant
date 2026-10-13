# This script scrapes faculty information from the Amrita University website.
# It iterates through multiple pages, extracts the name and designation
# of each faculty member, and prints the results.

import requests
from bs4 import BeautifulSoup
import time

def scrape_faculty_info():
    """
    Scrapes faculty data from a series of web pages and prints the results.
    """
    all_faculty = []

    # Define the URLs to scrape. This includes the first page and pages 2 through 8.
    base_url = "https://www.amrita.edu/faculty/?cmp=45"
    urls_to_scrape = [base_url]
    for i in range(2, 9):
        urls_to_scrape.append(f"https://www.amrita.edu/faculty/page/{i}/?cmp=45")

    print("Starting the web scraping process...")

    for url in urls_to_scrape:
        print(f"Scraping data from: {url}")
        try:
            # Use a user-agent to mimic a browser and avoid potential blocking.
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
            # Fetch the HTML content of the page
            response = requests.get(url, headers=headers, timeout=10)
            # Raise an exception if the request was unsuccessful
            response.raise_for_status()

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all the faculty item containers.
            # Based on the sample, these are divs with the class 'fc-item'.
            faculty_items = soup.find_all('div', class_='fc-item')

            if not faculty_items:
                print("No faculty items found on this page. Check the page structure.")

            # Extract the name and designation for each faculty member
            for item in faculty_items:
                name_tag = item.find('h6')
                designation_tag = item.find('p')

                name = name_tag.get_text(strip=True) if name_tag else "Name not found"
                designation = designation_tag.get_text(strip=True) if designation_tag else "Designation not found"

                all_faculty.append({
                    'name': name,
                    'designation': designation
                })

            # Add a short delay to be polite to the server and avoid being blocked.
            time.sleep(1)

        except requests.exceptions.RequestException as e:
            print(f"Error while scraping {url}: {e}")
            continue

    print("\nScraping complete. Displaying results:")
    print("---------------------------------------")

    if not all_faculty:
        print("No faculty information was successfully scraped.")
    else:
        for faculty in all_faculty:
            print(f"Name: {faculty['name']}")
            print(f"Designation: {faculty['designation']}\n")

# Run the main scraping function when the script is executed
if __name__ == "__main__":
    scrape_faculty_info()
