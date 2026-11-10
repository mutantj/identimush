# Identimush

A game for learning to identify North American mushrooms from photos.
Multiple choice with common names first, Latin names from level 4.

> Learning tool only. Never eat a wild mushroom based on a photo or an app.

## Run it

1. Get photos (needs Python 3):
   ```
   python scripts/fetch_photos.py
   ```
   This creates `photos/` with images and `photos/photos.json` (credits).
2. Start a local server in the project folder:
   ```
   python -m http.server 8000
   ```
3. Open http://localhost:8000

Opening `index.html` directly won't work: browsers block loading the JSON files from disk.

## Files

- `index.html`, `css/style.css`, `js/game.js`: the game
- `data/species.json`: species features, lookalikes and toxicity
- `scripts/fetch_photos.py`: downloads CC-licensed photos from GBIF

## Add a species

1. Add its Latin name to `SPECIES` in `scripts/fetch_photos.py` and rerun it.
2. Add an entry to `data/species.json`. The `id` is the Latin name in lowercase with dashes.

## Publish on GitHub Pages

Commit everything including `photos/`, then in the repo go to Settings, Pages, and deploy from the `main` branch.

## Photo credits

Photos come from GBIF and its partners (mainly iNaturalist) under Creative Commons licences.
Each photo's creator, licence and source link are shown in the game and stored in `photos/photos.json`.
