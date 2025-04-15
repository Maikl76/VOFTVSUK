import streamlit as st
import pandas as pd
import json
import os
import datetime
from io import BytesIO

# Soubor pro uložení dat poukazů na rehabilitaci
DATA_FILE = "pri_rehabilitace.json"

def load_data(current_year, next_year):
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}
    # Zajistíme, že pro oba roky existují prázdné seznamy, pokud ještě neexistují
    if str(current_year) not in data:
        data[str(current_year)] = []
    if str(next_year) not in data:
        data[str(next_year)] = []
    return data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def run_pri(selected_year):
    current_year = int(selected_year)
    next_year = current_year + 1

    st.title("Evidence PR-I – Přidělené poukazy na rehabilitaci")
    st.markdown(f"Evidence rehabilitačních poukazů pro rok {current_year} a {next_year}.")

    # Načtení dat do session_state; pokud už data existují, zkontrolujeme, že obsahují klíče pro aktuální a následující rok
    if "pri_data" not in st.session_state:
        st.session_state.pri_data = load_data(current_year, next_year)
    else:
        data = st.session_state.pri_data
        if str(current_year) not in data:
            data[str(current_year)] = []
        if str(next_year) not in data:
            data[str(next_year)] = []
        st.session_state.pri_data = data

    data = st.session_state.pri_data

    # Formulář pro přidání nové položky
    st.subheader("Přidat nový poukaz")
    with st.form("pri_form", clear_on_submit=True):
        cislo = st.text_input("Číslo poukazu")
        datum_od = st.date_input("Datum od")
        datum_do = st.date_input("Datum do")
        rehabilitacni_zarizeni = st.text_input("Rehabilitační zařízení")
        typ_rehabilitace = st.text_input("Typ rehabilitace")
        prijmeni = st.text_input("Příjmení")
        poznamka = st.text_area("Poznámka")
        # Uživatel si vybere, ke kterému roku se záznam vztahuje
        rok_vyber = st.selectbox("Rok", options=[str(current_year), str(next_year)], index=0,
                                  help="Vyberte, ke kterému roku se poukaz vztahuje")
        submitted = st.form_submit_button("➕ Přidat řádek")
        if submitted:
            novy_poukaz = {
                "Číslo poukazu": cislo,
                "Datum od": datum_od.strftime("%Y-%m-%d"),
                "Datum do": datum_do.strftime("%Y-%m-%d"),
                "Rehabilitační zařízení": rehabilitacni_zarizeni,
                "Typ rehabilitace": typ_rehabilitace,
                "Příjmení": prijmeni,
                "Poznámka": poznamka
            }
            data[rok_vyber].append(novy_poukaz)
            save_data(data)
            st.success("Poukaz byl přidán!")
            st.experimental_rerun()

    # Zobrazení tabulek pro oba roky
    for rok in [str(current_year), str(next_year)]:
        st.subheader(f"Poukazy na rok {rok}")
        df = pd.DataFrame(data[rok])
        if df.empty:
            st.info("Žádné záznamy.")
        else:
            st.dataframe(df, use_container_width=True)
            
            st.markdown("##### Mazání záznamů")
            row_to_delete = st.selectbox(
                "Vyberte řádek k odstranění",
                options=df.index,
                key="delete_" + rok,
                format_func=lambda idx: f"{df.loc[idx, 'Číslo poukazu']} - {df.loc[idx, 'Příjmení']}"
            )
            if st.button("❌ Smazat vybraný řádek", key="delete_button_" + rok):
                data[rok].pop(row_to_delete)
                save_data(data)
                st.success("Záznam byl smazán!")
                st.experimental_rerun()

            st.markdown("##### Úprava záznamů")
            if hasattr(st, "experimental_data_editor"):
                edited_df = st.experimental_data_editor(
                    df, num_rows="dynamic", key="editor_" + rok, use_container_width=True
                )
                if st.button("💾 Uložit změny", key="save_edit_" + rok):
                    data[rok] = edited_df.to_dict(orient="records")
                    save_data(data)
                    st.success("Změny byly uloženy!")
                    st.experimental_rerun()
            else:
                row_idx = st.selectbox(
                    "Vyberte řádek pro editaci",
                    options=df.index,
                    key="edit_" + rok,
                    format_func=lambda idx: f"{df.loc[idx, 'Číslo poukazu']} - {df.loc[idx, 'Příjmení']}"
                )
                cislo_edit = st.text_input("Číslo poukazu", value=df.loc[row_idx, "Číslo poukazu"], key="cislo_" + rok)
                datum_od_edit = st.date_input("Datum od", value=pd.to_datetime(df.loc[row_idx, "Datum od"]), key="datum_od_" + rok)
                datum_do_edit = st.date_input("Datum do", value=pd.to_datetime(df.loc[row_idx, "Datum do"]), key="datum_do_" + rok)
                rehabilitacni_zarizeni_edit = st.text_input("Rehabilitační zařízení", value=df.loc[row_idx, "Rehabilitační zařízení"], key="rehab_zarizeni_" + rok)
                typ_rehabilitace_edit = st.text_input("Typ rehabilitace", value=df.loc[row_idx, "Typ rehabilitace"], key="typ_rehab_" + rok)
                prijmeni_edit = st.text_input("Příjmení", value=df.loc[row_idx, "Příjmení"], key="prijmeni_" + rok)
                poznamka_edit = st.text_area("Poznámka", value=df.loc[row_idx, "Poznámka"], key="poznamka_" + rok)
                if st.button("💾 Uložit úpravy", key="save_edit_alt_" + rok):
                    df.loc[row_idx, "Číslo poukazu"] = cislo_edit
                    df.loc[row_idx, "Datum od"] = datum_od_edit.strftime("%Y-%m-%d")
                    df.loc[row_idx, "Datum do"] = datum_do_edit.strftime("%Y-%m-%d")
                    df.loc[row_idx, "Rehabilitační zařízení"] = rehabilitacni_zarizeni_edit
                    df.loc[row_idx, "Typ rehabilitace"] = typ_rehabilitace_edit
                    df.loc[row_idx, "Příjmení"] = prijmeni_edit
                    df.loc[row_idx, "Poznámka"] = poznamka_edit
                    data[rok] = df.to_dict(orient="records")
                    save_data(data)
                    st.success("Změny byly uloženy!")
                    st.experimental_rerun()

if __name__ == "__main__":
    run_pri(datetime.datetime.now().year)
