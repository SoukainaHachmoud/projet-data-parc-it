"""Étape 1 : génération de données FICTIVES du parc informatique (avec des erreurs volontaires).

Les données sont volontairement "sales" (doublons, valeurs manquantes, casse incohérente,
dates invalides) pour que l'étape de nettoyage (etl.py) ait un vrai travail à faire.
"""
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)  # graine fixe : résultats reproductibles
RAW = Path(__file__).parent / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

SERVICES = ["Direction", "Secrétariat", "Ressources Humaines", "Comptabilité",
            "Production", "Logistique", "Commercial", "Qualité"]
TYPES = ["PC", "Imprimante", "Switch", "Routeur", "Téléphone IP"]
TYPE_PROBS = [0.45, 0.20, 0.10, 0.05, 0.20]
# nombre moyen de pannes par an selon le type d'équipement
TYPE_RATE = {"PC": 1.0, "Imprimante": 1.8, "Switch": 0.4, "Routeur": 0.3, "Téléphone IP": 0.8}
MARQUES = {"PC": ["Dell", "HP", "Lenovo"], "Imprimante": ["HP", "Canon", "Epson"],
           "Switch": ["Cisco", "TP-Link"], "Routeur": ["Cisco", "MikroTik"],
           "Téléphone IP": ["Yealink", "Cisco", "Grandstream"]}
CATEGORIES = {"PC": ["Matériel", "Logiciel"], "Imprimante": ["Matériel"],
              "Switch": ["Réseau"], "Routeur": ["Réseau"], "Téléphone IP": ["Téléphonie IP"]}
URGENCES = ["Basse", "Moyenne", "Haute", "Critique"]
BASE_HEURES = {"Basse": 48, "Moyenne": 24, "Haute": 8, "Critique": 3}

START = pd.Timestamp("2025-11-01")
END = pd.Timestamp("2026-10-31")
REF = pd.Timestamp("2026-11-01")

# ---------- Équipements ----------
N_EQ = 300
types = rng.choice(TYPES, size=N_EQ, p=TYPE_PROBS)
achat = pd.to_datetime("2018-01-01") + pd.to_timedelta(rng.integers(0, 3100, size=N_EQ), unit="D")
equipements = pd.DataFrame({
    "equipement_id": [f"EQ{i:04d}" for i in range(1, N_EQ + 1)],
    "type": types,
    "marque": [rng.choice(MARQUES[t]) for t in types],
    "service": rng.choice(SERVICES, size=N_EQ),
    "date_achat": achat.strftime("%Y-%m-%d"),
})

# ---------- Tickets (plus de pannes sur les équipements anciens) ----------
rows = []
tid = 1
for _, eq in equipements.iterrows():
    age = (REF - pd.Timestamp(eq["date_achat"])).days / 365.25
    n = rng.poisson(TYPE_RATE[eq["type"]] * (1 + 0.35 * age) * 1.1)
    for _ in range(n):
        low = max(START, pd.Timestamp(eq["date_achat"]))
        span = (END - low).days
        if span <= 0:
            continue
        created = low + pd.to_timedelta(int(rng.integers(0, span)), unit="D") \
            + pd.to_timedelta(int(rng.integers(8 * 60, 18 * 60)), unit="m")
        p_crit = 0.2 if eq["type"] in ("Switch", "Routeur") else 0.08
        probs = np.array([0.3, 0.4, 0.3 - p_crit, p_crit])
        urg = rng.choice(URGENCES, p=probs / probs.sum())
        hours = float(BASE_HEURES[urg] * rng.lognormal(0, 0.5))
        resolved = created + pd.to_timedelta(hours, unit="h")
        statut = rng.choice(["Résolu", "Fermé"], p=[0.6, 0.4])
        if created > pd.Timestamp("2026-10-20") or rng.random() < 0.03:
            statut = rng.choice(["Nouveau", "En cours"])
            resolved = pd.NaT
        rows.append({
            "ticket_id": f"T{tid:05d}",
            "equipement_id": eq["equipement_id"],
            "date_creation": created.strftime("%Y-%m-%d %H:%M"),
            "date_resolution": resolved.strftime("%Y-%m-%d %H:%M") if pd.notna(resolved) else "",
            "categorie": rng.choice(CATEGORIES[eq["type"]]),
            "urgence": urg,
            "statut": statut,
        })
        tid += 1
tickets = pd.DataFrame(rows)

# ---------- Salissage volontaire ----------
# équipements : doublons, services manquants, casse incohérente
equipements = pd.concat([equipements, equipements.sample(8, random_state=1)], ignore_index=True)
equipements.loc[equipements.sample(12, random_state=2).index, "service"] = np.nan
for idx in equipements.sample(15, random_state=3).index:
    equipements.loc[idx, "type"] = rng.choice([equipements.loc[idx, "type"].lower(),
                                               " " + equipements.loc[idx, "type"] + " ",
                                               equipements.loc[idx, "type"].upper()])

# tickets : doublons, urgences mal écrites, dates invalides ou incohérentes
tickets = pd.concat([tickets, tickets.sample(15, random_state=4)], ignore_index=True)
for idx in tickets.sample(20, random_state=5).index:
    tickets.loc[idx, "urgence"] = rng.choice([tickets.loc[idx, "urgence"].lower(),
                                              tickets.loc[idx, "urgence"].upper() + " "])
bad = tickets[tickets["date_resolution"] != ""].sample(10, random_state=6).index
tickets.loc[bad, "date_resolution"] = tickets.loc[bad, "date_creation"].str.replace(
    r"^(\d{4})-(\d{2})-(\d{2})", lambda m: f"{m.group(1)}-{m.group(2)}-01", regex=True)  # avant la création
tickets.loc[tickets.sample(6, random_state=7).index, "date_creation"] = "N/A"

equipements.to_csv(RAW / "equipements.csv", index=False)
tickets.to_csv(RAW / "tickets.csv", index=False)
print(f"OK : {len(equipements)} lignes équipements, {len(tickets)} lignes tickets -> {RAW}")
