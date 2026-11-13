"""Génère data/n23/mercenaires.json (Aventuriers, Brutes, Bêtes exotiques N23).

Usage : python3 data/n23/src/mercenaires.py data/n23/mercenaires.json
"""
import json, sys
from pathlib import Path

OUT = Path(sys.argv[1])
ARMES = {a["id"] for a in json.load(open(OUT.parent / "armes.json", encoding="utf-8"))["armes"]}
K = ["M", "CC", "CT", "F", "E", "PV", "I", "A", "CD", "SF", "V", "INT"]


def P(s):
    v = s.split()
    assert len(v) == 12, s
    return dict(zip(K, v))


def C(spec):
    res = {"primaires": [], "secondaires": []}
    for part in spec.split(","):
        cat, lvl = part.strip().rsplit(" ", 1)
        res["primaires" if lvl == "P" else "secondaires"].append(cat)
    return res


def R(*pairs):
    return [{"nom": n, "texte": t} for n, t in pairs]


aventuriers = [
    dict(id="toubib-clandestin", nom="Toubib Clandestin", max=2, cout=50, profil=P('5" 5+ 5+ 2 3 1 4+ 1 9+ 8+ 7+ 5+'),
         equipement="Pistolet laser ou flingue ; médikit", competences=["Guérisseur"],
         effet="Une action d'Escorte Médicale gratuite en plus par Toubib à l'après-bataille. Un 6 sur le tableau donne Stabilisé au lieu de Récupération Totale."),
    dict(id="cartouchier", nom="Cartouchier", max=3, cout=50, profil=P('5" 4+ 3+ 3 3 1 5+ 1 9+ 7+ 6+ 7+'),
         equipement="Bolter ou fusil de combat (salve & nuage de grenaille) ; marteau énergétique ou épée énergétique ; armure composite",
         competences=["Armurier"],
         effet="Le gang relance les tests de Munitions ratés sur 1 naturel (1-2 avec deux Cartouchiers, 1-3 avec trois). Bonus perdu s'il est En Récupération ou Capturé."),
    dict(id="coureur-de-domes", nom="Coureur de Dômes", max=1, cout=20, profil=P('5" 5+ 5+ 3 3 1 3+ 1 10+ 9+ 7+ 8+'),
         equipement="Pistolet laser ou flingue ; couteau de combat ou hache", competences=["Profil Bas"],
         effet="Le gang peut relancer le D6 du contenu d'une caisse de butin ; le second résultat est conservé."),
    dict(id="tambouilleur", nom="Tambouilleur", max=1, cout=20, profil=P('4" 4+ 4+ 2 3 1 3+ 1 9+ 9+ 5+ 7+'),
         equipement="Couteau de combat", competences=[],
         effet="Avant-bataille : D6 par combattant En Récupération ; sur 6, il est disponible pour la bataille."),
    dict(id="guetteur-du-gang", nom="Guetteur du Gang", max=1, cout=20, profil=P('5" 5+ 4+ 2 3 1 3+ 1 9+ 7+ 5+ 7+'),
         equipement="Pistolet laser ou flingue ; couteau de combat ou hache", competences=["Zigzag"],
         effet="Escarmouche : +1 au jet attaquant/défenseur. En défense avec Attaque Furtive : +1 aux jets des sentinelles."),
]

brutes = [
    dict(id="ambot", nom='Luther Pattern Excavation Automata ("Ambot")', maison=None, max=2, cout=215,
         profil=P('4" 3+ 5+ 5 5 3 5+ 2 8+ 6+ 8+ 9+'), competences=C("Muscle S, Combat S, Férocité P"),
         armes=["griffes-excavatrices-ambot", "gantelet-a-gravitons-ambot"],
         equipement="Deux griffes excavatrices ; armure carapace légère (Construction Mécanique)",
         options=[("Remplacer 1 griffe excavatrice par un gantelet à gravitons", 70)],
         regles=R(("Infiltration", "Mis de côté au déploiement, puis placé avant le 1er round hors de vue et à plus de 6\" de tout ennemi."),
                  ("Régulateurs Crâniens", "Mode Sécurisé désactivable au début d'un round : gagne Berserk et A = D3+1, mais doit répartir ses attaques entre toutes les figurines au contact, amies comprises. Irréversible."),
                  ("Construction Mécanique", "Équipé d'une armure carapace légère."),
                  ("Automate d'Excavation", "Avec un territoire Mine, un D6 de revenu en plus."),
                  ("Précieux", "S'il est Capturé, le ravisseur peut le vendre ou le garder gratuitement s'il a la Réputation pour un Aventurier de plus."))),
    dict(id="jotunn", nom='"Jotunn" H-Grade Servitor-Ogryn', maison=None, max=2, cout=210,
         profil=P('5" 4+ 5+ 5 5 3 4+ 2 7+ 6+ 8+ 9+'), competences=C("Muscle P, Combat S, Férocité S"),
         armes=["poing-augmentique-jotunn-servitor", "soudeuse-a-l-arc-jotunn-servitor"],
         equipement="Deux poings augmétiques",
         options=[("Remplacer 1 poing augmétique par une soudeuse à l'arc", 70),
                  ("Remplacer 1 poing augmétique par une soudeuse d'assaut (livre Squats Ironhead)", 75),
                  ("Remplacer 1 poing augmétique par une dérouilleuse (livre Squats Ironhead)", -20),
                  ("Plates de fourneau", 15)],
         regles=R(("Coup d'Boule", "Action Coup de Tête (Élémentaire) si Engagé : 2D6 contre l'Endurance de la cible. Un dé ≥ E : touche F+2, D2. Sinon il subit sa propre Force."),
                  ("Loyal", "Ajoute 2 au lieu de 1 quand il assiste un ami en mêlée."),
                  ("Lourdaud", "Jamais activé dans une Activation de Groupe."))),
    dict(id="stig-shambler", nom="Stig-shambler Cawdor", maison="cawdor", max=1, cout=240,
         profil=P('4" 4+ 4+ 5 4 4 4+ 2 9+ 8+ 9+ 8+'), competences=C("Muscle P, Combat S, Ruse S, Savoir P"),
         armes=["matraque-lourde-stig-shambler-cawdor", "haste-cawdor-stig-shambler-cawdor", "mitrailleuse",
                "mitrailleuse-jumelee-stig-shambler-cawdor", "lance-flammes-lourd"],
         equipement="Matraque lourde ; mitrailleuse",
         options=[("Remplacer la matraque lourde par une haste", 0), ("Améliorer la mitrailleuse en mitrailleuse jumelée", 40),
                  ("Remplacer la mitrailleuse par un lance-flammes lourd", 70), ("Armure Flak", 10)],
         regles=R(("Contrôle Intelligent", "Relance immédiate des tests de Commandement, Sang-froid, Volonté et Intelligence ratés."),
                  ("Mouvement et Tir", "Tire avec une arme Encombrante en action Élémentaire, avec -1 supplémentaire à la touche."),
                  ("Mitrailleuse Jumelée", "Peut relancer n'importe quel nombre de dés de Munitions ; le second résultat est conservé."))),
    dict(id="spyker", nom="Spyker Delaque", maison="delaque", max=None, cout=190,
         profil=P('6" 6+ 6+ 3 4 4 3+ 1 5+ 5+ 4+ 6+'), competences=C("Agilité S, Ruse S, Savoir P"),
         armes=[], equipement="Désarmé (attaques désarmées)", competencesDepart=["Psyker Clandestin"],
         options=[("Champ téléporteur", 50)],
         regles=R(("Vol", "Ignore les terrains, change de niveau librement et ne chute jamais. Bloqué par les murs et le terrain infranchissable."),
                  ("Hurlement Psychique (Élémentaire)", "Ennemis à 3\" : test de Nervosité à -1, Démoralisés en cas d'échec."),
                  ("Assaut Psychique (Élémentaire)", "Un ennemi à 18\" fait un test de Volonté : Bloqué s'il réussit, perd 1 PV et Bloqué s'il échoue."),
                  ("Décharge de Force (Élémentaire)", "Ennemis à 3\" repoussés de D3+1\". Contre un mur : Bloqué et touche de Force égale à la distance."))),
    dict(id="khimerix", nom="Khimerix Escher", maison="escher", max=1, cout=220,
         profil=P('6" 4+ 4+ 4 5 3 3+ 3 8+ 7+ 7+ 8+'), competences=C("Agilité S, Combat S, Férocité P"),
         armes=["souffle-a-nuage-chimique-khimerix-escher", "souffle-a-eruption-gazeuse-khimerix-escher",
                "griffes-khimerix-escher-et-phyrr-cat-escher", "griffes-rasoirs-khimerix-escher"],
         equipement="Souffle à nuage chimique ; griffes",
         options=[("Remplacer le souffle à nuage chimique par un souffle à éruption gazeuse", 80),
                  ("Améliorer les griffes en griffes-rasoirs", 30), ("Peau endurcie (compte comme armure Flak)", 10)],
         regles=R(("Régénération (Simple)", "Sans pion Incendie : D6, sur 4+ récupère 1 PV."),
                  ("Coup Destructeur", "Avant les jets de touche en mêlée, un dé désigné gagne +1 en Force et en Dégâts."))),
    dict(id="zerker", nom="'Zerker Goliath", maison="goliath", max=1, cout=210,
         profil=P('4" 3+ 6+ 6 5 3 5+ 3 7+ 6+ 8+ 10+'), competences=C("Muscle P, Combat S, Férocité S"),
         armes=["mains-nues-zerker-goliath", "poings-mutants-excroissances-osseuses-zerker-goliath"],
         equipement="Deux mains nues",
         options=[("Poings mutants & excroissances osseuses", 70), ("Plates de fourneau", 10), ("Planque de stim'", 20)],
         regles=R(("Planque de Drogues de Combat", "À chaque activation : +D3 Attaques jusqu'à la fin du tour. Sur 1 naturel, A tombe à 1 jusqu'à la fin du round."),
                  ("Impétuosité", "Consolide de 4\" au lieu de 2\" après un corps à corps."))),
    dict(id="lugger", nom='"Lugger" Cargo Servitor Orlock', maison="orlock", max=1, cout=230,
         profil=P('4" 5+ 4+ 5 5 3 5+ 2 7+ 5+ 9+ 8+'), competences=C("Muscle S, Combat S, Tir P"),
         armes=["lance-harpon", "bolter-lourd", "lance-flammes-lourd", "mitrailleuse", "arme-de-melee-de-servitor-orlock-lugger"],
         equipement="Lance-harpon ; armure carapace légère (Construction Mécanique)",
         options=[("Remplacer le lance-harpon par un bolter lourd", 50), ("Remplacer le lance-harpon par un lance-flammes lourd", 85),
                  ("Remplacer le lance-harpon par une mitrailleuse", 20), ("Armure carapace lourde au lieu de légère", 20), ("Lunette", 25)],
         regles=R(("Construction Mécanique", "Équipé d'une armure carapace légère."),
                  ("Plate-forme d'Armes", "Tirer avec une arme Encombrante est une action Élémentaire au lieu de Double."),
                  ("Trémies à Munitions", "Relance les tests de Munitions ratés sur 1 naturel."))),
    dict(id="arachni-rig", nom='"Arachni-rig" Servo-suit Van Saar', maison="van-saar", max=1, cout=240,
         profil=P('5" 4+ 4+ 5 4 3 4+ 4 5+ 5+ 8+ 6+'), competences=C("Muscle S, Férocité S, Tir P"),
         armes=["carabine-laser-lourde-jumelee-arachnirig-van-saar", "fusil-a-radiations", "fusil-a-plasma", "servobras-servo-suit-van-saar"],
         equipement="Carabine laser lourde jumelée ; quatre servobras ; armure carapace légère (Construction Mécanique)",
         options=[("Remplacer 1 servobras par un fusil à radiations (-1 A)", 60), ("Remplacer 1 servobras par un fusil à plasma (-1 A)", 60),
                  ("Armure carapace lourde au lieu de légère", 20)],
         regles=R(("Carabine Laser Jumelée", "Peut relancer n'importe quel nombre de dés de Munitions ; le second résultat est conservé."),
                  ("Construction Mécanique", "Équipée d'une armure carapace légère."),
                  ("Tenue Protectrice Van Saar", "Immunisée aux effets du trait Radiations."),
                  ("Panoplie d'Armes Supérieure", "Deux actions Tirer (Simple) par tour au lieu d'une Tirer (Élémentaire), avec des armes et des cibles différentes possibles."))),
]

brutes += [
    dict(id="exo-foreuse-vartijan", nom="Exo-Foreuse Vartijan Squat Ironhead", maison="squats", max=2, cout=250,
         profil=P('4" 4+ 3+ 4 5 3 5+ 2 7+ 6+ 6+ 7+'), competences=C("Muscle S, Férocité P, Tir S, Sagesse des Anciens P"),
         armes=["poing-vartijan-exo-foreuse-squat", "lance-flammes-lourd-vartijan-exo-foreuse-squat",
                "broyeur-sismique-exo-foreuse-squat", "bolter-lourd-vartijan-exo-foreuse-squat"],
         competencesDepart=["Personne Ne Bouscule Le Frère"],
         equipement="Poing Vartijan ; lance-flammes lourd Vartijan ; broyeur sismique ; armure carapace légère",
         options=[("Remplacer le lance-flammes lourd Vartijan par un bolter lourd Vartijan", 50)],
         regles=R(("Exo-Armure Sentinelle", "Peut toujours être déployée comme sentinelle en plus, même au-delà de la taille d'équipe."),
                  ("Combinaison de Senseurs", "Traite la règle Visibilité (X) comme 3\" plus haute."))),
    dict(id="fouisseur-de-dunes", nom="Fouisseur de Dunes Arthromite", maison="nomades", max=2, cout=210,
         profil=P('6" 3+ 5+ 5 5 3 3+ 4 7+ 8+ 8+ 8+'), competences=C("Agilité S, Combat P, Férocité S"),
         armes=["mandibules-fouisseur-de-dunes-arthromite"], competencesDepart=["Effrayant", "Nerfs d'Acier"],
         equipement="Mandibules ; armure carapace lourde",
         regles=R(("Sabordeur de Mur", "Ne divise pas la distance verticale en escalade : compte toujours comme une échelle."),
                  ("Difficile à Tuer", "Sur le tableau des Blessures Persistantes, deux jets ; le joueur choisit le résultat."))),
    dict(id="belluaire", nom="Belluaire de l'Outreterre", maison=None, max=2, cout=100,
         profil=P('6" 4+ 4+ 3 3 2 3+ 1 7+ 6+ 7+ 8+'), competences=C("Agilité P, Muscle S, Ruse S, Férocité P"),
         armes=["electrosceptre", "fusil-a-canon-scie"], competencesDepart=["Effrayant", "+ Esquive (rats), Infiltration (centipattes) ou Réception Féline (lamias)"],
         equipement="Électrosceptre ; fusil à canon scié (balles & grenaille) ; armure composite",
         options=[("Rat Géant des Désolations (bête)", 30), ("Centipatte (bête)", 60), ("Lamia (bête)", 70)],
         note="Moins de trois Bêtes : peut en acheter d'autres à son recrutement ou au début des Actions d'Après-bataille. Voir Rat Géant, Centipatte et Lamia dans les Bêtes exotiques.",
         regles=R(("Dresseur de Bêtes", "Ses bêtes restent à 6\" de lui au lieu de 3\"."),
                  ("Un avec la Bête", "Choisit une spécialité au recrutement (rats, centipattes ou lamias) et n'a que des bêtes de ce type."))),
]

betes = [
    dict(id="sheen-bird", nom="Sheen Bird", maison="cawdor", max=2, cout=90, rarete="Rare (12)",
         profil=P('6" 4+ 6+ 3 2 1 3+ 2 8+ 7+ 8+ 9+'), competences=C("Agilité S, Férocité P"), armes=["bec-serres-sheen-bird-cawdor"],
         regles=R(("Vol", "Ignore les terrains, change de niveau librement et ne chute jamais."),
                  ("Agressif", "Quand son propriétaire est activé, test de Volonté du propriétaire ; en cas d'échec, l'oiseau charge l'ennemi le plus proche."),
                  ("Rappel", "En fin d'activation, test de Volonté du propriétaire : réussite, l'oiseau revient vers lui (Se Déplacer ou Se Replier gratuit)."))),
    dict(id="cephalopod-spekter", nom="Cephalopod Spekter", maison="delaque", max=1, cout=100, rarete="Rare (11)",
         profil=P('5" 4+ 5+ 3 3 1 3+ 1 7+ 5+ 6+ 4+'), competences=C("Agilité S, Ruse P"), armes=["electrovrilles-cephalopod-spekter-delaque"],
         regles=R(("Vol", "Ignore les terrains, change de niveau librement et ne chute jamais."),
                  ("Panoplie de Senseurs", "À 3\" du propriétaire, celui-ci jette un D6 de plus aux tests d'Intelligence et défausse un dé."),
                  ("Réponse à la Menace", "Si le propriétaire est Hors de Combat à 3\", touche automatique F1 Sismique sur les ennemis à D6\"."),
                  ("Chien de Garde", "Propriétaire sentinelle : détecte hors champ de vision, +1 au jet de détection."))),
    dict(id="phyrr-cat", nom="Phyrr Cat", maison="escher", max=2, cout=120, rarete="Rare (12)",
         profil=P('7" 3+ - 3 3 1 2+ 2 7+ 8+ 7+ 8+'), competences=C("Agilité P, Ruse S"), armes=["griffes-khimerix-escher-et-phyrr-cat-escher"],
         regles=R(("Indépendant", "Doit rester à 9\" du propriétaire au lieu de 3\"."),
                  ("Retombe sur ses Pattes", "Force des chutes réduite de 2."))),
    dict(id="sumpkroc", nom="Sumpkroc", maison="goliath", max=1, cout=130, rarete="Rare (11)",
         profil=P('4" 3+ - 4 4 2 6+ 2 8+ 6+ 7+ 11+'), competences=C("Muscle P, Férocité S"), armes=["machoires-feroces-sumpkroc-goliath"],
         regles=R(("Contre-charge", "Si son propriétaire est chargé, il peut charger aussitôt l'assaillant et l'attaquer avant ses attaques. Une fois par round."),
                  ("Peau Écailleuse", "Sauvegarde de 5+."))),
    dict(id="cyber-mastiff", nom="Cyber-mastiff", maison="orlock", max=3, cout=100, rarete="Rare (10)",
         profil=P('5" 3+ - 3 3 1 4+ 1 7+ 6+ 8+ 8+'), competences=C("Combat P, Férocité S"), armes=["morsure-sauvage-cyber-mastiff"],
         regles=R(("Chien de Garde", "Propriétaire sentinelle : détecte hors champ de vision, +1 au jet de détection."),
                  ("Fidèle Protecteur", "Debout à 3\" du propriétaire : les ennemis ne peuvent pas lui porter le Coup de Grâce."))),
    dict(id="cyberachnid", nom="Cyberachnid", maison="van-saar", max=3, cout=75, rarete="Rare (10)",
         profil=P('6" 4+ 5+ 2 2 1 2+ 1 7+ 8+ 8+ 8+'), competences=C("Agilité S, Ruse P"),
         armes=["morsure-venimeuse-cyberachnid-van-saar", "projecteur-de-toile-cyberachnid-van-saar"],
         regles=R(("Escalade", "Ne divise pas la distance verticale : compte toujours comme une échelle."),
                  ("Suscite la Phobie", "A la compétence Effrayant et la confère à son propriétaire tant qu'il est Actif à 3\"."),
                  ("Horrible", "Ne peut jamais être Capturé."))),
    dict(id="rat-geant", nom="Rat Géant des Désolations", maison=None, acces="Belluaire de l'Outreterre seulement (3 bêtes max.)", max=None, cout=30,
         profil=P('5" 4+ 5+ 3 3 1 3+ 1 8+ 7+ 8+ 7+'), competences=C("Agilité P, Ruse S"), armes=["crocs-rat-geant-des-desolations"],
         regles=R(("Sacrifiable", "S'il est Gravement Blessé ou Hors de Combat, les amis à 3\" ne font pas de test de Nervosité (sauf s'ils sont aussi Sacrifiables)."),
                  ("Jamais à plus d'Un Mètre d'un Rat", "Les rats retirés de la carte à l'après-bataille sont remplacés gratuitement."),
                  ("Instinct de Survie", "A la compétence Esquive."))),
    dict(id="centipatte", nom="Centipatte", maison=None, acces="Belluaire de l'Outreterre seulement (3 bêtes max.)", max=None, cout=60,
         profil=P('6" 4+ 5+ 3 3 2 4+ 2 8+ 7+ 7+ 8+'), competences=C("Agilité S, Ruse P"), armes=["gueule-crochue-centipatte"],
         regles=R(("Enfouissement", "Traverse librement le terrain infranchissable s'il a assez de mouvement, sans pouvoir y finir."),
                  ("Prédateur Embusqué", "A la compétence Infiltration."),
                  ("Cuirasse Blindée", "Sauvegarde d'armure de 5+."))),
    dict(id="lamia", nom="Lamia", maison=None, acces="Belluaire de l'Outreterre seulement (3 bêtes max.)", max=None, cout=70,
         profil=P('7" 4+ 6+ 3 3 2 3+ 2 8+ 7+ 8+ 8+'), competences=C("Combat S, Férocité P"), armes=["dents-lamia"],
         regles=R(("Vol", "Ignore les terrains, change de niveau librement et ne chute jamais."),
                  ("Chasseur Solitaire", "Ne donne et ne reçoit jamais d'assistance."),
                  ("Attaque Enveloppante", "Ennemi engagé : -2 à l'Initiative pour Retraite. Attaques de réaction contre elle : -1 à la touche."))),
    dict(id="caryatid", nom="Caryatid", maison=None, max=1, cout=0, rarete="Rare (15)",
         profil=P('6" 5+ - 2 2 1 2+ 1 7+ 7+ 8+ 8+'), competences=C("Agilité P, Ruse S"), armes=[],
         note="Ne s'achète pas : après une recherche d'Équipement Rare à 15+, 2D6 + Réputation ≥ 20 et elle se lie au Chef. Attaques désarmées uniquement.",
         regles=R(("De Bon Augure", "À 3\" du propriétaire : une fois par tour, test de Volonté pour annuler une touche subie."),
                  ("Précognition", "Sauvegarde de 3+ non modifiable. Sous un gabarit d'Explosion ou de Souffle, touchée seulement sur 4+ au D6."),
                  ("Symbole de Renom", "+1 Réputation tant qu'elle accompagne le Chef ; -2 si elle meurt ou part."),
                  ("Abandon", "Si le gang perd de la Réputation : D6 moins la perte, sur 1 ou moins elle part (6 naturel : reste)."),
                  ("Vol", "Ignore les terrains, change de niveau librement et ne chute jamais."))),
]

for lst in (brutes, betes):
    for m in lst:
        for a in m.get("armes", []):
            assert a in ARMES, (m["id"], a)
        if "options" in m:
            m["options"] = [{"nom": n, "cout": c} for n, c in m["options"]]

data = {
    "edition": "Necromunda N23",
    "source": "Livre de règles N23 (version française), Aventuriers et Brutes, Bêtes Exotiques",
    "recrutement": {
        "texte": "Recrutés à l'après-bataille avec les crédits du Magot. Ils ne comptent pas dans le nombre de combattants du gang. Le nombre total d'Aventuriers et de Brutes dépend de la Réputation.",
        "limites": [["Moins de 5", 1], ["5-9", 2], ["10-14", 3], ["15-19", 4], ["20-24", 5], ["Par tranche de 5 au-delà", "+1"]],
    },
    "aventuriers": {
        "texte": "Ne combattent normalement pas. Sur le territoire du gang, D6 par Aventurier : sur 1-3 il est inclus dans l'équipe. Pas d'Expérience ; une Blessure Persistante le fait partir. Aucun équipement en plus.",
        "liste": aventuriers,
    },
    "brutes": {
        "texte": "Combattent comme n'importe quel combattant. Gagnent Expérience et Progressions comme un Ganger Spécialiste et restent malgré les Blessures Persistantes. Aucun équipement en plus de leurs options.",
        "liste": brutes,
    },
    "betes": {
        "texte": "Achetées comme de l'Équipement, par le Chef ou un Champion seulement. Activées avec leur propriétaire et doivent finir à 3\" de lui. Démoralisées, elles courent vers lui. Retirées s'il est retiré. Expérience comme un Ganger, pas d'équipement.",
        "tableauCompetences": {
            "Agilité": ["Réception Féline", "Esquive", "Sprint"],
            "Muscle": ["Charge Buffle", "Coup Destructeur", "Gueule de Fer"],
            "Combat": ["Contre-attaque", "Désarmement", "Saut de Côté"],
            "Ruse": ["Coup en Traître", "Zigzag", "Profil Bas"],
            "Férocité": ["Berserk", "Effrayant", "Nerfs d'Acier"],
        },
        "liste": betes,
    },
}
OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(len(aventuriers), len(brutes), len(betes))
