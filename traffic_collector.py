import os
import time
import csv
import hashlib
import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from PIL import Image
from io import BytesIO
from datetime import datetime

# CAMERA
CAMERA_ID = "5d9ddd49766c880017188c94"

BASE_URL = f"https://giaothong.hochiminhcity.gov.vn/render/ImageHandler.ashx?id={CAMERA_ID}"

SAVE_DIR = "images"
CSV_FILE = "metadata.csv"

os.makedirs(SAVE_DIR, exist_ok=True)

session = requests.Session()

retry = Retry(
    total=5,
    connect=5,
    read=5,
    backoff_factor=2,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=frozenset(["GET"])
)

adapter = HTTPAdapter(max_retries=retry)

session.mount("https://", adapter)
session.mount("http://", adapter)

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "vi,en-US;q=0.9",
    "Referer": "https://giaothong.hochiminhcity.gov.vn/"
}

last_hash = None

saved = 0
duplicate = 0
errors = 0

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "time",
            "camera",
            "filename",
            "sha256"
        ])

print("=" * 50)
print("Traffic Collector Started")
print("=" * 50)

while True:

    try:

        timestamp = int(time.time() * 1000)

        url = BASE_URL + "&t=" + str(timestamp)

        response = session.get(
            url,
            headers=headers,
            timeout=(5, 15)
        )

        if response.status_code != 200:

            print(f"HTTP Error: {response.status_code}")
            errors += 1
            continue

        img = response.content

        current_hash = hashlib.sha256(img).hexdigest()

        if current_hash == last_hash:

            duplicate += 1
            print(f"[{datetime.now():%H:%M:%S}] Duplicate")

        else:

            try:

                image = Image.open(BytesIO(img))
                image.verify()

            except Exception:

                print("Invalid Image")
                errors += 1
                continue

            image = Image.open(BytesIO(img))

            now = datetime.now()

            day_folder = os.path.join(SAVE_DIR, now.strftime("%Y-%m-%d"))

            os.makedirs(day_folder, exist_ok=True)

            filename = now.strftime("%Y%m%d_%H%M%S") + ".jpg"

            filepath = os.path.join(day_folder, filename)

            image.save(filepath)

            with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:

                writer = csv.writer(f)

                writer.writerow([
                    datetime.now(),
                    CAMERA_ID,
                    filename,
                    current_hash
                ])

            last_hash = current_hash

            saved += 1

            print(f"[{datetime.now():%H:%M:%S}] Saved -> {filename}")

        print("-" * 50)
        print(f"Saved     : {saved}")
        print(f"Duplicate : {duplicate}")
        print(f"Errors    : {errors}")
        print("-" * 50)

    except KeyboardInterrupt:

        print("\nCollector Stopped")
        break

    except Exception as e:

        errors += 1
        print("Error:", e)

    time.sleep(10)