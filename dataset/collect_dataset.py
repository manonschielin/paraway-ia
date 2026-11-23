"""
collect_dataset.py
Dataset négatif complet pour détection de perruches à collier en IDF.
~40 catégories x 100 images = ~4000 images
Sources : iNaturalist, Wikimedia Commons, Unsplash, GBIF
Usage   : python collect_dataset.py --output ./dataset2 --per-category 100
"""

import os, time, hashlib, csv, argparse, random
from pathlib import Path
from io import BytesIO

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False
    print("[WARN] pip install Pillow pour redimensionnement automatique")

try:
    import requests
except ImportError:
    print("ERREUR : pip install requests")
    exit(1)

TARGET_SIZE  = 640
SLEEP        = 0.35
IDF_PLACE_ID = 6753

# ============================================================
# CATÉGORIES
# ============================================================
CATEGORIES = {

    # ── OISEAUX IDF COMMUNS ──────────────────────────────────
    "birds/merle_noir": {
        "inaturalist": "Turdus merula",
        "gbif": "Turdus merula",
        "wikimedia_cats": ["Turdus merula", "Blackbird (Turdus merula) in France"],
        "wikimedia_search": ["Turdus merula France", "merle noir jardin"],
        "unsplash": ["blackbird bird", "merle noir"],
    },
    "birds/moineau": {
        "inaturalist": "Passer domesticus",
        "gbif": "Passer domesticus",
        "wikimedia_cats": ["Passer domesticus", "House sparrow in France"],
        "wikimedia_search": ["moineau domestique France", "Passer domesticus Paris"],
        "unsplash": ["house sparrow bird", "moineau"],
    },
    "birds/pigeon_ramier": {
        "inaturalist": "Columba palumbus",
        "gbif": "Columba palumbus",
        "wikimedia_cats": ["Columba palumbus", "Wood pigeon in France"],
        "wikimedia_search": ["pigeon ramier France", "Columba palumbus"],
        "unsplash": ["wood pigeon bird", "pigeon ramier"],
    },
    "birds/pigeon_biset": {
        "inaturalist": "Columba livia",
        "gbif": "Columba livia",
        "wikimedia_cats": ["Columba livia", "Feral pigeon"],
        "wikimedia_search": ["pigeon de ville Paris", "Columba livia urbain"],
        "unsplash": ["city pigeon urban", "pigeon ville"],
    },
    "birds/corneille_noire": {
        "inaturalist": "Corvus corone",
        "gbif": "Corvus corone",
        "wikimedia_cats": ["Corvus corone", "Carrion crow in France"],
        "wikimedia_search": ["corneille noire France", "Corvus corone"],
        "unsplash": ["carrion crow bird", "corneille"],
    },
    "birds/pie_bavarde": {
        "inaturalist": "Pica pica",
        "gbif": "Pica pica",
        "wikimedia_cats": ["Pica pica", "Eurasian magpie in France"],
        "wikimedia_search": ["pie bavarde France", "Pica pica jardin"],
        "unsplash": ["magpie bird", "pie bavarde"],
    },
    "birds/mesange_bleue": {
        "inaturalist": "Cyanistes caeruleus",
        "gbif": "Cyanistes caeruleus",
        "wikimedia_cats": ["Cyanistes caeruleus", "Blue tit in France"],
        "wikimedia_search": ["mésange bleue France", "Cyanistes caeruleus"],
        "unsplash": ["blue tit bird", "mésange bleue"],
    },
    "birds/mesange_charbonniere": {
        "inaturalist": "Parus major",
        "gbif": "Parus major",
        "wikimedia_cats": ["Parus major", "Great tit in France"],
        "wikimedia_search": ["mésange charbonnière France", "Parus major"],
        "unsplash": ["great tit bird", "mésange charbonnière"],
    },
    "birds/verdier": {
        "inaturalist": "Chloris chloris",
        "gbif": "Chloris chloris",
        "wikimedia_cats": ["Chloris chloris", "European greenfinch"],
        "wikimedia_search": ["verdier Europe France", "Chloris chloris"],
        "unsplash": ["greenfinch bird", "verdier oiseau"],
    },
    "birds/pinson_arbres": {
        "inaturalist": "Fringilla coelebs",
        "gbif": "Fringilla coelebs",
        "wikimedia_cats": ["Fringilla coelebs", "Common chaffinch in France"],
        "wikimedia_search": ["pinson des arbres France", "Fringilla coelebs"],
        "unsplash": ["chaffinch bird", "pinson oiseau"],
    },
    "birds/rouge_gorge": {
        "inaturalist": "Erithacus rubecula",
        "gbif": "Erithacus rubecula",
        "wikimedia_cats": ["Erithacus rubecula", "European robin in France"],
        "wikimedia_search": ["rougegorge familier France", "Erithacus rubecula"],
        "unsplash": ["robin bird", "rougegorge"],
    },
    "birds/etourneau": {
        "inaturalist": "Sturnus vulgaris",
        "gbif": "Sturnus vulgaris",
        "wikimedia_cats": ["Sturnus vulgaris", "Common starling in France"],
        "wikimedia_search": ["étourneau sansonnet France", "Sturnus vulgaris"],
        "unsplash": ["starling bird", "étourneau"],
    },
    "birds/hirondelle": {
        "inaturalist": "Hirundo rustica",
        "gbif": "Hirundo rustica",
        "wikimedia_cats": ["Hirundo rustica", "Barn swallow in France"],
        "wikimedia_search": ["hirondelle rustique France", "Hirundo rustica"],
        "unsplash": ["swallow bird flight", "hirondelle"],
    },
    "birds/martinet": {
        "inaturalist": "Apus apus",
        "gbif": "Apus apus",
        "wikimedia_cats": ["Apus apus", "Common swift in France"],
        "wikimedia_search": ["martinet noir Paris", "Apus apus vol"],
        "unsplash": ["swift bird flight", "martinet noir"],
    },
    "birds/accenteur_mouchet": {
        "inaturalist": "Prunella modularis",
        "gbif": "Prunella modularis",
        "wikimedia_cats": ["Prunella modularis", "Dunnock in France"],
        "wikimedia_search": ["accenteur mouchet France", "Prunella modularis"],
        "unsplash": ["dunnock bird", "accenteur"],
    },
    "birds/grimpereau": {
        "inaturalist": "Certhia brachydactyla",
        "gbif": "Certhia brachydactyla",
        "wikimedia_cats": ["Certhia brachydactyla"],
        "wikimedia_search": ["grimpereau jardins France", "Certhia brachydactyla"],
        "unsplash": ["treecreeper bird", "grimpereau"],
    },
    "birds/sittelle": {
        "inaturalist": "Sitta europaea",
        "gbif": "Sitta europaea",
        "wikimedia_cats": ["Sitta europaea", "Eurasian nuthatch in France"],
        "wikimedia_search": ["sittelle torchepot France", "Sitta europaea"],
        "unsplash": ["nuthatch bird tree", "sittelle"],
    },
    "birds/pic_vert": {
        "inaturalist": "Picus viridis",
        "gbif": "Picus viridis",
        "wikimedia_cats": ["Picus viridis", "European green woodpecker in France"],
        "wikimedia_search": ["pic vert France jardin", "Picus viridis"],
        "unsplash": ["green woodpecker bird", "pic vert"],
    },
    "birds/pic_epeiche": {
        "inaturalist": "Dendrocopos major",
        "gbif": "Dendrocopos major",
        "wikimedia_cats": ["Dendrocopos major", "Great spotted woodpecker France"],
        "wikimedia_search": ["pic épeiche France", "Dendrocopos major"],
        "unsplash": ["great spotted woodpecker", "pic épeiche"],
    },
    "birds/fauvette": {
        "inaturalist": "Sylvia atricapilla",
        "gbif": "Sylvia atricapilla",
        "wikimedia_cats": ["Sylvia atricapilla", "Eurasian blackcap France"],
        "wikimedia_search": ["fauvette tête noire France", "Sylvia atricapilla"],
        "unsplash": ["blackcap bird", "fauvette"],
    },
    # ── OISEAUX EUROPÉENS COMMUNS ────────────────────────────
    "birds/bergeronnette": {
        "inaturalist": "Motacilla alba",
        "gbif": "Motacilla alba",
        "wikimedia_cats": ["Motacilla alba", "White wagtail in France"],
        "wikimedia_search": ["bergeronnette grise France", "Motacilla alba"],
        "unsplash": ["white wagtail bird", "bergeronnette"],
    },
    "birds/rouge_queue": {
        "inaturalist": "Phoenicurus ochruros",
        "gbif": "Phoenicurus ochruros",
        "wikimedia_cats": ["Phoenicurus ochruros", "Black redstart France"],
        "wikimedia_search": ["rougequeue noir France", "Phoenicurus ochruros"],
        "unsplash": ["black redstart bird", "rougequeue"],
    },
    "birds/grive_musicienne": {
        "inaturalist": "Turdus philomelos",
        "gbif": "Turdus philomelos",
        "wikimedia_cats": ["Turdus philomelos", "Song thrush in France"],
        "wikimedia_search": ["grive musicienne France", "Turdus philomelos"],
        "unsplash": ["song thrush bird", "grive musicienne"],
    },
    "birds/geai_des_chenes": {
        "inaturalist": "Garrulus glandarius",
        "gbif": "Garrulus glandarius",
        "wikimedia_cats": ["Garrulus glandarius", "Eurasian jay in France"],
        "wikimedia_search": ["geai des chênes France", "Garrulus glandarius"],
        "unsplash": ["eurasian jay bird", "geai oiseau"],
    },
    "birds/tourterelle_turque": {
        "inaturalist": "Streptopelia decaocto",
        "gbif": "Streptopelia decaocto",
        "wikimedia_cats": ["Streptopelia decaocto", "Eurasian collared dove France"],
        "wikimedia_search": ["tourterelle turque France", "Streptopelia decaocto"],
        "unsplash": ["collared dove bird", "tourterelle turque"],
    },
    # ── PSITTACIDÉS CONFONDANTS (FAUX POSITIFS POTENTIELS) ──
    "birds/perruche_moine": {
        "inaturalist": "Myiopsitta monachus",
        "gbif": "Myiopsitta monachus",
        "wikimedia_cats": ["Myiopsitta monachus", "Monk parakeet in Europe"],
        "wikimedia_search": ["perruche moine France", "Myiopsitta monachus Europe"],
        "unsplash": ["monk parakeet bird green", "perruche moine"],
    },
    "birds/perroquet_vert": {
        "inaturalist": "Amazona",
        "gbif": "Amazona amazonica",
        "wikimedia_cats": ["Amazona amazonica", "Amazon parrot green"],
        "wikimedia_search": ["perroquet vert amazone", "green amazon parrot"],
        "unsplash": ["amazon parrot green", "perroquet vert"],
    },
    "birds/conure_soleil": {
        "inaturalist": "Aratinga solstitialis",
        "gbif": "Aratinga solstitialis",
        "wikimedia_cats": ["Aratinga solstitialis", "Sun parakeet"],
        "wikimedia_search": ["conure soleil perruche", "sun conure parakeet"],
        "unsplash": ["sun conure parrot", "conure perruche"],
    },
    "birds/perruche_alexandre": {
        "inaturalist": "Psittacula eupatria",
        "gbif": "Psittacula eupatria",
        "wikimedia_cats": ["Psittacula eupatria", "Alexandrine parakeet"],
        "wikimedia_search": ["perruche alexandre grande", "Psittacula eupatria"],
        "unsplash": ["alexandrine parakeet bird", "grande perruche"],
    },
    "birds/cacatoes": {
        "inaturalist": "Cacatua galerita",
        "gbif": "Cacatua",
        "wikimedia_cats": ["Cacatua galerita", "Sulphur-crested cockatoo"],
        "wikimedia_search": ["cacatoès blanc", "cockatoo white bird"],
        "unsplash": ["cockatoo white parrot", "cacatoès"],
    },
    # ── BACKGROUNDS VÉGÉTATION ───────────────────────────────
    "background/parcs_urbains": {
        "inaturalist": None,
        "gbif": None,
        "wikimedia_cats": [
            "Parks in Paris", "Bois de Vincennes", "Bois de Boulogne",
            "Parc de Saint-Cloud", "Parc des Buttes-Chaumont",
            "Parc Montsouris", "Jardins de Versailles"
        ],
        "wikimedia_search": ["parc Paris arbres vert", "jardin public Paris pelouse"],
        "unsplash": ["paris park nature trees", "urban park green", "jardin public"],
    },
    "background/arbres_feuillage": {
        "inaturalist": "Quercus robur",
        "gbif": None,
        "wikimedia_cats": [
            "Trees in Paris", "Trees in Île-de-France",
            "Oak trees in France", "Platanus in France",
            "Lime trees in France", "Poplar trees in France"
        ],
        "wikimedia_search": ["feuillage arbre France été", "canopée forêt IDF", "branches feuilles vertes"],
        "unsplash": ["tree canopy green leaves", "feuillage arbre", "forest canopy sunlight"],
    },
    "background/buissons_haies": {
        "inaturalist": "Ligustrum vulgare",
        "gbif": None,
        "wikimedia_cats": [
            "Shrubs in France", "Hedges in France",
            "Ligustrum vulgare", "Prunus spinosa in France",
            "Cornus sanguinea"
        ],
        "wikimedia_search": ["haie buissons France", "arbuste jardin vert", "hedge shrubs green"],
        "unsplash": ["garden hedge bushes", "green shrubs nature", "haie verte"],
    },
    "background/ciel_branches": {
        "inaturalist": None,
        "gbif": None,
        "wikimedia_cats": [
            "Blue sky with trees", "Sky through trees",
            "Trees against sky in France", "Silhouettes of trees"
        ],
        "wikimedia_search": ["ciel bleu branches arbres", "contre-jour arbre ciel", "sky through tree canopy"],
        "unsplash": ["sky through trees", "branches blue sky", "tree silhouette sky"],
    },
    "background/foret_sous_bois": {
        "inaturalist": "Hedera helix",
        "gbif": None,
        "wikimedia_cats": [
            "Forêt de Fontainebleau", "Forêt de Rambouillet",
            "Forêt de Sénart", "Forêt de Marly",
            "Forests in Île-de-France", "Forest paths in France"
        ],
        "wikimedia_search": ["sous-bois forêt IDF", "sentier forêt France", "intérieur forêt"],
        "unsplash": ["forest path france", "sous-bois forêt", "woodland forest floor"],
    },
    "background/sol_litiere": {
        "inaturalist": "Bryophyta",
        "gbif": None,
        "wikimedia_cats": [
            "Forest floors in France", "Leaf litter",
            "Mosses in France", "Ground vegetation in France",
            "Fallen leaves"
        ],
        "wikimedia_search": ["litière feuilles sol forêt", "mousse sol forêt France", "feuilles mortes automne"],
        "unsplash": ["forest floor leaves autumn", "leaf litter ground", "mossy forest floor"],
    },
    "background/vegetation_dense": {
        "inaturalist": "Pteridium aquilinum",
        "gbif": None,
        "wikimedia_cats": [
            "Dense vegetation in France", "Ferns in France",
            "Brambles in France", "Undergrowth in France"
        ],
        "wikimedia_search": ["végétation dense France", "fougères forêt", "ronces buissons denses"],
        "unsplash": ["dense vegetation green", "ferns forest", "undergrowth green"],
    },
    "background/berges_cours_eau": {
        "inaturalist": "Salix",
        "gbif": None,
        "wikimedia_cats": [
            "Banks of the Seine", "Rivers in Île-de-France",
            "Marne river banks", "Willow trees France"
        ],
        "wikimedia_search": ["berge rivière IDF", "bords Seine arbres", "cours d'eau végétation"],
        "unsplash": ["river bank trees france", "berge rivière", "waterside vegetation"],
    },
    "background/zones_urbaines": {
        "inaturalist": None,
        "gbif": None,
        "wikimedia_cats": [
            "Streets in Paris", "Suburbs of Paris",
            "Buildings in Île-de-France", "Facades in Paris"
        ],
        "wikimedia_search": ["banlieue parisienne arbres", "rue Paris végétation", "immeuble Paris jardin"],
        "unsplash": ["paris street trees", "urban nature paris", "suburban paris"],
    },
    "background/ciel_nuageux": {
        "inaturalist": None,
        "gbif": None,
        "wikimedia_cats": [
            "Cloudy skies in France", "Overcast skies",
            "Grey sky France"
        ],
        "wikimedia_search": ["ciel nuageux France gris", "overcast sky trees", "ciel couvert IDF"],
        "unsplash": ["cloudy sky overcast", "grey sky trees", "ciel nuageux"],
    },
}

# ============================================================
# UTILITAIRES
# ============================================================

def md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def resize_and_save(src_bytes: bytes, dest: Path) -> bool:
    if not PIL_OK:
        dest.write_bytes(src_bytes)
        return os.path.getsize(dest) > 5000
    try:
        img = Image.open(BytesIO(src_bytes)).convert("RGB")
        w, h = img.size
        if max(w, h) < 150:
            return False
        ratio = TARGET_SIZE / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        img.save(dest, "JPEG", quality=90)
        return True
    except Exception:
        return False

def download(url: str, dest: Path) -> bool:
    try:
        r = requests.get(url, timeout=20,
                         headers={"User-Agent": "perruche-dataset/1.0"})
        r.raise_for_status()
        ok = resize_and_save(r.content, dest)
        if not ok and dest.exists():
            dest.unlink()
        return ok
    except Exception as e:
        if dest.exists():
            dest.unlink()
        return False

def get_json(url, params=None):
    r = requests.get(url, params=params, timeout=15,
                     headers={"User-Agent": "perruche-dataset/1.0"})
    r.raise_for_status()
    return r.json()

# ============================================================
# SOURCES
# ============================================================

def fetch_inaturalist(taxon: str, n: int) -> list[dict]:
    if not taxon:
        return []
    results = []
    seen_obs = {}
    try:
        data = get_json("https://api.inaturalist.org/v1/observations", {
            "taxon_name": taxon, "place_id": IDF_PLACE_ID,
            "quality_grade": "research", "photos": "true",
            "per_page": min(n * 3, 100), "order_by": "random",
        })
        for obs in data.get("results", []):
            oid = obs.get("id")
            count = seen_obs.get(oid, 0)
            for photo in obs.get("photos", []):
                if count >= 3 or len(results) >= n:
                    break
                url = photo.get("url", "").replace("square", "medium")
                if url:
                    results.append({"url": url, "source": "iNaturalist",
                                    "license": photo.get("license_code", "cc")})
                    count += 1
            seen_obs[oid] = count
        time.sleep(SLEEP)
    except Exception as e:
        print(f"      [iNat] {taxon}: {e}")
    return results[:n]

def fetch_gbif(taxon: str, n: int) -> list[dict]:
    if not taxon:
        return []
    results = []
    try:
        match = get_json("https://api.gbif.org/v1/species/match", {"name": taxon})
        key = match.get("usageKey")
        if not key:
            return []
        data = get_json("https://api.gbif.org/v1/occurrence/search", {
            "taxonKey": key, "country": "FR",
            "mediaType": "StillImage", "hasCoordinate": "true",
            "limit": min(n * 3, 100),
        })
        for occ in data.get("results", []):
            for m in occ.get("media", []):
                url = m.get("identifier", "")
                if url and url.startswith("http") and len(results) < n:
                    results.append({"url": url, "source": "GBIF",
                                    "license": m.get("license", "CC")})
        time.sleep(SLEEP)
    except Exception as e:
        print(f"      [GBIF] {taxon}: {e}")
    return results[:n]

def fetch_wikimedia_cat(category: str, n: int) -> list[dict]:
    results = []
    try:
        data = get_json("https://commons.wikimedia.org/w/api.php", {
            "action": "query", "generator": "categorymembers",
            "gcmtitle": f"Category:{category}", "gcmtype": "file",
            "gcmlimit": min(n * 3, 100), "prop": "imageinfo",
            "iiprop": "url|extmetadata|mime", "iiurlwidth": TARGET_SIZE,
            "format": "json",
        })
        for page in data.get("query", {}).get("pages", {}).values():
            ii = page.get("imageinfo", [{}])[0]
            if "image" not in ii.get("mime", ""):
                continue
            url = ii.get("thumburl") or ii.get("url", "")
            if not url:
                continue
            lic = ii.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "CC")
            if "ND" in lic.upper():
                continue
            results.append({"url": url, "source": "Wikimedia", "license": lic})
            if len(results) >= n:
                break
        time.sleep(SLEEP)
    except Exception as e:
        print(f"      [Wiki cat '{category}']: {e}")
    return results

def fetch_wikimedia_search(query: str, n: int) -> list[dict]:
    results = []
    try:
        data = get_json("https://commons.wikimedia.org/w/api.php", {
            "action": "query", "generator": "search",
            "gsrnamespace": 6, "gsrsearch": query,
            "gsrlimit": min(n * 2, 50), "prop": "imageinfo",
            "iiprop": "url|extmetadata|mime", "iiurlwidth": TARGET_SIZE,
            "format": "json",
        })
        for page in data.get("query", {}).get("pages", {}).values():
            ii = page.get("imageinfo", [{}])[0]
            if "image" not in ii.get("mime", ""):
                continue
            url = ii.get("thumburl") or ii.get("url", "")
            if not url:
                continue
            lic = ii.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "CC")
            if "ND" in lic.upper():
                continue
            results.append({"url": url, "source": "Wikimedia", "license": lic})
            if len(results) >= n:
                break
        time.sleep(SLEEP)
    except Exception as e:
        print(f"      [Wiki search '{query}']: {e}")
    return results

def fetch_unsplash(query: str, n: int) -> list[dict]:
    results = []
    key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
    try:
        if key:
            r = requests.get("https://api.unsplash.com/search/photos",
                             params={"query": query, "per_page": min(n, 30), "orientation": "landscape"},
                             headers={"Authorization": f"Client-ID {key}"}, timeout=15)
            r.raise_for_status()
            for p in r.json().get("results", []):
                url = p.get("urls", {}).get("regular", "")
                if url:
                    results.append({"url": url, "source": "Unsplash", "license": "Unsplash"})
        else:
            r = requests.get("https://unsplash.com/napi/search/photos",
                             params={"query": query, "per_page": min(n, 20)},
                             headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            r.raise_for_status()
            for p in r.json().get("results", []):
                url = p.get("urls", {}).get("regular", "")
                if url:
                    results.append({"url": url, "source": "Unsplash", "license": "Unsplash"})
        time.sleep(SLEEP)
    except Exception as e:
        print(f"      [Unsplash '{query}']: {e}")
    return results[:n]

# ============================================================
# PIPELINE
# ============================================================

def collect(output_dir: Path, per_category: int):
    output_dir.mkdir(parents=True, exist_ok=True)
    meta_path = output_dir / "metadata" / "sources.csv"
    meta_path.parent.mkdir(exist_ok=True)

    seen_hashes: set[str] = set()
    total = 0
    per_src = max(10, per_category // 4)

    cats = list(CATEGORIES.items())
    n_cats = len(cats)

    with open(meta_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile,
            fieldnames=["filename", "category", "source", "license", "url", "md5"])
        writer.writeheader()

        for idx, (cat_path, cfg) in enumerate(cats, 1):
            cat_dir = output_dir / cat_path
            cat_dir.mkdir(parents=True, exist_ok=True)
            print(f"\n[{idx:02d}/{n_cats}] {cat_path}")

            candidates: list[dict] = []

            if cfg.get("inaturalist"):
                candidates += fetch_inaturalist(cfg["inaturalist"], per_src)
            if cfg.get("gbif"):
                candidates += fetch_gbif(cfg["gbif"], per_src)
            for wcat in cfg.get("wikimedia_cats", []):
                candidates += fetch_wikimedia_cat(wcat, per_src)
            for wsearch in cfg.get("wikimedia_search", []):
                candidates += fetch_wikimedia_search(wsearch, per_src // 2)
            for uq in cfg.get("unsplash", []):
                candidates += fetch_unsplash(uq, per_src)

            random.shuffle(candidates)
            print(f"      {len(candidates)} candidats → téléchargement...")

            collected = 0
            for item in candidates:
                if collected >= per_category:
                    break
                fname = f"{cat_path.replace('/', '_')}_{collected:04d}.jpg"
                dest = cat_dir / fname

                if not download(item["url"], dest):
                    continue

                h = md5(dest)
                if h in seen_hashes:
                    dest.unlink()
                    continue
                seen_hashes.add(h)

                writer.writerow({
                    "filename": str(dest.relative_to(output_dir)),
                    "category": cat_path, "source": item["source"],
                    "license": item.get("license", "CC"),
                    "url": item["url"], "md5": h,
                })
                csvfile.flush()
                collected += 1
                total += 1
                print(f"      [{collected:03d}/{per_category}] {fname}  ({item['source']})")

            print(f"      ✓ {collected} images")

    # Splits
    import glob
    all_imgs = list(output_dir.rglob("*.jpg"))
    random.shuffle(all_imgs)
    n = len(all_imgs)
    t = int(n * 0.70)
    v = int(n * 0.15)
    splits_dir = output_dir / "splits"
    splits_dir.mkdir(exist_ok=True)
    for name, subset in [("train", all_imgs[:t]), ("val", all_imgs[t:t+v]), ("test", all_imgs[t+v:])]:
        (splits_dir / f"{name}.txt").write_text(
            "\n".join(str(p.relative_to(output_dir)) for p in subset))

    print(f"\n{'='*55}")
    print(f"✓ Collecte terminée — {total} images / {n_cats} catégories")
    print(f"  Splits : {t} train / {v} val / {n-t-v} test")
    print(f"  Métadonnées : {meta_path}")
    if not os.environ.get("UNSPLASH_ACCESS_KEY"):
        print(f"\n  → Clé Unsplash (gratuite) pour +30% d'images background :")
        print(f"    https://unsplash.com/developers")
        print(f"    set UNSPLASH_ACCESS_KEY=ta_cle")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output",       default="./dataset2")
    parser.add_argument("--per-category", type=int, default=100)
    args = parser.parse_args()
    collect(Path(args.output), args.per_category)
