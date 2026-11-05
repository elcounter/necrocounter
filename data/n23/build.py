"""Génère les fichiers JSON Necromunda N23 de NecroCounter à partir des sources texte.

Sources (transcrites depuis le livre de règles N23, version française) :
  src/maisons.txt   listes de gangs des six Maisons
  src/armes.txt     tableaux de référence des armes
  src/comptoir.txt  Comptoir Commercial (prix et rareté)

Sorties :
  armes.json, comptoir.json, maisons/<maison>.json, index.json

Usage : python3 data/n23/build.py
"""
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
STATS = ["M", "CC", "CT", "F", "E", "PV", "I", "A", "CD", "SF", "V", "INT"]
PROFILE = ["porC", "porL", "preC", "preL", "F", "PA", "D", "Mu"]
SKILL_CATEGORIES = ["Agilité", "Muscle", "Combat", "Ruse", "Férocité", "Autorité", "Tir", "Savoir"]
WARNINGS = []


def slug(text):
    """Identifiant stable : minuscules, sans accents ni ponctuation."""
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def lines(path):
    """Lignes utiles d'une source : sans commentaires ni lignes vides."""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            yield line
        elif line.startswith("## "):
            yield line


def take_doubt(text):
    """Retire le marqueur de doute "?" final et le signale."""
    if text.endswith("?"):
        return text[:-1].strip(), True
    return text, False


def clean_name(name):
    """Sépare le nom de ses marqueurs : "*" (compte double) et "'" (accessoire non cumulable)."""
    flags = {}
    if "*" in name:
        flags["compteDouble"] = True
        name = name.replace("*", "")
    if name.rstrip().endswith("'") and not name.rstrip().endswith("p'"):
        flags["accessoireUnique"] = True
        name = name.rstrip()[:-1]
    name = re.sub(r"'(?= \()", "", name)  # Lunette' (armes...) -> Lunette (armes...)
    if "accessoireUnique" not in flags and re.search(r"\w' \(", name):
        flags["accessoireUnique"] = True
    return re.sub(r"\s+", " ", name).strip(), flags


def parse_armes():
    weapons, section, current = [], None, None
    for line in lines(SRC / "armes.txt"):
        if line.startswith("## "):
            section = line[3:]
            continue
        line, doubt = take_doubt(line)
        cols = [c.strip() for c in line.split("|")]
        is_mode = cols[0].startswith("- ")
        name = cols[0][2:] if is_mode else cols[0]
        profile = None
        if len(cols) == 10:
            profile = dict(zip(PROFILE, cols[1:9]))
            profile["traits"] = [] if cols[9] == "-" else [t.strip() for t in cols[9].split(",")]
            if doubt:
                profile["aVerifier"] = True
                WARNINGS.append(f"armes : {current['nom'] + ' / ' if is_mode else ''}{name}")
        elif len(cols) != 1:
            raise ValueError(f"armes.txt : {len(cols)} colonnes au lieu de 10 : {line}")
        if is_mode:
            current["profils"].append({"mode": name, **profile})
        else:
            current = {"id": slug(name), "nom": name, "categorie": section, "profils": []}
            if profile:
                current["profils"].append({"mode": None, **profile})
            weapons.append(current)
    return weapons


def parse_price(name, price, rarity=None, section=None):
    name, flags = clean_name(name)
    item = {"nom": name, "prix": int(price), **flags}
    if rarity is not None:
        rarity, doubt = take_doubt(rarity)
        item["rarete"] = rarity
        if doubt:
            item["aVerifier"] = True
    if section:
        item["categorie"] = section
    return item


def parse_comptoir():
    items, section, parent = [], None, None
    for line in lines(SRC / "comptoir.txt"):
        if line.startswith("## "):
            section = line[3:]
            continue
        line, doubt = take_doubt(line)
        cols = [c.strip() for c in line.split("|")]
        if len(cols) == 1:
            parent, _ = clean_name(cols[0])
            continue
        name = cols[0]
        if name.startswith("- "):
            name = f"{parent} ({name[2:]})"
        else:
            parent = None
        item = parse_price(name, cols[1], cols[2] + ("?" if doubt else ""), section)
        item["id"] = slug(item["nom"])
        if doubt:
            WARNINGS.append(f"comptoir : {item['nom']}")
        items.append(item)
    return items


def parse_skills(spec):
    res = {"primaires": [], "secondaires": []}
    for part in spec.split(","):
        cat, level = part.strip().rsplit(" ", 1)
        if cat not in SKILL_CATEGORIES or level not in ("P", "S"):
            raise ValueError(f"compétence inconnue : {part}")
        res["primaires" if level == "P" else "secondaires"].append(cat)
    return res


def parse_maisons():
    houses, house, section = [], None, None
    for line in lines(SRC / "maisons.txt"):
        if line.startswith("= "):
            house = {"id": slug(line[2:]), "nom": line[2:], "combattants": [],
                     "competences": {}, "equipement": []}
            houses.append(house)
        elif line.startswith("combattant:"):
            role, cost, stats, gear = [c.strip() for c in line.split(":", 1)[1].split("|")]
            values = stats.split()
            if len(values) != len(STATS):
                raise ValueError(f"{house['nom']} {role} : {len(values)} caractéristiques")
            house["combattants"].append({
                "id": slug(role), "role": role, "cout": int(cost),
                "profil": dict(zip(STATS, values)),
                "equipementDeDepart": [g.strip() for g in gear.split(",") if g.strip()],
            })
        elif line.startswith("competences:"):
            role, spec = [c.strip() for c in line.split(":", 1)[1].split("|")]
            house["competences"][slug(role)] = parse_skills(spec)
        elif line.startswith("## "):
            section = line[3:]
        else:
            cols = [c.strip() for c in line.split("|")]
            item = parse_price(cols[0], cols[1], section=section)
            item["id"] = slug(item["nom"])
            if len(cols) == 3:
                item["modes"] = [m.strip() for m in cols[2].split(";")]
            house["equipement"].append(item)
    return houses


def link_weapons(houses, weapons):
    """Relie chaque arme de Maison à son profil dans armes.json (plus long préfixe commun)."""
    by_slug = sorted(weapons, key=lambda w: -len(w["id"]))
    for house in houses:
        for item in house["equipement"]:
            if not item["categorie"].startswith("Armes") and item["categorie"] != "Pistolets" \
                    and item["categorie"] != "Grenades":
                continue
            target = next((w for w in by_slug if item["id"].startswith(w["id"])), None)
            if target is None:
                WARNINGS.append(f"{house['nom']} : pas de profil pour {item['nom']}")
                continue
            item["arme"] = target["id"]
            known = {p["mode"] for p in target["profils"]}
            if "modes" in item:
                unknown = [m for m in item["modes"] if m not in known]
                if unknown:
                    WARNINGS.append(f"{house['nom']} : modes inconnus {unknown} pour {item['nom']}")
                continue
            # Armes combinées : ne garder que les composants nommés entre parenthèses
            m = re.search(r"\(([^)]*/[^)]*)\)", item["nom"])
            if m and target["profils"] and target["profils"][0]["mode"]:
                parts = [p.strip().lower() for p in m.group(1).split("/")]
                modes = [p["mode"] for p in target["profils"] if p["mode"].lower() in parts]
                if len(modes) == len(parts):
                    item["modes"] = modes
                else:
                    WARNINGS.append(f"{house['nom']} : composants introuvables pour {item['nom']}")


def main():
    weapons = parse_armes()
    comptoir = parse_comptoir()
    houses = parse_maisons()
    link_weapons(houses, weapons)

    meta = {"edition": "Necromunda N23", "source": "Livre de règles N23 (version française)"}
    rules = {
        "novice": "Un Novice ne peut pas recevoir d'objet d'une valeur supérieure à 20 crédits "
                  "lorsqu'il est ajouté au gang. Cette limite cesse après sa première Progression.",
        "armeSpeciale": "À la création du gang, un seul Ganger peut être équipé d'une Arme Spéciale. "
                        "En campagne, les Gangers recrutés ensuite peuvent aussi en recevoir.",
        "chefEtChampion": "Le Chef et les Champions ne sont soumis à aucune restriction d'armes "
                          "et commencent avec une compétence gratuite de leurs sets Primaires.",
    }

    def write(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    write(ROOT / "armes.json", {**meta, "armes": weapons})
    write(ROOT / "comptoir.json", {**meta, "objets": comptoir})
    for h in houses:
        write(ROOT / "maisons" / f"{h['id']}.json", {**meta, "reglesDeCreation": rules, **h})
    write(ROOT / "index.json", {**meta, "maisons": [{"id": h["id"], "nom": h["nom"],
                                                    "fichier": f"maisons/{h['id']}.json"}
                                                   for h in houses]})

    print(f"armes : {len(weapons)}, comptoir : {len(comptoir)}, maisons : {len(houses)}")
    for w in WARNINGS:
        print("A VERIFIER", w)


if __name__ == "__main__":
    main()
