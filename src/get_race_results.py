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
import pandas as pd
import tabula


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
    for event in event_list:
        event_data.append(get_vtyc_dataframe(event))
    return event_data


def get_vtyc_dataframe(url):
    # read_pdf returns a list of dataframes (one for each page)
    # lattice=True is often better for defined table grids
    dfs = tabula.read_pdf(url, pages='all', lattice=False, stream=True)

    # Combine pages if the table spans multiple pages
    full_df = pd.concat(dfs, ignore_index=True)

    # Cleaning steps:
    # 1. Drop rows that are completely empty
    full_df = full_df.dropna(how='all')

    # 2. Rename columns based on the header found in the PDF
    # Typical columns: Rank, Plate, Name/Team, Intermediate, Time, Points
    if len(full_df.columns) >= 6:
        full_df.columns = ['Rank', 'Plate', 'Name_Team', 'Intermediate', 'Time', 'Points']

    return full_df


# Execute and display
df = get_vtyc_dataframe(pdf_url)

# Display the first few rows
print("VTYC Results DataFrame:")
print(df.head(10))


# Optional: Export to CSV
# df.to_csv("vtyc_results.csv", index=False)


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
        for event, event_list in results_database:


    finally:
        driver.quit()

    return results_database


def get_vtyc_dataframe(url):
    # read_pdf returns a list of dataframes (one for each page)
    # lattice=True is often better for defined table grids
    dfs = tabula.read_pdf(url, pages='all', lattice=False, stream=True)

    # Combine pages if the table spans multiple pages
    full_df = pd.concat(dfs, ignore_index=True)

    # Cleaning steps:
    # 1. Drop rows that are completely empty
    full_df = full_df.dropna(how='all')

    # 2. Rename columns based on the header found in the PDF
    # Typical columns: Rank, Plate, Name/Team, Intermediate, Time, Points
    if len(full_df.columns) >= 6:
        full_df.columns = ['Rank', 'Plate', 'Name_Team', 'Intermediate', 'Time', 'Points']

    return full_df


# Execute and display
df = get_vtyc_dataframe(pdf_url)

# Display the first few rows
print("VTYC Results DataFrame:")
print(df.head(10))

# Optional: Export to CSV
# df.to_csv("vtyc_results.csv", index=False)


if __name__ == "__main__":
    data = get_bullitt_timing_data(event_name='VTYC', year=2025)

    print("\n--- Final Results ---")
    print(json.dumps(data, indent=4))