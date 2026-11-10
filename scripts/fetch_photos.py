"""
Identimush v1 photo fetcher (GBIF).

Downloads CC-licensed North American mushroom photos for each species
and writes photos/photos.json with credits for every image.

Run:  python fetch_photos.py
Needs: Python 3.8+ (no extra packages)
"""

import json
import os
import time
import urllib.parse
import urllib.request

# ---- Settings -------------------------------------------------------------
PHOTOS_PER_SPECIES = 6
ALLOW_NONCOMMERCIAL = False   # True = also accept CC BY-NC photos
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "photos")
API = "https://api.gbif.org/v1"

SPECIES = [
    "Agaricus campestris",
    "Amanita bisporigera",
    "Cantharellus cibarius",
    "Omphalotus illudens",
    "Morchella americana",
    "Gyromitra esculenta",
    "Chlorophyllum rhacodes",
    "Chlorophyllum molybdites",
    "Armillaria mellea",
    "Galerina marginata",
    "Boletus edulis",
    "Tylopilus felleus",
    "Amanita muscaria",
    "Amanita phalloides",
    "Laetiporus sulphureus",
    "Grifola frondosa",
    "Calvatia gigantea",
    "Pleurotus ostreatus",
    "Hericium erinaceus",
]

HEADERS = {"User-Agent": "Identimush/0.1 (educational mushroom ID game)"}


# ---- Helpers --------------------------------------------------------------
def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def slug(name):
    return name.lower().replace(" ", "-")


def licence_ok(licence):
    """Accept CC0, CC BY, CC BY-SA. Reject no-derivatives. NC optional."""
    lic = (licence or "").lower()
    if not lic or "nd" in lic.split("/"):
        return False
    if "-nd" in lic or "by-nd" in lic:
        return False
    if "nc" in lic:
        return ALLOW_NONCOMMERCIAL
    return "publicdomain" in lic or "cc0" in lic or "/by" in lic or "cc_by" in lic


def smaller_url(url):
    """Ask the source for a mid-size image instead of the full original."""
    if "inaturalist" in url:
        return url.replace("/original.", "/medium.")
    if "mushroomobserver" in url:
        return url.replace("/orig/", "/640/")
    return url


def taxon_key(name):
    m = get_json(f"{API}/species/match?name={urllib.parse.quote(name)}")
    if m.get("matchType") == "NONE":
        return None
    return m.get("acceptedUsageKey") or m.get("usageKey")


# ---- Main -----------------------------------------------------------------
def fetch_species(name):
    key = taxon_key(name)
    if not key:
        print(f"  ! No GBIF match for {name}")
        return []

    params = urllib.parse.urlencode({
        "taxonKey": key,
        "mediaType": "StillImage",
        "continent": "NORTH_AMERICA",
        "limit": 100,
    })
    results = get_json(f"{API}/occurrence/search?{params}")["results"]

    folder = os.path.join(OUT_DIR, slug(name))
    os.makedirs(folder, exist_ok=True)
    photos, seen = [], set()

    for occ in results:
        for media in occ.get("media", []):
            if len(photos) >= PHOTOS_PER_SPECIES:
                return photos
            url = media.get("identifier")
            if not url or url in seen or not licence_ok(media.get("license")):
                continue
            seen.add(url)

            filename = f"{len(photos) + 1}.jpg"
            path = os.path.join(folder, filename)
            try:
                req = urllib.request.Request(smaller_url(url), headers=HEADERS)
                with urllib.request.urlopen(req, timeout=30) as r, open(path, "wb") as f:
                    f.write(r.read())
            except Exception as e:
                print(f"  ! Download failed: {e}")
                continue

            photos.append({
                "file": f"{slug(name)}/{filename}",
                "creator": media.get("creator") or media.get("rightsHolder") or "Unknown",
                "license": media.get("license"),
                "source": f"https://www.gbif.org/occurrence/{occ['key']}",
            })
            time.sleep(1)  # be polite to image hosts
            break  # one photo per observation = more variety

    return photos


def main():
    manifest = {}
    for name in SPECIES:
        print(f"{name}...")
        photos = fetch_species(name)
        manifest[slug(name)] = {"latin": name, "photos": photos}
        print(f"  {len(photos)} photos")
        time.sleep(1)

    with open(os.path.join(OUT_DIR, "photos.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nDone. Credits saved to {OUT_DIR}/photos.json")


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    main()
