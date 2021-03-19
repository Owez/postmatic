import hashlib
import json
import os
import random
import sqlite3
import sys
import time
from pathlib import Path
import praw
import requests
from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

#### CONFIG/SETUP ####

CONFIG_PATH = Path("config.json")
BANNER = """ ____  _____  ___  ____  __  __    __   ____  ____  ___ 
(  _ \(  _  )/ __)(_  _)(  \/  )  /__\ (_  _)(_  _)/ __)
 )___/ )(_)( \__ \  )(   )    (  /(__)\  )(   _)(_( (__ 
(__)  (_____)(___/ (__) (_/\/\_)(__)(__)(__) (____)\___)"""
BANNER_DIV = "=" * 56
MEME_IMG_PATH = os.getcwd() + "/meme.jpg"


class Config:
    """Pulls from config.json"""

    def __init__(self):
        with open(CONFIG_PATH, "r") as json_in:
            _json = json.load(json_in)

            self.insta_username = _json["instagram"]["username"]
            self.insta_password = _json["instagram"]["password"]

            self.reddit_subreddit = _json["reddit"]["subreddit"]
            self.reddit_client_secret = _json["reddit"]["client_secret"]
            self.reddit_client_id = _json["reddit"]["client_id"]

            self.description = _json["description"]
            self.mins_per_upload = _json["mins_per_upload"]


# config/reddit
config = Config()
reddit = praw.Reddit(
    client_id=config.reddit_client_id,
    client_secret=config.reddit_client_secret,
    user_agent=config.description,
)
subreddit = reddit.subreddit(config.reddit_subreddit)

# db
conn = sqlite3.connect("dupes.db")


def new_db():
    """Creates basic tables"""

    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS post(id text PRIMARY KEY, hash text)")
    conn.commit()


class RedditPost:
    """A single reddit post, made from a [praw.Submission]"""

    def __init__(self, post):
        self.id = post.name
        self.name = post.title
        self.img_bytes = self._get_bytes_from_url(post.url)
        self.img_hash = self._get_hash(self.img_bytes)

    def is_duped(self) -> bool:
        """Checks if post is duplicated"""

        c = conn.cursor()

        result = c.execute(
            "SELECT * FROM post WHERE id=? OR hash=?", (self.id, self.img_hash)
        ).fetchall()

        if len(result) != 0:
            return True

        c.execute("INSERT INTO post(id, hash) VALUES (?, ?)", (self.id, self.img_hash))
        conn.commit()

        return False

    def save_to_file(self, path: Path):
        """Saves img_bytes to given path, should be .jpg/jpeg ending"""

        with open(path, "wb+") as f:
            f.write(self.img_bytes)

    def _get_bytes_from_url(self, url: str) -> bytes:
        """Gets image hash from url and returns it in [bytes]"""

        return requests.get(url).content

    def _get_hash(self, img_bytes: bytes) -> str:
        """Gets sha256 hash from bytes and returns [str] of it"""

        return hashlib.sha256(img_bytes).digest()


#### SELENIUM ####


def insta_login(wd: webdriver):
    wd.get("https://www.instagram.com/accounts/login/?source=auth_switcher")
    time.sleep(5)

    username = config.insta_username
    password = config.insta_password

    wd.find_element_by_name("username").send_keys(username)
    wd.find_element_by_name("password").send_keys(password)
    wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    wd.find_element_by_xpath(
        '//*[@id="react-root"]/section/main/article/div/div/div/form/div[7]/button'
    )
    time.sleep(5)
    wd.find_element_by_css_selector('button[type="submit"').click()
    time.sleep(5)
    wd.find_element_by_xpath(
        '//*[@id="react-root"]/section/main/div/div/div/button'
    ).click()
    time.sleep(5)
    wd.find_element_by_xpath("/html/body/div[4]/div/div/div/div[3]/button[2]").click()
    print("Successfully logged into instagram!")


def insta_add_post(post: RedditPost, wd: webdriver):
    """Uploads a reddit post to instagram"""
    WebDriverWait(wd, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "/html/body/div[1]/section/nav[2]/div/div/div[2]/div/div/div[3]")
        )
    ).click()
    WebDriverWait(wd, 10).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/form/input"))
    ).send_keys(MEME_IMG_PATH)
    time.sleep(5)
    wd.find_element_by_class_name("pHnkA").click()
    time.sleep(1.5)
    wd.find_element_by_xpath(
        "/html/body/div[1]/section/div[1]/header/div/div[2]/button"
    ).click()
    time.sleep(5)

    caption = (
        post.name
        + "\n----------------\n\n\n#meme #memes #funny #dankmemes #memesdaily #lol #dank #follow #humor #like #dankmeme #lmao #love #anime #edgymemes #comedy #ol #dailymemes #instagram #offensivememes #fun #fortnite #tiktok #funnymeme #memer #relatable #relatablememes"
    )

    if len(caption) > 2200:
        caption = (
            "Caption this!"
            + "\n----------------\n\n\n#meme #memes #funny #dankmemes #memesdaily #dank #funnymemes #lol #follow #humor #like #dankmeme #lmao #love #anime #edgymemes #comedy #ol #dailymemes #instagram #offensivememes #fun #fortnite #tiktok #funnymeme #memer #relatable #relatablememes"
        )

    wd.find_element_by_class_name("_472V_").send_keys(caption)
    time.sleep(1.5)
    wd.find_element_by_class_name("UP43G").click()
    time.sleep(3)
    wd.find_element_by_xpath("/html/body/div[4]/div/div/div[3]/button[2]").click()
    wd.quit()
    print("Successfully uploaded")


def open_browser() -> webdriver:
    """Opens a new webdriver instance"""

    options = Options()
    mobileEmulation = {"deviceName": "Nexus 5"}
    options.add_experimental_option("mobileEmulation", mobileEmulation)
    wd = webdriver.Chrome(options=options)
    wd.maximize_window()
    action_chains = ActionChains(wd)


#### MAIN ####


def shutdown(msg: str = "No reason given"):
    """Quits gracefully"""

    print(f"Error: {msg}!", file=sys.stderr)
    sys.exit(1)


def fetch_reddit(amount: int = 10):
    """Gets x best submissions from given [Config.subreddit]"""

    return subreddit.random_rising(limit=amount)


def reddit_credential_check():
    """Does double-duty by checking if given subreddit is over 18 and ensures
    reddit login credentials are valid"""

    try:
        if subreddit.over18:
            shutdown("Subreddit is over 18 and is not allowed on Instagram")
    except:
        shutdown("Login credentials for Reddit are invalid")


def smart_wait():
    """Simple context-sensitive wait message and actual timer based on
    [Config.mins_per_upload]. To be used whenever you need to wait to let user
    know"""

    if config.mins_per_upload == 1:
        print(f"Waiting {config.mins_per_upload} minute..")
    else:
        print(f"Waiting {config.mins_per_upload} minutes..")

    time.sleep(config.mins_per_upload * 60)


def main_loop():
    """Starts main reddit-based loop of program"""

    wd = open_browser()

    while True:
        print("Fetching new batch of posts..")

        posts = fetch_reddit()

        for post in posts:
            reddit_post = RedditPost(post)

            post_dsq = (
                post.url is None
                or post.score < 25
                or post.over_18
                or post.stickied
                or not post.url.endswith(".jpg")
            )  # basic submission/post issues that are disqualified

            if post_dsq or reddit_post.is_duped():
                continue

            reddit_post.save_to_file(MEME_IMG_PATH)  # dump file

            meme_image = Image.open(MEME_IMG_PATH)
            width, height = meme_image.size
            aspect_ratio = width / height

            if aspect_ratio <= 0.80 and aspect_ratio >= 1.90:
                continue

            print(f"Adding '{post.title}'..")

            try:
                insta_login(wd)
                insta_add_post(reddit_post, wd)  # upload to insta
            except NoSuchElementException:
                pass

            smart_wait()

        time.sleep(5)


#### STARTUP ####

if __name__ == "__main__":
    print(f"{BANNER}\n{BANNER_DIV}")
    print(f"Used as: '{config.description}'")

    print("Generating db if it is empty..")
    new_db()

    print("Logging into reddit..")
    reddit_credential_check()  # check nsfw + credentials

    print("Logging into instagram..")

    main_loop()  # enter main upload loop
