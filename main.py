from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from PIL import Image
import requests
import sqlite3 as sq
import time
import io
import asyncio
import aiosqlite

"""
Parser data for dataset from: https://lexica.art/
"""

options = webdriver.ChromeOptions()
options.add_argument("user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--headless")

driver = webdriver.Chrome(options=options)

driver.maximize_window()
driver.get("https://lexica.art/")


def read_img(name):
    with open(name, 'rb') as f:
        return f.read()


async def load_to_db(img, ant):
    async with aiosqlite.connect("data.db") as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS images (img BLOB, annotation TEXT)""")
        await db.execute(f"""INSERT INTO images VALUES (?, ?)""", (img, ant))
        await db.commit()


def main():
    while True:
        try:
            image_count = int(input("How many images with descriptions do you need?: "))
            break
        except Exception as ex:
            continue

    count = 0

    while True:
        try:
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            time.sleep(0.5)
        except Exception as ex:
            print("Failed loading")
        else:
            try:
                for i in driver.find_elements(By.TAG_NAME, 'a'):
                    if "prompt" in i.get_attribute("href"):
                        url = i.get_attribute("href")

                        if len(driver.window_handles) < 2:
                            driver.switch_to.new_window()

                        driver.switch_to.window(driver.window_handles[1])
                        driver.get(url)

                        image_url = driver.find_element(By.TAG_NAME, "img").get_attribute("src")
                        ant_list = [i.text for i in driver.find_elements(By.TAG_NAME, 'a')]
                        Image.open(io.BytesIO(requests.get(image_url).content)).resize((100, 100)).save("img.png")

                        img = sq.Binary(read_img("img.png"))
                        ant = ''.join(ant_list).replace("HomeGenerateHistoryLikesAccount", '')

                        asyncio.run(load_to_db(img, ant))

                        count += 1
                        driver.switch_to.window(driver.window_handles[0])

                        print(f"{count} / {image_count}")
                        if count == image_count:
                            print("Done")
                            exit()

            except Exception as ex:
                print("Error during getting data")
                driver.switch_to.window(driver.window_handles[0])


if __name__ == "__main__":
    main()
