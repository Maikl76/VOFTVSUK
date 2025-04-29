import streamlit as st
import pandas as pd
import datetime
from io import BytesIO
from supabase import create_client, Client
import json

# ===== KONFIGURACE SUPABASE =====
SUPABASE_URL = st.secrets["supabase"]["supabase_url"]
SUPABASE_KEY = st.secrets["supabase"]["supabase_key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# =================================

def safe_rerun():
    try:
        st.experimental_rerun()
    except AttributeError:
        pass


def load_data():
    response = supabase.table("dpp_planovani").select("data").eq("id", 1).execute()
    if response.data and "data" in response.data[0]:
        return response.data[0]["data"]
    else:
        return {}


def save_data(data):
    return supabase.table("dpp_planovani").update({"data": data}).eq("id", 1).execute()


def load_budget():
    response = supabase.table("dpp_budget").select("value").eq("id", 1).execute()
    if response.data:
        return response.data[0]["value"]
    else:
        return 0.0


def save_budget(budget):
    return supabase.table("dpp_budget").update({"value": budget}).eq("id", 1).execute()


def load_history():
    response = supabase.table("dpp_historie").select("data").eq("id", 1).execute()
    if response.data and "data" in response.data[0]:
        return response.data[0]["data"]
    else:
        return {}


def save_history(history):
    return supabase.table("dpp_historie").update({"data": history}).eq("id", 1).execute()


def hr():
    st.markdown("<hr style='border-top: 3px solid #fff;'>", unsafe_allow_html=True)


def run_dpp():
    st.title("Plánování DPP")
    st.markdown("##### Plánování dohod o pracovní činnosti pro aktuální rok")

    cols = st.columns([1, 3])
    with cols[0]:
        if st.button("Aktualizovat", key="dpp_update"):
            safe_rerun()
    with cols[1]:
        st.markdown("**Klikni pro aktualizaci a zobrazení změn**")

    # Načtení dat z session state nebo Supabase
    if "dpp_data" not in st.session_state:
        st.session_state.dpp_data = load_data()
    data = st.session_state.dpp_data

    if "dpp_total_budget" not in st.session_state:
        st.session_state.dpp_total_budget = load_budget()

    current_year = datetime.datetime.now().year

    hr()
    st.subheader("Přidat novou akci")
    with st.form("dpp_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            provede = st.text_input("Provede", placeholder="Jméno a příjmení osoby")
            nazev_akce = st.text_input("Název akce", placeholder="Popis činnosti")
            zadal = st.text_input("Zadal", placeholder="Jméno zadavatele")
        with col2:
            cena_h = st.number_input("Cena/h", min_value=0.0, step=1.0, format="%.2f")
            pocet_h = st.number_input("Pč/h", min_value=0.0, step=1.0, format="%.2f")
            poznamka = st.text_input("Poznámka")
        submitted = st.form_submit_button("➕ Přidat akci")
        if submitted:
            nova_akce = {
                "Provede": provede,
                "Název akce": nazev_akce,
                "Cena/h": cena_h,
                "Pč/h": pocet_h,
                "Cena": round(cena_h * pocet_h, 2),
                "Zadal": zadal,
                "Poznámka": poznamka
            }
            if str(current_year) not in data:
                data[str(current_year)] = []
            data[str(current_year)].append(nova_akce)
            save_data(data)
            st.success("Akce byla přidána!")
            safe_rerun()

    hr()
    st.subheader("Přehled záznamů DPP")
    # Vytvoření DataFrame pro aktuální rok
    if str(current_year) in data:
        df = pd.DataFrame(data[str(current_year)])
    else:
        df = pd.DataFrame()

    if df.empty or "Cena" not in df.columns:
        st.info("Zatím nebyly přidány žádné akce.")
    else:
        # Zobrazení tabulky
        table_height = 40 * (len(df) + 1)
        st.dataframe(df, use_container_width=True, height=table_height)

        hr()
        st.markdown("##### Mazání řádku")
        row_to_delete = st.selectbox(
            "Vyberte řádek k odstranění",
            options=df.index,
            key="dpp_select_delete",
            format_func=lambda idx: f"{df.loc[idx, 'Provede']} - {df.loc[idx, 'Název akce']}"
        )
        if st.button("❌ Smazat vybraný řádek", key="dpp_delete_row"):
            data[str(current_year)].pop(row_to_delete)
            save_data(data)
            st.success("Řádek byl smazán!")
            safe_rerun()

        hr()
        st.subheader("Upravit existující záznam")
        idx_to_edit = st.selectbox(
            "Vyberte řádek k úpravě:",
            options=df.index,
            format_func=lambda i: f"{df.loc[i, 'Provede']} - {df.loc[i, 'Název akce']}",
            key="edit_select"
        )
        original = data[str(current_year)][idx_to_edit]
        with st.form("edit_form"):
            provede_edit = st.text_input("Provede", value=original.get("Provede", ""))
            nazev_edit = st.text_input("Název akce", value=original.get("Název akce", ""))
            zadal_edit = st.text_input("Zadal", value=original.get("Zadal", ""))
            cena_h_edit = st.number_input(
                "Cena/h", min_value=0.0, step=1.0, format="%.2f", value=float(original.get("Cena/h", 0.0))
            )
            pocet_h_edit = st.number_input(
                "Pč/h", min_value=0.0, step=1.0, format="%.2f", value=float(original.get("Pč/h", 0.0))
            )
            poznamka_edit = st.text_input("Poznámka", value=original.get("Poznámka", ""))
            submit_edit = st.form_submit_button("💾 Uložit změny")
            if submit_edit:
                updated = {
                    "Provede": provede_edit,
                    "Název akce": nazev_edit,
                    "Zadal": zadal_edit,
                    "Cena/h": cena_h_edit,
                    "Pč/h": pocet_h_edit,
                    "Cena": round(cena_h_edit * pocet_h_edit, 2),
                    "Poznámka": poznamka_edit
                }
                data[str(current_year)][idx_to_edit] = updated
                save_data(data)
                st.success("Záznam byl úspěšně upraven!")
                safe_rerun()

    hr()
    st.subheader(f"Přehled financí pro rok {current_year}")
    total_budget = st.number_input("Zadejte celkový rozpočet (Kč):", min_value=0.0, step=1000.0, format="%.2f", key="dpp_total_budget")
    if st.button("💾 Uložit rozpočet", key="dpp_save_budget"):
        save_budget(total_budget)
        st.success("Rozpočet byl uložen!")
    if not df.empty and "Cena" in df.columns:
        celkove_cerpano = df["Cena"].sum()
    else:
        celkove_cerpano = 0.0
    zbyva = total_budget - celkove_cerpano
    col1, col2, col3 = st.columns(3)
    col1.metric("Celkový rozpočet", f"{total_budget:.2f} Kč")
    col2.metric("Vydáno", f"{celkove_cerpano:.2f} Kč")
    col3.metric("Zbývá", f"{zbyva:.2f} Kč")

    hr()
    st.subheader("Uložení do historie a nový rok")
    if st.button("💾 Uložit rok a začít nový", key="d
