"""
Identimush v1 photo fetcher (GBIF).

Downloads CC-licensed North American mushroom photos for each species
and writes photos/photos.json with credits for every image.

Run:  python fetch_photos.py                    (all species)
      python fetch_photos.py "Agaricus augustus"  (just these)
Existing photos are kept; each species is topped up to PHOTOS_PER_SPECIES.

To reject a photo, delete its file and rerun. The script notices it's gone,
adds its observation to photos/skip.json so it's never downloaded again,
and fetches a replacement. You can also edit skip.json by hand.
Needs: Python 3.8+ (no extra packages)
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request

# ---- Settings -------------------------------------------------------------
PHOTOS_PER_SPECIES = 10
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
    "Pleurocybella porrigens",
    "Hypomyces lactifluorum",
    "Agaricus xanthodermus",
    "Agaricus arvensis",
    "Agaricus augustus",
    "Psilocybe cubensis",
    "Psilocybe cyanescens",
    "Psilocybe semilanceata",
    "Pholiotina rugosa",
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
def occurrences(key, max_results=500):
    """Yield North American occurrences with images, 100 per page."""
    for offset in range(0, max_results, 100):
        params = urllib.parse.urlencode({
            "taxonKey": key,
            "mediaType": "StillImage",
            "continent": "NORTH_AMERICA",
            "limit": 100,
            "offset": offset,
        })
        page = get_json(f"{API}/occurrence/search?{params}")
        yield from page["results"]
        if page.get("endOfRecords"):
            return


def fetch_species(name, photos, skip=()):
    """Top up `photos` (existing manifest entries) to PHOTOS_PER_SPECIES.

    Existing photos are kept; observations already used or in `skip`
    (GBIF occurrence URLs) are passed over.
    """
    photos = list(photos)
    if len(photos) >= PHOTOS_PER_SPECIES:
        return photos

    key = taxon_key(name)
    if not key:
        print(f"  ! No GBIF match for {name}")
        return photos

    folder = os.path.join(OUT_DIR, slug(name))
    os.makedirs(folder, exist_ok=True)
    used = {p["source"] for p in photos} | set(skip)
    next_num = max([int(os.path.splitext(os.path.basename(p["file"]))[0]) for p in photos] + [0]) + 1

    for occ in occurrences(key):
        if len(photos) >= PHOTOS_PER_SPECIES:
            break
        source = f"https://www.gbif.org/occurrence/{occ['key']}"
        if source in used:
            continue
        for media in occ.get("media", []):
            url = media.get("identifier")
            if not url or not licence_ok(media.get("license")):
                continue

            filename = f"{next_num}.jpg"
            path = os.path.join(folder, filename)
            try:
                req = urllib.request.Request(smaller_url(url), headers=HEADERS)
                with urllib.request.urlopen(req, timeout=30) as r, open(path, "wb") as f:
                    f.write(r.read())
            except Exception as e:
                print(f"  ! Download failed: {e}")
                continue

            next_num += 1
            used.add(source)
            photos.append({
                "file": f"{slug(name)}/{filename}",
                "creator": media.get("creator") or media.get("rightsHolder") or "Unknown",
                "license": media.get("license"),
                "source": source,
            })
            time.sleep(1)  # be polite to image hosts
            break  # one photo per observation = more variety

    return photos


def main(names):
    """Top up the given species, or all of SPECIES if none are given.

    Photos already in photos.json are kept. Photos whose file was deleted
    are added to skip.json and replaced.
    """
    manifest_path = os.path.join(OUT_DIR, "photos.json")
    skip_path = os.path.join(OUT_DIR, "skip.json")
    manifest, skip = {}, {}
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)
    if os.path.exists(skip_path):
        with open(skip_path) as f:
            skip = json.load(f)

    for name in names or SPECIES:
        sid = slug(name)
        print(f"{name}...")
        skipped = skip.setdefault(sid, [])
        existing = []
        for p in manifest.get(sid, {}).get("photos", []):
            if os.path.exists(os.path.join(OUT_DIR, p["file"])):
                existing.append(p)
            else:
                print(f"  {p['file']} was deleted, skipping it from now on")
                if p["source"] not in skipped:
                    skipped.append(p["source"])

        photos = fetch_species(name, existing, skipped)
        manifest[sid] = {"latin": name, "photos": photos}
        print(f"  {len(photos)} photos ({len(photos) - len(existing)} new)")
        with open(manifest_path, "w") as f:  # save as we go
            json.dump(manifest, f, indent=2)
        with open(skip_path, "w") as f:
            json.dump({k: v for k, v in skip.items() if v}, f, indent=2)
        time.sleep(1)

    print(f"\nDone. Credits saved to {OUT_DIR}/photos.json")


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    main(sys.argv[1:])
