# Analyse du parc informatique - Projet Data

Pipeline de données complet sur un parc informatique  (équipements et tickets d'incidents) :
génération de données, nettoyage (ETL), stockage SQL et dashboard interactif.

## Objectif
Identifier ce qui génère le plus de pannes dans un parc informatique (type d'équipement, âge, service)
et mesurer l'efficacité du support (taux et durée de résolution).

## Architecture

```
generate_data.py  →  data/raw/*.csv  →  etl.py  →  data/parc_it.db (SQLite)  →  analysis.py  →  app.py (Streamlit)
 (données fictives     (données          (nettoyage,    (tables equipements       (indicateurs      (dashboard
  volontairement        brutes)           validation,    et tickets)               pandas)           interactif)
  "sales")                                chargement)
```

## Technologies
Python · Pandas · NumPy · SQLite · Streamlit

## Ce que fait chaque étape
1. **Génération** (`generate_data.py`) : 300 équipements et ~850 tickets sur 12 mois, avec des erreurs volontaires
   (doublons, valeurs manquantes, casse incohérente, dates invalides).
2. **ETL** (`etl.py`) : suppression des doublons, normalisation du texte, gestion des valeurs manquantes,
   contrôle des dates, vérification de l'intégrité (chaque ticket pointe vers un équipement connu),
   calcul de l'âge des équipements et de la durée de résolution, puis chargement dans SQLite.
   Un rapport de qualité est produit (`data/rapport_qualite.json`).
3. **Analyse** (`analysis.py`) : indicateurs (KPI) et agrégations.
4. **Dashboard** (`app.py`) : filtres par service, type d'équipement et période.

## Lancer le projet
```bash
pip install -r pandas streamlit numpy
python generate_data.py     # crée data/raw/equipements.csv et tickets.csv
python etl.py               # nettoie et crée data/parc_it.db
streamlit run app.py        # ouvre le dashboard
```

## Résultats (sur données simulées)
- 831 tickets analysés après nettoyage ; taux de résolution de 94 % ; durée moyenne de résolution d'environ 30 h.
- Les imprimantes sont les équipements les plus problématiques (environ 4,6 tickets par équipement),
  devant les PC (2,8) et les téléphones IP (2,3).
- Le nombre de pannes par équipement augmente avec l'âge : environ 1,8 pour les équipements de moins de 2 ans,
  contre plus de 4 à partir de 6 ans.
- La durée de résolution dépend fortement de l'urgence : environ 56 h pour une urgence basse, 3 h pour une critique.

