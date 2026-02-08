import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import pandas as pd
from pathlib import Path
import camelot


def get_rendered_soup(driver, url, wait_condition):
    """Navigates to a URL and waits for a specific element to load."""
    driver.get(url)
    try:
        # Wait up to 10 seconds for the expected element (e.g., an <a> tag)
        WebDriverWait(driver, 10).until(wait_condition)
        # Brief sleep to ensure Ember finishes rendering the list
        time.sleep(1)
        return BeautifulSoup(driver.page_source, 'html.parser')
    except Exception as e:
        print(f"Timeout or error loading {url}: {e}")
        return None


def get_event_data(event_list):
    event_data = []
    for category in event_list:
        category_data = get_vtyc_dataframe(category)
        event_data.append(category_data)
    return event_data


def get_vtyc_dataframe(url):
    # read_pdf returns a list of dataframes (one for each page)
    # lattice=True is often better for defined table grids
    # dfs = tabula.read_pdf(url, pages='all', lattice=False, stream=True)

    filename = url.split('/')[-1]
    response = requests.get(url)
    response.raise_for_status()

    # Get the directory where the current script file is located
    script_dir = Path(__file__).parent.parent
    save_path = script_dir / f"data/{filename}"

    with open(save_path, "wb") as f:
        f.write(response.content)

    # # Read the PDF using Camelot (Lattice is default, use 'stream' if needed)
    # tables = camelot.read_pdf(filename, pages='1', flavor='lattice')
    #
    # # Combine pages if the table spans multiple pages
    # full_df = pd.concat(dfs, ignore_index=True)
    #
    # # Cleaning steps:
    # # 1. Drop rows that are completely empty
    # full_df = full_df.dropna(how='all')
    #
    # # 2. Rename columns based on the header found in the PDF
    # # Typical columns: Rank, Plate, Name/Team, Intermediate, Time, Points
    # if len(full_df.columns) >= 6:
    #     full_df.columns = ['Rank', 'Plate', 'Name_Team', 'Intermediate', 'Time', 'Points']
    #
    # print("VTYC Results DataFrame:")
    # print(full_df.head(10))
    #
    # # Optional: Export to CSV
    # # df.to_csv("vtyc_results.csv", index=False)
    #
    # return full_df



def get_bullit_timing_data(event_name, year):
    base_url = "https://www.bullitttiming.com"
    events_url = f"{base_url}/events"

    # Configure Headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    results_database = {}

    try:
        print("Accessing main events page...")
        # Step 1: Get main events page and wait for links to appear
        main_soup = get_rendered_soup(driver, events_url, EC.presence_of_element_located((By.TAG_NAME, "a")))

        if not main_soup:
            return {}

        # Step 2: Filter for VTYC events
        events = []
        for a in main_soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True)
            if event_name.lower() in href.lower() and str(year) in href:
                full_url = urljoin(base_url, href)
                events.append((text, full_url))

        print(f"Found {len(events)} {event_name} events in {year}. Identifying results...")

        # Step 3: Visit each event page
        for name, link in events:
            print(f"  Evaluating categories for: {name}")

            event_soup = get_rendered_soup(driver, link, EC.presence_of_element_located((By.TAG_NAME, "a")))

            if event_soup:
                cat_links = []
                for a in event_soup.find_all('a', href=True):
                    c_href = a['href']
                    c_text = a.get_text(strip=True)

                    if "cat" in c_href.lower() or "cat" in c_text.lower():
                        cat_links.append(urljoin(link, c_href))

                # Store in nested dictionary
                results_database[name] = list(set(cat_links))

        # Step 4: Extract data from each event
        results = {}

        for event, event_list in results_database.items():
            try:
                print(f'gathering results for {event} ...')
                results[event] = get_event_data(event_list)
            except Exception as e:
                print(f'error: {e}')


    finally:
        driver.quit()

    return results_database


# def get_vtyc_dataframe(url):
#     # read_pdf returns a list of dataframes (one for each page)
#     # lattice=True is often better for defined table grids
#     print(f'reading {url} ...')
#     dfs = tabula.read_pdf(url, pages='all', lattice=False, stream=True)
#
#     # Combine pages if the table spans multiple pages
#     full_df = pd.concat(dfs, ignore_index=True)
#
#     # Cleaning steps:
#     # 1. Drop rows that are completely empty
#     full_df = full_df.dropna(how='all')
#
#     # 2. Rename columns based on the header found in the PDF
#     # Typical columns: Rank, Plate, Name/Team, Intermediate, Time, Points
#     if len(full_df.columns) >= 6:
#         full_df.columns = ['Rank', 'Plate', 'Name_Team', 'Intermediate', 'Time', 'Points']
#
#     return full_df


if __name__ == "__main__":
    data = get_bullit_timing_data(event_name='VTYC', year=2025)

    print("\n--- Final Results ---")
    print(json.dumps(data, indent=4))