import os
import json
import time
import re
import pandas as pd
from bs4 import BeautifulSoup as bs
import requests
from requests.exceptions import ConnectionError, ConnectTimeout
from random import randint
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# from patch import webdriver_executable
import mimetypes
from joblib import Parallel, delayed
import urllib3
from tqdm import tqdm

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class fish_scraper:
    def __init__(
        self,
        fish,
        folder_path,
        webdriver_path="./webdriver/chromedriver.exe",
        num_images=100,
        headless=True,
        min_res=(100, 100),
        max_res=(1920, 1080),
        export_urls=False,
    ):

        # assert fish != None, print("[ERROR] You need to specify a fish to search for!")
        # assert (
        #     folder_path != None
        # ), "[ERROR] You need to specify a folderpath for the images to be stored at!"
        # assert (
        #     type(num_images) != int
        # ), "[ERROR] Number of images must be integer value."

        fish_path = os.path.join(folder_path, fish)
        if not os.path.exists(fish_path):
            print("[INFO] Image path not found. Creating a new folder.")
            os.makedirs(fish_path)

        options = Options()
        if headless:
            options.add_argument("--headless")
        driver = webdriver.Chrome(webdriver_path, chrome_options=options)
        driver.set_window_size(1400, 1050)
        driver.get("https://www.google.com")

        self.driver = driver
        self.url = (
            "https://www.google.com/search?q=%s&source=lnms&tbm=isch&sa=X&ved=2ahUKEwie44_AnqLpAhUhBWMBHUFGD90Q_AUoAXoECBUQAw&biw=1920&bih=947"
            % (fish)
        )
        self.headless = headless
        self.folder_path = folder_path
        self.fish_path = fish_path
        self.fish = fish
        self.num_images = 200
        self.headless = headless
        self.min_res = (100, 100)
        self.max_res = (1400, 1200)
        self.json_filepath = fish_path = os.path.join(folder_path, "fish_img_urls.json")
        self.urls = []

    def dl_image(self, url):
        """
        Download images from passed in urls.
        Only files of filetype .png and .jpg are downloaded to
        the passed in folder path
        """

        fileid = randint(10000, 99999)
        r = requests.get(url, allow_redirects=True, verify=False)
        content_type = r.headers["content-type"]
        extension = mimetypes.guess_extension(content_type)
        if extension == None:
            extension = ".jpg"
        if extension in [".jpg", ".jpeg", ".png"]:
            open(
                f"{self.fish_path}/{self.fish[:3]}{str(fileid)}{extension}",
                "wb",
            ).write(r.content)

    def write_json(self):
        file_exists = os.path.exists(self.json_filepath)
        temp_dict = {self.fish: self.urls}

        if not file_exists:
            with open(self.json_filepath, "w") as f:
                json.dump(temp_dict, f)
                f.close()
        else:
            with open(self.json_filepath) as f:
                urls_dict = json.load(f)

            urls_dict.update(temp_dict)

            with open(self.json_filepath, "w") as f:
                json.dump(urls_dict, f)
                f.close()

    def scrape_fishbase(self):
        def get_url(image):
            url = image["src"]
            url = url.replace("%2F", "/")
            url = "https://www.fishbase.de" + url[2:]
            return url

        html_page = requests.get(f"http://fishbase.de/summary/{self.fish}")
        soup = bs(html_page.content, "html.parser")
        txt = soup.find(title="English")
        if txt == None:
            return
        # txt = soup.find_all("a", href=True, class="slabel8")
        fish_id = re.search("[0-9]+", str(txt))[0]

        html_page = requests.get(
            f"https://www.fishbase.de/photos/thumbnailssummary.php?ID={fish_id}"
        )
        soup = bs(html_page.content, "html.parser")
        image_urls = soup.find_all("img", width="300")
        self.urls = [get_url(image) for image in image_urls]
        # self.urls = list(set(urls))
        # [self.dl_image(url) for url in urls]
        print(f"Fishbase done scraping for {self.fish}")

    def scrape_google(self):
        """
        This function search and return a list of image urls based on the search key.
        Example:
                                                                        google_image_scraper = GoogleImageScraper("webdriver_path","image_path","fish",number_of_photos)
                                                                        image_urls = google_image_scraper.find_image_urls()

        """
        print("[INFO] Scraping for image link... Please wait.")
        # image_urls = []
        count = 0
        missed_count = 0
        self.driver.get(self.url)
        time.sleep(3)
        indx = 1
        while self.num_images > count:
            imgurl = self.driver.find_element(
                By.XPATH,
                '//*[@id="islrg"]/div[1]/div[%s]/a[1]/div[1]/img' % (str(indx)),
            )
            try:
                # find and click image
                # imgurl get
                imgurl.click()
                missed_count = 0
            except Exception:
                print(f"[-] Unable to click this photo. {imgurl}")
                missed_count = missed_count + 1
                if missed_count > 10:
                    print("[INFO] No more photos.")
                    break

            try:
                # select image from the popup
                time.sleep(2)
                class_names = ["n3VNCb"]  # ["v4dQwb"] #
                images = [
                    self.driver.find_elements(by=By.CLASS_NAME, value=class_name)
                    for class_name in class_names
                    if len(
                        self.driver.find_elements(by=By.CLASS_NAME, value=class_name)
                    )
                    != 0
                ][0]
                # only download images that starts with http
                for image in images:
                    # only download images that starts with http
                    src_link = image.get_attribute("src")
                    if ("http" in src_link) and (not "encrypted" in src_link):
                        print("[INFO] %d. %s" % (count, src_link))
                        self.urls.append(src_link)
                        count += 1
                        break
            except Exception:
                print("[INFO] Unable to get link")

            try:
                # scroll page to load next image
                if count % 3 == 0:
                    self.driver.execute_script(
                        "window.scrollTo(0, " + str(indx * 60) + ");"
                    )
                element = self.driver.find_element(
                    by=By.CLASS_NAME, value="lxa62b.MIdC8d.jwwPNd"
                )
                element.click()
                print("[INFO] Loading more photos")
                time.sleep(3)
            except Exception:
                time.sleep(1)
            indx += 1

        self.driver.quit()
        print("[INFO] Google search ended")
        # [self.dl_image(url) for url in image_urls]
        # print(f"[INFO] Google done downloading images for {self.fish}")

    def run(self):
        print(f"{self.fish} fetching initiated...")
        try:
            self.scrape_fishbase()
        except ConnectTimeout as e:
            print("Fishbase unresponsive. Ignoring", e)
        self.scrape_google()
        self.urls = list(set(self.urls))
        self.write_json()
        [self.dl_image(url) for url in self.urls]


if __name__ == "__main__":
    fish_scraper().run()
