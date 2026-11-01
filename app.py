"""Étape 4 : dashboard Streamlit.  Lancer avec :  streamlit run app.py"""
import json
from pathlib import Path

import streamlit as st

import analysis as an

st.set_page_config(page_title="Analyse du parc informatique", layout="wide")
st.title("Analyse du parc informatique")

if not an.DB.exists():
    st.error("Base introuvable. Lance d'abord : python generate_data.py puis python etl.py")
    st.stop()


@st.cache_data
def get_data():
    return an.load_data()


tk_all, eq_all = get_data()

# ---------- Filtres ----------
st.sidebar.header("Filtres")
services = st.sidebar.multiselect("Service", sorted(eq_all["service"].unique()),
                                  default=sorted(eq_all["service"].unique()))
types = st.sidebar.multiselect("Type d'équipement", sorted(eq_all["type"].unique()),
                               default=sorted(eq_all["type"].unique()))
mois_dispo = sorted(tk_all["mois"].unique())
debut, fin = st.sidebar.select_slider("Période (mois)", options=mois_dispo,
                                      value=(mois_dispo[0], mois_dispo[-1]))

eq = eq_all[eq_all["service"].isin(services) & eq_all["type"].isin(types)]
tk = tk_all[tk_all["service"].isin(services) & tk_all["type"].isin(types)
            & (tk_all["mois"] >= debut) & (tk_all["mois"] <= fin)]

if tk.empty:
    st.warning("Aucun ticket pour ces filtres.")
    st.stop()

# ---------- KPI ----------
k = an.kpis(tk)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Tickets", k["tickets"])
c2.metric("Taux de résolution", f"{k['taux_resolution']} %")
c3.metric("Durée moyenne de résolution", f"{k['duree_moyenne_h']} h")
c4.metric("Tickets critiques", k["critiques"])

st.divider()

# ---------- Graphiques ----------
left, right = st.columns(2)
with left:
    st.subheader("Tickets par mois")
    st.line_chart(an.tickets_par_mois(tk))
    st.subheader("Pannes moyennes par équipement, selon le type")
    st.bar_chart(an.pannes_par_equipement_selon_type(tk, eq))
    st.subheader("Tickets par service")
    st.bar_chart(an.tickets_par_service(tk))
with right:
    st.subheader("Tickets par catégorie")
    st.bar_chart(an.tickets_par_categorie(tk))
    st.subheader("Pannes moyennes par équipement, selon l'âge")
    st.bar_chart(an.pannes_par_tranche_age(tk, eq))
    st.subheader("Durée moyenne de résolution (h) par urgence")
    st.bar_chart(an.duree_moyenne_par_urgence(tk))

st.subheader("Top 10 des équipements les plus problématiques")
st.dataframe(an.top_equipements(tk), use_container_width=True, hide_index=True)

# ---------- Qualité des données ----------
rapport = Path(__file__).parent / "data" / "rapport_qualite.json"
if rapport.exists():
    with st.expander("Rapport de qualité des données (nettoyage ETL)"):
        st.json(json.loads(rapport.read_text(encoding="utf-8")))
