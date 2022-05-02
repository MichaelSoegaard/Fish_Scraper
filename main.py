import os
import pandas as pd
import requests
import numpy as np
from joblib import Parallel, delayed
from bs4 import BeautifulSoup as bs
from Fishy import fish_scraper

image_folder = "d://fish_scraper/"
wikiurl = "https://en.wikipedia.org/wiki/List_of_freshwater_aquarium_fish_species"
table_class = "sortable"
response = requests.get(wikiurl)
soup = bs(response.text, "html.parser")
fishy = soup.findAll("table", {"class": table_class})
all_tables = pd.read_html(str(fish_tables))

full_df = pd.DataFrame(columns=["Common name", "Taxonomy"])

for table in all_tables:
    cols = table.columns.tolist()
    if "Common name" not in cols:
        continue
    t = table[["Common name", "Taxonomy"]]
    full_df = full_df.append(t, ignore_index=True)

full_df["Taxonomy"] = full_df["Taxonomy"].apply(lambda x: x.replace(" ", "-"))

if not os.path.exists("data"):
    os.makedirs("data")

full_df.to_csv("data/Fish_list.csv", index=False)


def get_fish(fish, image_folder):
    f = fish_scraper(
        fish, image_folder, headless=False, num_images=200, max_res=(1400, 1200)
    )
    f.run()


Parallel(n_jobs=6)(
    delayed(get_fish)(fish, image_folder) for fish in full_df["Taxonomy"]
)
