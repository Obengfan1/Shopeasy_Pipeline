import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import time
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL   = "https://books.toscrape.com/"
HEADERS    = {"User-Agent": "Mozilla/5.0 (educational-scraper/1.0)"}
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def make_session():
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(HEADERS)
    return session


def check_robots(session):
    try:
        response = session.get(
            "https://books.toscrape.com/robots.txt", timeout=15, verify=False
        )
        print("=== robots.txt ===")
        print(response.text)
        print("==================")
    except Exception as e:
        print(f"Could not fetch robots.txt: {e}")


def safe_get(session, url):
    time.sleep(1)
    try:
        response = session.get(url, timeout=15, verify=False)
        response.raise_for_status()
        # ✅ Force correct encoding so £ is read as £, not Â£
        response.encoding = "utf-8"
        return response
    except requests.exceptions.SSLError:
        print(f"SSL error on {url} — retrying in 3s...")
        time.sleep(3)
        try:
            response = session.get(url, timeout=20, verify=False)
            response.raise_for_status()
            response.encoding = "utf-8"
            return response
        except Exception as e2:
            print(f"Gave up on {url}: {e2}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return None


def scrape_page(session, url, category="General"):
    response = safe_get(session, url)
    if response is None:
        return []

    soup  = BeautifulSoup(response.text, "lxml")
    books = []

    for article in soup.select("article.product_pod"):
        name        = article.h3.a["title"]
        price_text  = article.select_one(".price_color").text.strip()
        rating_word = article.p["class"][1]
        rating      = RATING_MAP.get(rating_word, 0)

        books.append({
            "name":     name,
            "price":    price_text,
            "rating":   rating,
            "category": category
        })

    return books


def scrape_all():
    session = make_session()
    check_robots(session)
    all_books = []

    home_resp = safe_get(session, BASE_URL)
    if home_resp is None:
        print("Could not load homepage — aborting.")
        return []

    soup           = BeautifulSoup(home_resp.text, "lxml")
    category_links = soup.select("ul.nav-list ul li a")

    for link in category_links:
        category_name = link.text.strip()
        category_url  = BASE_URL + link["href"]
        category_dir  = category_url.rsplit("/", 1)[0] + "/"

        print(f"Scraping category: {category_name}")
        page_url = category_url

        while page_url:
            books = scrape_page(session, page_url, category=category_name)
            all_books.extend(books)

            page_resp = safe_get(session, page_url)
            if page_resp is None:
                break

            page_soup = BeautifulSoup(page_resp.text, "lxml")
            next_btn  = page_soup.select_one("li.next a")
            page_url  = category_dir + next_btn["href"] if next_btn else None

    print(f"\nTotal books scraped: {len(all_books)}")
    return all_books


if __name__ == "__main__":
    books = scrape_all()
    # ✅ ensure_ascii=False preserves £ correctly in the JSON file
    with open("raw_books.json", "w", encoding="utf-8") as f:
        json.dump(books, f, indent=2, ensure_ascii=False)
    print("Saved to raw_books.json")
