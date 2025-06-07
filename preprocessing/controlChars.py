import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup




# Step 1: Fetch the webpage
url = "https://www.c64-wiki.com/wiki/control_character"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

# Step 2: Locate the first table with class 'wikitable'
table = soup.find("table", class_="wikitable")

# Step 3: Extract headers
headers = [th.get_text(strip=True) for th in table.find_all("th")]

# Step 4: Extract rows
rows = []
for tr in table.find_all("tr")[1:]:  # skip header row
    cols = [td.get_text(separator=" ", strip=True) for td in tr.find_all("td")]
    if cols:
        rows.append(cols)

# Step 5: Create DataFrame and export to CSV
df = pd.DataFrame(rows, columns=headers)
df.to_csv("control_characters.csv", index=False)

print("Saved as control_characters.csv")