import streamlit as st
import pandas as pd
import datetime
from io import BytesIO
from supabase import create_client, Client
import json

# ===== KONFIGURACE SUPABASE =====
from supabase import create_client, Client
# Načtení hodnot ze st.secrets
SUPABASE_URL = st.secrets["supabase"]["supabase_url"]
SUPABASE_KEY = st.secrets["supabase"]["supabase_key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# =================================

def safe_rerun():
    try:
        st.experimental_rerun()
    except AttributeError:
        pass

# ... load_data, save_data, load_budget, save_budget, load_history, save_history, hr definitions ...

def run_dpp():
    st.title("Plánování DPP")
    st.markdown("##### Plánování dohod o pracovní činnosti pro aktuální rok")
    
    cols = st.columns([1, 3])
    with cols[0]:
        if st.button("Aktualizovat", key="dpp_update"):
            safe_rerun()
    with cols[1]:
        st.markdown("**Klikni pro aktualizaci a zobrazení změn**")
    
    # Načtení dat z Supabase
    if "dpp_data" not in st.session_state:
        st.session_state.dpp_data = load_data()
    data = st.session_state.dpp_data

    current_year = datetime.datetime.now().year

    hr()
    st.subheader("Přehled záznamů DPP")
    # Vytvoříme DataFrame pro aktuální rok
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
        st.markdown("##### Upravit existující záznam")
        # Manuální editor pro úpravu záznamu
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

    # ... zbytek funkce včetně přidávání, mazání a rozpočtu ...

if __name__ == "__main__":
    run_dpp()
