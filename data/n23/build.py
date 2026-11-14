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
SKILL_CATEGORIES = ["Agilité", "Muscle", "Combat", "Ruse", "Férocité", "Autorité", "Tir", "Savoir",
                    "Sagesse des Anciens", "Désolations", "Formation Palanite", "Sauvagerie", "Pouvoirs Wyrd du Chaos", "Pouvoirs Wyrd Genestealer"]
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
    houses, house, section, roles = [], None, None, None
    for line in lines(SRC / "maisons.txt"):
        if line.startswith("= "):
            name, _, hid = line[2:].partition("=>")
            name = name.strip()
            house = {"id": hid.strip() or slug(name), "nom": name, "combattants": [],
                     "competences": {}, "equipement": []}
            if hid.strip():
                house["titre"] = name
            houses.append(house)
        elif line.startswith("source:"):
            house["source"] = line.split(":", 1)[1].strip()
        elif line.startswith("creation:"):
            key, text = [c.strip() for c in line.split(":", 1)[1].split("|", 1)]
            house.setdefault("creation", {})[key] = text
        elif line.startswith("option:"):
            house[line.split(":", 1)[1].strip()] = True
        elif line.startswith("gangerArmes:"):
            house["gangerArmes"] = [c.strip() for c in line.split(":", 1)[1].split(",")]
        elif line.startswith("regle:"):
            nom, texte = [c.strip() for c in line.split(":", 1)[1].split("|", 1)]
            house.setdefault("regles", []).append({"nom": nom, "texte": texte})
        elif line.startswith("combattant:"):
            role, cost, stats, gear = [c.strip() for c in line.split(":", 1)[1].split("|")]
            role, _, rid = role.partition("=>")
            rid, _, base = rid.partition(":")
            base, _, promo = base.partition(":")
            role, rid = role.strip(), slug(rid.strip()) if rid.strip() else None
            values = stats.split()
            if len(values) != len(STATS):
                raise ValueError(f"{house['nom']} {role} : {len(values)} caractéristiques")
            house["combattants"].append({
                "id": rid or slug(role), "role": role, "cout": int(cost),
                "profil": dict(zip(STATS, values)),
                "equipementDeDepart": [g.strip() for g in gear.split(",") if g.strip()],
                **({"base": slug(base)} if base.strip() else {}),
                **({"promotionDepuis": slug(promo)} if promo.strip() else {}),
            })
        elif line.startswith("competences:"):
            role, spec = [c.strip() for c in line.split(":", 1)[1].split("|")]
            house["competences"][slug(role)] = parse_skills(spec)
        elif line.startswith("## "):
            m = re.match(r"(.*?)\s*\[(.*)\]$", line[3:])
            section, roles = (m.group(1), [slug(r) for r in m.group(2).split(",")]) if m else (line[3:], None)
        else:
            cols = [c.strip() for c in line.split("|")]
            item = parse_price(cols[0], cols[1], section=section)
            item["id"] = slug(item["nom"])
            if roles:
                item["roles"] = roles
            if len(cols) == 3:
                item["modes"] = [m.strip() for m in cols[2].split(";")]
            house["equipement"].append(item)
    return houses


def link_weapons(houses, weapons):
    """Relie chaque arme de Maison à son profil dans armes.json (plus long préfixe commun)."""
    by_slug = sorted(weapons, key=lambda w: -len(w["id"]))
    for house in houses:
        for item in house["equipement"]:
            if "arme" in item:
                continue
            cat = item.get("categorieArme", item["categorie"]).split(" : ")[-1]
            if not cat.startswith("Armes") and cat not in ("Pistolets", "Grenades", "Couteaux", "Armement inclus", "Options d'armes"):
                continue
            key = item["id"][3:] if item["id"].startswith("cc-") else item["id"]
            target = next((w for w in by_slug if key.startswith(w["id"])), None)
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


VEN_PROFILES = {
    "chef": ("Chef Chasseur", 110, [
        '5" 3+ 3+ 3 3 2 3+ 2 7+ 6+ 6+ 6+', '3" 3+ 4+ 3 4 2 5+ 2 6+ 6+ 5+ 5+',
        '4" 3+ 5+ 4 4 2 4+ 2 7+ 5+ 8+ 9+', '4" 4+ 2+ 3 3 2 3+ 1 5+ 5+ 6+ 5+']),
    "champion": ("Champion Chasseur", 85, [
        '5" 4+ 4+ 3 3 2 4+ 2 7+ 6+ 7+ 7+', '3" 4+ 4+ 3 4 2 5+ 2 6+ 6+ 6+ 5+',
        '4" 3+ 5+ 4 4 2 5+ 2 7+ 5+ 8+ 8+', '4" 5+ 2+ 3 3 2 4+ 1 6+ 6+ 6+ 6+']),
    "ganger": ("Chasseur", 50, [
        '5" 4+ 4+ 3 3 1 4+ 1 7+ 6+ 7+ 7+', '3" 4+ 4+ 3 4 1 5+ 1 6+ 6+ 7+ 6+',
        '4" 3+ 4+ 3 4 1 5+ 1 7+ 6+ 8+ 9+', '4" 5+ 3+ 3 3 1 4+ 1 6+ 6+ 6+ 7+']),
}


def rarity_level(text):
    """Seuil de rareté principal d'un objet du Comptoir (0 pour Commune, None si réservé à une Maison)."""
    if "seulement" in text:
        return None
    m = re.match(r"Rare \((\d+)\)", text)
    return int(m.group(1)) if m else 0


def build_venators(comptoir, houses):
    """Gang de Venators (Livre des Périls) : profils au choix, Comptoir comme liste, Legs de Maison."""
    v = {"id": "venators", "nom": "Venators", "titre": "Venators (chasseurs de primes)",
         "source": "Livre des Périls (version française)", "combattants": [], "competences": {},
         "competencesDynamiques": True, "equipement": [],
         "rareteMax": {"chef": 11, "champion": 10, "ganger": 8},
         "gangerArmes": ["Armes de base", "Pistolets", "Couteaux", "Armes de corps à corps ordinaires",
                         "Armes à énergie/choc", "Armes à deux mains", "Grenades"],
         "creation": {
             "chefEtChampion": "Chef Chasseur et Champions Chasseurs n'ont pas de restriction de type d'arme et commencent avec une compétence gratuite de leurs sets Primaires. Au maximum deux Champions Chasseurs à la fondation.",
             "novice": "Pas de Novice : les Chasseurs forment la base du gang et doivent être au moins aussi nombreux que Chef et Champions réunis.",
             "armeSpeciale": "Équipement pris au Comptoir Commercial : Commun ou Rare jusqu'à 11 pour le Chef, 10 pour un Champion, 8 pour un Chasseur. Un Chasseur ne prend que des armes de base, pistolets, armes de corps à corps et grenades (le Spécialiste n'a plus cette limite)."},
         "regles": [
             {"nom": "Profils", "texte": "Pour chaque recrue, choisis un des quatre profils proposés pour son type, selon la figurine."},
             {"nom": "Sets de compétences", "texte": "À la fondation, classe quatre sets (hors Autorité) de 1 à 4. Chef : Primaires 1, 2 et Autorité, Secondaires 3 et 4. Champion : Primaires 1 et 2, Secondaires 3, 4 et Autorité. Spécialiste : Primaires 1 et 2, Secondaires 3 et 4."},
             {"nom": "Hiérarchie de la chasse", "texte": "Le Chef Chasseur suit les règles d'un Chef et les Champions Chasseurs celles des Champions (activation de groupe, actions d'après-bataille, panoplies)."},
             {"nom": "Legs de Maison (30 crédits)", "texte": "Un combattant peut prendre un seul Legs (Goliath, Escher, Cawdor, Orlock, Van Saar ou Delaque) : il accède alors à toute la liste d'équipement de cette Maison. Chef et Champions peuvent aussi acheter les Objets de prestige et Bêtes exotiques de cette Maison."},
             {"nom": "Recrues", "texte": "Brutes et Aventuriers non liés à une Maison seulement. Pas d'autres Chasseurs de primes que les Dramatis Personae. Maximum d'Aventuriers : 1 sous 9 de Réputation, 2 de 10 à 14, 3 de 15 à 19, 4 de 20 à 24, puis +1 par tranche de 5."},
             {"nom": "En campagne Dominion", "texte": "Traités comme un gang normal, avec une Colonie. Bénéfices Accrus seulement selon la Maison d'origine du Chef (son Legs), sinon aucun. Captif vendu à la Guilde : valeur entière au lieu de la moitié. Ennemi tué rayé de sa feuille : prime égale à la moitié de sa valeur, arrondie à 5. Les Chasseurs progressent comme des Gangers (Spécialiste sur 2 ou 12)."}]}
    for rid, (role, cost, profils) in VEN_PROFILES.items():
        for n, stats in enumerate(profils, 1):
            v["combattants"].append({"id": rid if n == 1 else f"{rid}-{n}", "role": f"{role} (profil {n})", "cout": cost,
                                     "profil": dict(zip(STATS, stats.split())), "equipementDeDepart": [],
                                     **({"base": rid} if n > 1 else {})})
    for item in comptoir:
        lvl = rarity_level(item["rarete"])
        if lvl is None or item["categorie"] == "Bêtes exotiques" or item["prix"] <= 0:
            continue
        it = {k: item[k] for k in ("nom", "prix", "categorie", "id") if k in item}
        it.update({k: item[k] for k in ("compteDouble", "accessoireUnique") if k in item})
        it["rarete"] = item["rarete"]
        it["niveau"] = lvl
        if item["categorie"] == "Objets de prestige":
            it["roles"] = ["chef", "champion"]
        v["equipement"].append(it)
    for h in [x for x in houses if "titre" not in x]:
        name = h["nom"]
        v["equipement"].append({"nom": f"Legs de Maison {name}", "prix": 30, "categorie": "Legs de Maison",
                                "id": f"legs-{h['id']}", "legsMaison": h["id"]})
        for item in h["equipement"]:
            it = dict(item)
            it["id"] = f"legs-{h['id']}-{item['id']}"
            it["categorie"] = f"Legs {name} : {item['categorie']}"
            it["legs"] = h["id"]
            it.pop("roles", None)
            v["equipement"].append(it)
    return v


PROSCRIT_SKILLS = {
    "chef": {
        "bagarreur": ({"Muscle", "Férocité", "Autorité"}, {"Agilité", "Combat"}),
        "flingueur": ({"Agilité", "Autorité", "Tir"}, {"Ruse", "Savoir"}),
        "survivant": ({"Combat", "Férocité", "Autorité"}, {"Agilité", "Muscle"}),
        "genie": ({"Ruse", "Autorité", "Savoir"}, {"Agilité", "Tir"}),
        "wyrd": ({"Autorité"}, {"Ruse"}),
    },
    "champion": {
        "bagarreur": ({"Muscle"}, {"Férocité", "Autorité"}),
        "flingueur": ({"Tir"}, {"Agilité", "Autorité"}),
        "survivant": ({"Férocité"}, {"Combat", "Autorité"}),
        "genie": ({"Ruse"}, {"Autorité", "Savoir"}),
        "wyrd": (set(), {"Ruse", "Autorité"}),
    },
}
ARCHETYPES = {"bagarreur": "Bagarreur", "flingueur": "Flingueur", "survivant": "Survivant", "genie": "Génie", "wyrd": "Wyrd"}


def build_proscrits(comptoir, houses):
    """Proscrits du Sous-Monde (Livre des Proscrits) : profils, archétypes, Comptoir limité, Allégeance."""
    order = SKILL_CATEGORIES[:8]
    v = {"id": "proscrits", "nom": "Proscrits", "titre": "Proscrits du Sous-Monde",
         "source": "Livre des Proscrits (version française)", "combattants": [], "competences": {},
         "equipement": [], "rareteMax": {"chef": 9, "champion": 8, "ganger": 0},
         "gangerArmes": ["Armes de base", "Pistolets", "Armes de corps à corps"],
         "archetypes": {"labels": ARCHETYPES, "roles": {}},
         "creation": {
             "chefEtChampion": "Le Chef et les Champions choisissent un Archétype (Bagarreur, Flingueur, Survivant, Génie ou Wyrd) qui fixe leurs sets de compétences, et commencent avec une compétence gratuite de leurs sets Primaires (un Wyrd peut prendre un Pouvoir Wyrd). Deux Champions maximum à la fondation, puis un par tranche complète de 3 Rebuts.",
             "novice": "Pas de Novice : un résultat qui donnerait un Novice donne un Rebut de la Ruche.",
             "armeSpeciale": "Chef : Comptoir Commercial jusqu'à Rareté 9, Champion jusqu'à 8, sans restriction de type. Rebut : sa propre liste (armes de base, pistolets et corps à corps) ; le Spécialiste ajoute les armes spéciales en campagne."},
         "regles": [
             {"nom": "Profils", "texte": "Le Chef Proscrit choisit un des quatre profils proposés, selon la figurine."},
             {"nom": "Chef de gang", "texte": "Un seul Chef, qui ne prend jamais sa retraite. S'il meurt en campagne, le gang se disperse et un nouveau gang doit être fondé."},
             {"nom": "Hiérarchie du gang", "texte": "Une fois le gang Dégonflé, si le Chef réussit son test de Sang-froid en phase de Fin, les Proscrits à 12\" ou moins réussissent automatiquement le leur (6\" pour un Champion). Chef et Champions font des actions d'après-bataille et peuvent avoir plusieurs panoplies."},
             {"nom": "Activation de groupe", "texte": "Le Chef peut activer à sa suite 2 Proscrits Parés à 3\" ou moins, un Champion 1."},
             {"nom": "Composition", "texte": "Les Rebuts doivent être au moins aussi nombreux que les autres combattants (hors Aventuriers et Mercenaires). Trois armes maximum, un Rebut non Spécialiste ne dépasse jamais trois armes et ne peut pas défausser une arme."},
             {"nom": "Allégeance du Chef", "texte": "Sans-clan : ni Intègre ni Hors-la-Loi pour les effets, aucune Alliance possible. Maison Clanique (une des six) : le gang compte comme cette Maison et accède à sa liste d'équipement et ses Bêtes exotiques ; pas d'alliance avec les ennemis de cette Maison. Guilde des Marchands, Organisation Criminelle ou Maison Noble : accès à l'équipement de la Délégation correspondante (livres des Maisons, non intégrés ici) et alliances limitées à cette organisation."},
             {"nom": "Wyrd", "texte": "Un Chef ou Champion Wyrd peut choisir des Pouvoirs Wyrd à la place des compétences et gagne la règle Psyker Clandestin."}]}
    prof = ['7" 4+ 2+ 3 3 2 3+ 2 5+ 4+ 7+ 5+', '6" 3+ 3+ 3 3 2 3+ 3 6+ 7+ 6+ 4+',
            '5" 2+ 4+ 4 3 2 4+ 3 6+ 6+ 4+ 7+', '4" 3+ 4+ 3 4 3 5+ 2 6+ 4+ 6+ 5+']
    for n, stats in enumerate(prof, 1):
        v["combattants"].append({"id": "chef" if n == 1 else f"chef-{n}", "role": f"Chef Proscrit (profil {n})", "cout": 125,
                                 "profil": dict(zip(STATS, stats.split())), "equipementDeDepart": [], **({"base": "chef"} if n > 1 else {})})
    v["combattants"].append({"id": "champion", "role": "Champion Proscrit", "cout": 60,
                             "profil": dict(zip(STATS, '5" 3+ 4+ 3 3 2 4+ 1 6+ 7+ 8+ 8+'.split())), "equipementDeDepart": []})
    v["combattants"].append({"id": "ganger", "role": "Rebut Proscrit", "cout": 30,
                             "profil": dict(zip(STATS, '5" 4+ 4+ 3 3 1 4+ 1 8+ 8+ 8+ 8+'.split())), "equipementDeDepart": []})
    for role, arch in PROSCRIT_SKILLS.items():
        v["archetypes"]["roles"][role] = {a: {"primaires": [c for c in order if c in p], "secondaires": [c for c in order if c in s]}
                                         for a, (p, s) in arch.items()}
        v["competences"][role] = v["archetypes"]["roles"][role]["bagarreur"]
    v["competences"]["specialiste"] = {"primaires": ["Ruse"], "secondaires": ["Férocité"]}
    for item in comptoir:
        lvl = rarity_level(item["rarete"])
        if lvl is None or item["categorie"] == "Bêtes exotiques" or item["prix"] <= 0:
            continue
        it = {k: item[k] for k in ("nom", "prix", "categorie", "id", "compteDouble", "accessoireUnique") if k in item}
        it.update({"rarete": item["rarete"], "niveau": lvl, "roles": ["chef", "champion"],
                   "categorie": "Comptoir : " + item["categorie"]})
        it["id"] = "cc-" + it["id"]
        it["categorieArme"] = item["categorie"]
        v["equipement"].append(it)
    rebut = [("Armes de base", ["Fusil d'assaut|15", "Fusil d'assaut de récup'|10", "Fusil laser|15", "Fusil à canon scié|15",
                                "Fusil à pompe (balles & grenaille)|30", "Couteaux de lancer|10"]),
             ("Pistolets", ["Pistolet-mitrailleur|10", "Pistolet-mitrailleur de récup'|5", "Pistolet laser|10", "Flingue|5"]),
             ("Armes de corps à corps", ["Hache|10", "Épée tronçonneuse|25", "Couteau de combat|10", "Fléau|20", "Masse (matraque)|10",
                                         "Hache à deux mains*|25", "Marteau à deux mains*|35"]),
             ("Grenades", ["Charges explosives|35", "Grenades Frag|30", "Grenades Krak|45", "Grenades fumigènes|15"]),
             ("Armures", ["Armure Flak|10", "Combinaison NBC|10", "Armure composite|15"]),
             ("Équipement personnel", ["Balles dum-dum (flingue)|5", "Sous-combinaison renforcée|25", "Filin|10", "Filtre nasal|10", "Photolunettes|35"]),
             ("Accessoires d'armes", ["Lunette télescopique'|25"])]
    for cat, rows in rebut:
        for r in rows:
            name, price = r.split("|")
            it = parse_price(name, price, section=cat)
            it["id"] = slug(it["nom"])
            it["roles"] = ["ganger"]
            v["equipement"].append(it)
    for h in [x for x in houses if "titre" not in x]:
        for item in h["equipement"]:
            it = dict(item)
            it["id"] = f"alg-{h['id']}-{item['id']}"
            it["categorie"] = f"Allégeance {h['nom']} : {item['categorie']}"
            it["allegeance"] = h["id"]
            it.pop("roles", None)
            v["equipement"].append(it)
    return v


def main():
    weapons = parse_armes()
    comptoir = parse_comptoir()
    houses = parse_maisons()
    link_weapons(houses, weapons)
    houses.append(build_venators(comptoir, houses))
    houses.append(build_proscrits(comptoir, houses))
    link_weapons(houses[-2:], weapons)

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
        hrules = {**rules, **h.pop("creation", {})}
        hmeta = {**meta, "source": h.pop("source")} if "source" in h else meta
        write(ROOT / "maisons" / f"{h['id']}.json", {**hmeta, "reglesDeCreation": hrules, **h})
    write(ROOT / "index.json", {**meta, "maisons": [{"id": h["id"], "nom": h["nom"], **({"titre": h["titre"]} if "titre" in h else {}),
                                                    "fichier": f"maisons/{h['id']}.json"}
                                                   for h in houses]})

    print(f"armes : {len(weapons)}, comptoir : {len(comptoir)}, maisons : {len(houses)}")
    for w in WARNINGS:
        print("A VERIFIER", w)


if __name__ == "__main__":
    main()
