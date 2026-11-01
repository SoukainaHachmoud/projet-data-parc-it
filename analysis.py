"""Étape 3 : fonctions d'analyse (pandas) utilisées par le dashboard."""
import sqlite3
from pathlib import Path

import pandas as pd

DB = Path(__file__).parent / "data" / "parc_it.db"
ORDRE_URGENCE = ["Basse", "Moyenne", "Haute", "Critique"]


def load_data(db_path: Path = DB):
    """Retourne (tickets_enrichis, equipements)."""
    with sqlite3.connect(db_path) as conn:
        eq = pd.read_sql("SELECT * FROM equipements", conn)
        tk = pd.read_sql("SELECT * FROM tickets", conn, parse_dates=["date_creation", "date_resolution"])
    tk = tk.merge(eq[["equipement_id", "type", "marque", "service", "age_ans"]],
                  on="equipement_id", how="left")
    return tk, eq


def kpis(tk: pd.DataFrame) -> dict:
    total = len(tk)
    resolus = tk["statut"].isin(["Résolu", "Fermé"]).sum()
    return {
        "tickets": total,
        "taux_resolution": float(round(100 * resolus / total, 1)) if total else 0.0,
        "duree_moyenne_h": float(round(tk["duree_resolution_h"].mean(), 1)) if total else 0.0,
        "critiques": int((tk["urgence"] == "Critique").sum()),
    }


def tickets_par_mois(tk: pd.DataFrame) -> pd.Series:
    return tk.groupby("mois").size().sort_index()


def tickets_par_categorie(tk: pd.DataFrame) -> pd.Series:
    return tk.groupby("categorie").size().sort_values(ascending=False)


def pannes_par_equipement_selon_type(tk: pd.DataFrame, eq: pd.DataFrame) -> pd.Series:
    """Nombre moyen de tickets par équipement, pour chaque type d'équipement."""
    n_eq = eq.groupby("type").size()
    n_tk = tk.groupby("type").size()
    return (n_tk / n_eq).dropna().round(2).sort_values(ascending=False)


def duree_moyenne_par_urgence(tk: pd.DataFrame) -> pd.Series:
    s = tk.groupby("urgence")["duree_resolution_h"].mean().round(1)
    return s.reindex([u for u in ORDRE_URGENCE if u in s.index])


def pannes_par_tranche_age(tk: pd.DataFrame, eq: pd.DataFrame) -> pd.Series:
    bins = [0, 2, 4, 6, 8, 20]
    labels = ["0-2 ans", "2-4 ans", "4-6 ans", "6-8 ans", "8+ ans"]
    eq = eq.assign(tranche=pd.cut(eq["age_ans"], bins=bins, labels=labels, include_lowest=True))
    tk = tk.assign(tranche=pd.cut(tk["age_ans"], bins=bins, labels=labels, include_lowest=True))
    n_eq = eq.groupby("tranche", observed=True).size()
    n_tk = tk.groupby("tranche", observed=True).size()
    return (n_tk / n_eq).dropna().round(2)


def tickets_par_service(tk: pd.DataFrame) -> pd.Series:
    return tk.groupby("service").size().sort_values(ascending=False)


def top_equipements(tk: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    return (tk.groupby(["equipement_id", "type", "marque", "service"]).size()
            .reset_index(name="nb_tickets").sort_values("nb_tickets", ascending=False).head(n))


if __name__ == "__main__":  # petit test en ligne de commande
    tk, eq = load_data()
    print(kpis(tk))
    print(pannes_par_equipement_selon_type(tk, eq))
    print(pannes_par_tranche_age(tk, eq))
    print(duree_moyenne_par_urgence(tk))
    print(tickets_par_categorie(tk))
