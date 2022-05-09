import os
import string
import re
import pandas as pd
import requests
import numpy as np
from joblib import Parallel, delayed
from Fishy import fish_scraper

image_folder = "d://fish_scraper/"
wikiurl = "https://en.wikipedia.org/wiki/List_of_freshwater_aquarium_fish_species"
table_class = "sortable"
response = requests.get(wikiurl)
soup = bs(response.text, "html.parser")
fish_tables = soup.findAll("table", {"class": table_class})
all_tables = pd.read_html(str(fish_tables))

full_df = pd.DataFrame(columns=["Common name", "Taxonomy"])

for table in all_tables:
    cols = table.columns.tolist()
    if "Common name" not in cols:
        continue
    t = table[["Common name", "Taxonomy"]]
    full_df = full_df.append(t, ignore_index=True)


def clean_string(fish_str):
    pattern = r"[" + string.punctuation + "]"
    fish_str = re.sub(pattern, "", fish_str)
    fish_str.replace(" ", "-")
    return fish_str


full_df["Taxonomy"] = full_df["Taxonomy"].apply(lambda x: clean_string(x))

if not os.path.exists("data"):
    os.makedirs("data")

full_df.to_csv("data/Fish_list.csv", index=False)


def get_fish(fish, image_folder):
    f = fish_scraper(
        fish,
        image_folder,
        headless=False,
        num_images=200,
        max_res=(1400, 1200),
        export_urls=True,
    )
    f.run()


Parallel(n_jobs=8)(
    delayed(get_fish)(fish, image_folder) for fish in full_df["Taxonomy"]
)
