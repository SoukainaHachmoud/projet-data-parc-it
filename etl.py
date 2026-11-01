"""Étape 2 : ETL (Extract - Transform - Load).

Extract  : lecture des CSV bruts (data/raw)
Transform: nettoyage (doublons, casse, valeurs manquantes, dates invalides) + nouvelles colonnes
Load     : chargement dans une base SQLite (data/parc_it.db)
Un rapport de qualité des données est affiché et sauvegardé.
"""
import json
import sqlite3
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent / "data"
RAW = BASE / "raw"
DB = BASE / "parc_it.db"
REF_DATE = pd.Timestamp("2026-11-01")

TYPE_MAP = {"pc": "PC", "imprimante": "Imprimante", "switch": "Switch",
            "routeur": "Routeur", "téléphone ip": "Téléphone IP"}


def clean_equipements(df: pd.DataFrame, report: dict) -> pd.DataFrame:
    report["equipements_lignes_brutes"] = len(df)
    df = df.drop_duplicates(subset="equipement_id").copy()
    report["equipements_doublons_supprimes"] = report["equipements_lignes_brutes"] - len(df)

    df["type"] = df["type"].str.strip().str.lower().map(TYPE_MAP)
    report["equipements_type_inconnu"] = int(df["type"].isna().sum())
    df = df.dropna(subset=["type"]).copy()

    report["equipements_service_manquant"] = int(df["service"].isna().sum())
    df["service"] = df["service"].fillna("Non renseigné")

    df["date_achat"] = pd.to_datetime(df["date_achat"], errors="coerce")
    df["age_ans"] = ((REF_DATE - df["date_achat"]).dt.days / 365.25).round(1)
    report["equipements_lignes_propres"] = len(df)
    return df


def clean_tickets(df: pd.DataFrame, equipements: pd.DataFrame, report: dict) -> pd.DataFrame:
    report["tickets_lignes_brutes"] = len(df)
    df = df.drop_duplicates(subset="ticket_id").copy()
    report["tickets_doublons_supprimes"] = report["tickets_lignes_brutes"] - len(df)

    df["urgence"] = df["urgence"].str.strip().str.capitalize()

    df["date_creation"] = pd.to_datetime(df["date_creation"], errors="coerce", format="mixed")
    df["date_resolution"] = pd.to_datetime(df["date_resolution"], errors="coerce", format="mixed")

    report["tickets_date_creation_invalide"] = int(df["date_creation"].isna().sum())
    df = df.dropna(subset=["date_creation"]).copy()

    incoherent = df["date_resolution"] < df["date_creation"]
    report["tickets_resolution_avant_creation"] = int(incoherent.sum())
    df.loc[incoherent, "date_resolution"] = pd.NaT

    # intégrité référentielle : le ticket doit pointer vers un équipement connu
    orphelins = ~df["equipement_id"].isin(equipements["equipement_id"])
    report["tickets_equipement_inconnu"] = int(orphelins.sum())
    df = df[~orphelins].copy()

    df["duree_resolution_h"] = ((df["date_resolution"] - df["date_creation"])
                                .dt.total_seconds() / 3600).round(1)
    df["mois"] = df["date_creation"].dt.to_period("M").astype(str)
    report["tickets_lignes_propres"] = len(df)
    return df


def main() -> None:
    report: dict = {}
    eq = pd.read_csv(RAW / "equipements.csv")
    tk = pd.read_csv(RAW / "tickets.csv")

    eq = clean_equipements(eq, report)
    tk = clean_tickets(tk, eq, report)

    DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB) as conn:
        eq.assign(date_achat=eq["date_achat"].dt.strftime("%Y-%m-%d")).to_sql(
            "equipements", conn, if_exists="replace", index=False)
        tk.assign(date_creation=tk["date_creation"].dt.strftime("%Y-%m-%d %H:%M"),
                  date_resolution=tk["date_resolution"].dt.strftime("%Y-%m-%d %H:%M")).to_sql(
            "tickets", conn, if_exists="replace", index=False)

    (BASE / "rapport_qualite.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("=== Rapport de qualité des données ===")
    for k, v in report.items():
        print(f"{k:40s} {v}")
    print(f"\nBase SQLite créée : {DB}")


if __name__ == "__main__":
    main()
