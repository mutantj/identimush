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

## Remove a bad photo

Delete the photo file, then run `python scripts/fetch_photos.py "<Latin name>"`. The script drops it from `photos/photos.json`, adds it to `photos/skip.json` so it's never downloaded again, and fetches a replacement.

## Add a species

1. Add its Latin name to `SPECIES` in `scripts/fetch_photos.py`, then fetch just that species (keeps existing photos):
   ```
   python scripts/fetch_photos.py "Agaricus augustus"
   ```
2. Add an entry to `data/species.json`. The `id` is the Latin name in lowercase with dashes. `say` is a respelling of the Latin name with the stressed syllables in capitals.
3. Add the name's phonemes to `PHONEMES` in `scripts/make_audio.py` (cheat sheet at the top of the file), then make its audio (needs `espeak-ng`):
   ```
   python scripts/make_audio.py agaricus-augustus
   ```

## Publish on GitHub Pages

Commit everything including `photos/`, then in the repo go to Settings, Pages, and deploy from the `main` branch.

## Photo credits

Photos come from GBIF and its partners (mainly iNaturalist) under Creative Commons licences.
Each photo's creator, licence and source link are shown in the game and stored in `photos/photos.json`.
