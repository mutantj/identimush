"""
Identimush Latin-name audio.

Makes audio/<id>.wav for each species with espeak-ng, using the English
field-guide pronunciation (how North American foragers say the names).
Each name is given as espeak phonemes so stress and vowels match the
"say" respelling in data/species.json, instead of espeak guessing.

Run:  python make_audio.py                      (all species)
      python make_audio.py agaricus-augustus    (just these ids)
Needs: espeak-ng

Phoneme cheat sheet (espeak, en-us voice):
  '  primary stress before the syllable   ,  secondary stress
  @ a-in-sofa   a cat   A: father   aI nye   eI day   e@ air   E bed
  i: see   I sit   i happy   0 lot   O: or   oU go   OI boy   u: loo
  U put   V cut   3: her   T thin   S sh   dZ j   j y
"""

import json
import os
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT_DIR = os.path.join(ROOT, "audio")

AGARICUS = "@g'arIk@s"
AMANITA = ",am@n'aIt@"
CHLOROPHYLLUM = ",klO:roUf'Il@m"
PSILOCYBE = ",saIloUs'aIbi"

PHONEMES = {
    "agaricus-campestris": f"{AGARICUS} kamp'EstrIs",
    "amanita-bisporigera": f"{AMANITA} ,baIspOr'IdZ@r@",
    "cantharellus-cibarius": ",kanT@r'El@s sIb'e@ri@s",
    "omphalotus-illudens": ",0mf@l'oUt@s Il'u:dEnz",
    "morchella-americana": "mO:rk'El@ @,mErIk'an@",
    "gyromitra-esculenta": ",dZaIroUm'aItr@ ,EskjUl'Ent@",
    "chlorophyllum-rhacodes": f"{CHLOROPHYLLUM} r@k'oUdi:z",
    "chlorophyllum-molybdites": f"{CHLOROPHYLLUM} ,m0lIbd'aIti:z",
    "armillaria-mellea": ",A:rmIl'e@ri@ m'Eli@",
    "galerina-marginata": ",gal@r'i:n@ ,mA:rdZIn'A:t@",
    "boletus-edulis": "boUl'i:t@s 'EdjUlIs",
    "tylopilus-felleus": "taIl'0pIl@s f'Eli@s",
    "amanita-muscaria": f"{AMANITA} mVsk'e@ri@",
    "amanita-phalloides": f"{AMANITA} fal'OIdi:z",
    "laetiporus-sulphureus": "li:t'Ip@r@s sVlf'jUri@s",
    "grifola-frondosa": "grIf'oUl@ fr0nd'oUs@",
    "calvatia-gigantea": "kalv'eIS@ dZaIg'anti@",
    "pleurotus-ostreatus": "plu:r'oUt@s ,0stri'eIt@s",
    "hericium-erinaceus": "hEr'Isi@m ,ErIn'eIsi@s",
    "pleurocybella-porrigens": ",plu:roUsaIb'El@ p'0rIdZEnz",
    "hypomyces-lactifluorum": ",haIpoUm'aIsi:z ,laktIfl'O:r@m",
    "agaricus-xanthodermus": f"{AGARICUS} ,zanToUd'3:m@s",
    "agaricus-arvensis": f"{AGARICUS} A:rv'EnsIs",
    "agaricus-augustus": f"{AGARICUS} O:g'Vst@s",
    "psilocybe-cubensis": f"{PSILOCYBE} kju:b'EnsIs",
    "psilocybe-cyanescens": f"{PSILOCYBE} ,saI@n'Es@nz",
    "psilocybe-semilanceata": f"{PSILOCYBE} ,sEmi,lansi'A:t@",
    "pholiotina-rugosa": "foU,lioUt'aIn@_ ru:g'oUs@",
}


def make(species_id):
    path = os.path.join(OUT_DIR, f"{species_id}.wav")
    # -s words per minute (slow for learners), -g gap between words
    subprocess.run(
        ["espeak-ng", "-v", "en-us", "-s", "130", "-g", "4", "-w", path,
         f"[[{PHONEMES[species_id]}]]"],
        check=True,
    )


def main(ids):
    with open(os.path.join(ROOT, "data", "species.json")) as f:
        species = [s["id"] for s in json.load(f)]

    missing = [s for s in species if s not in PHONEMES]
    for s in missing:
        print(f"  ! No phonemes for {s}: add it to PHONEMES")

    os.makedirs(OUT_DIR, exist_ok=True)
    for sid in ids or [s for s in species if s in PHONEMES]:
        if sid not in PHONEMES:
            print(f"  ! Unknown id {sid}")
            continue
        make(sid)
        print(f"{sid}.wav")


if __name__ == "__main__":
    main(sys.argv[1:])
