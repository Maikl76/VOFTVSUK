import streamlit as st
import pandas as pd
import json
import os
import datetime
from io import BytesIO

# Definice cest k souborům a aktuální rok
DATA_FILE = "zsc_cesty.json"
HIST_FILE = "zsc_historie.json"
BUDGET_FILE = "zsc_budget.json"
rok = datetime.datetime.now().year

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}
    if str(rok) not in data:
        data[str(rok)] = []
    return data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_budget():
    if os.path.exists(BUDGET_FILE):
        with open(BUDGET_FILE, "r", encoding="utf-8") as f:
            budget = json.load(f)
    else:
        budget = 0.0
    return budget

def save_budget(budget):
    with open(BUDGET_FILE, "w", encoding="utf-8") as f:
        json.dump(budget, f, ensure_ascii=False, indent=4)

def run_zsc():
    st.title("Evidence Zahraničních cest (ZSC)")
    st.markdown("Evidence zahraničních cest pro aktuální rok")
    
    # Tlačítko pro aktualizaci v rámci záložky ZSC
    if st.button("Aktualizace", key="zsc_update"):
        try:
            st.experimental_rerun()
        except AttributeError:
            pass

    # Definice vlastního oddělovače: tlustá bílá čára
    st.markdown("<hr style='border-top: 5px solid white;'>", unsafe_allow_html=True)

    if "zsc_data" not in st.session_state:
        st.session_state.zsc_data = load_data()
    data = st.session_state.zsc_data

    if "zsc_total_budget" not in st.session_state:
        st.session_state.zsc_total_budget = load_budget()

    # Sekce pro přidání nové cesty
    st.subheader("Přidat novou cestu")
    with st.form("zsc_form", clear_on_submit=True):
        planovana_cesta = st.text_input("Plánovaná cesta", placeholder="Název destinace nebo popis cesty")
        letenka = st.number_input("Letenka (Kč)", min_value=0.0, step=100.0, format="%.2f")
        ucast_poplatek = st.number_input("Účast poplatek (Kč)", min_value=0.0, step=100.0, format="%.2f")
        ubytovani = st.number_input("Ubytování (Kč)", min_value=0.0, step=100.0, format="%.2f")
        stravne = st.number_input("Stravné (Kč)", min_value=0.0, step=50.0, format="%.2f")
        kapesne = st.number_input("Kapesné (Kč)", min_value=0.0, step=50.0, format="%.2f")
        os_vydaje = st.number_input("Os. výdaje (Kč)", min_value=0.0, step=50.0, format="%.2f")
        pocet_osob = st.number_input("Počet osob", min_value=1, step=1)
        termín = st.date_input("Termín")
        zadal = st.text_input("Zadal", placeholder="Kdo zadal cestu")
        poznamka = st.text_area("Poznámka")
        submitted = st.form_submit_button("➕ Přidat cestu")
        if submitted:
            cena_za_osobu = letenka + ucast_poplatek + ubytovani + stravne + kapesne + os_vydaje
            celkem = cena_za_osobu * pocet_osob
            nova_cesta = {
                "Plánovaná cesta": planovana_cesta,
                "Letenka (Kč)": letenka,
                "Účast poplatek (Kč)": ucast_poplatek,
                "Ubytování (Kč)": ubytovani,
                "Stravné (Kč)": stravne,
                "Kapesné (Kč)": kapesne,
                "Os. výdaje (Kč)": os_vydaje,
                "Cena za osobu (Kč)": round(cena_za_osobu, 2),
                "Počet osob": pocet_osob,
                "Celkem (Kč)": round(celkem, 2),
                "Termín": termín.strftime("%Y-%m-%d"),
                "Zadal": zadal,
                "Poznámka": poznamka
            }
            data[str(rok)].append(nova_cesta)
            save_data(data)
            st.success("Cesta byla přidána!")
            try:
                st.experimental_rerun()
            except AttributeError:
                pass

    st.markdown("<hr style='border-top: 5px solid white;'>", unsafe_allow_html=True)

    # Sekce pro přehled záznamů cest
    st.subheader("Přehled záznamů cest")
    df = pd.DataFrame(data[str(rok)])
    if df.empty:
        st.info("Zatím nebyly přidány žádné cesty.")
    else:
        st.dataframe(df, use_container_width=True)
        
        st.markdown("<hr style='border-top: 5px solid white;'>", unsafe_allow_html=True)
        st.markdown("##### Mazání záznamů")
        row_to_delete = st.selectbox("Vyberte řádek k odstranění", options=df.index, key="zsc_select_delete", format_func=lambda idx: f"{df.loc[idx, 'Plánovaná cesta']} - {df.loc[idx, 'Termín']}")
        if st.button("❌ Smazat vybraný řádek", key="zsc_delete_row"):
            data[str(rok)].pop(row_to_delete)
            save_data(data)
            st.success("Záznam byl smazán!")
            try:
                st.experimental_rerun()
            except AttributeError:
                pass

        st.markdown("<hr style='border-top: 5px solid white;'>", unsafe_allow_html=True)
        st.markdown("##### Upravit záznamy")
        if hasattr(st, "experimental_data_editor"):
            edited_df = st.experimental_data_editor(
                df, num_rows="dynamic", key="zsc_editor", use_container_width=True
            )
            if st.button("💾 Uložit změny (inline editor)", key="zsc_save_inline"):
                data[str(rok)] = edited_df.to_dict(orient="records")
                save_data(data)
                st.success("Změny byly uloženy!")
                try:
                    st.experimental_rerun()
                except AttributeError:
                    pass
        else:
            row_idx = st.selectbox("Vyberte řádek pro editaci", options=df.index, key="zsc_select_edit", format_func=lambda idx: f"{df.loc[idx, 'Plánovaná cesta']} - {df.loc[idx, 'Termín']}")
            planovana_cesta_edit = st.text_input("Plánovaná cesta", value=df.loc[row_idx, "Plánovaná cesta"], key="zsc_edit_plan")
            letenka_edit = st.number_input("Letenka (Kč)", value=float(df.loc[row_idx, "Letenka (Kč)"]), format="%.2f", key="zsc_edit_letenka")
            ucast_poplatek_edit = st.number_input("Účast poplatek (Kč)", value=float(df.loc[row_idx, "Účast poplatek (Kč)"]), format="%.2f", key="zsc_edit_uctpop")
            ubytovani_edit = st.number_input("Ubytování (Kč)", value=float(df.loc[row_idx, "Ubytování (Kč)"]), format="%.2f", key="zsc_edit_ubytovani")
            stravne_edit = st.number_input("Stravné (Kč)", value=float(df.loc[row_idx, "Stravné (Kč)"]), format="%.2f", key="zsc_edit_stravne")
            kapesne_edit = st.number_input("Kapesné (Kč)", value=float(df.loc[row_idx, "Kapesné (Kč)"]), format="%.2f", key="zsc_edit_kapesne")
            os_vydaje_edit = st.number_input("Os. výdaje (Kč)", value=float(df.loc[row_idx, "Os. výdaje (Kč)"]), format="%.2f", key="zsc_edit_osvydaje")
            pocet_osob_edit = st.number_input("Počet osob", value=int(df.loc[row_idx, "Počet osob"]), min_value=1, step=1, key="zsc_edit_osoby")
            termín_edit = st.date_input("Termín", value=pd.to_datetime(df.loc[row_idx, "Termín"]), key="zsc_edit_termin")
            zadal_edit = st.text_input("Zadal", value=df.loc[row_idx, "Zadal"], key="zsc_edit_zadal")
            poznamka_edit = st.text_area("Poznámka", value=df.loc[row_idx, "Poznámka"], key="zsc_edit_poznamka")
            if st.button("💾 Uložit změny", key="zsc_save_edit"):
                cena_za_osobu_edit = letenka_edit + ucast_poplatek_edit + ubytovani_edit + stravne_edit + kapesne_edit + os_vydaje_edit
                celkem_edit = cena_za_osobu_edit * pocet_osob_edit
                df.loc[row_idx, "Plánovaná cesta"] = planovana_cesta_edit
                df.loc[row_idx, "Letenka (Kč)"] = letenka_edit
                df.loc[row_idx, "Účast poplatek (Kč)"] = ucast_poplatek_edit
                df.loc[row_idx, "Ubytování (Kč)"] = ubytovani_edit
                df.loc[row_idx, "Stravné (Kč)"] = stravne_edit
                df.loc[row_idx, "Kapesné (Kč)"] = kapesne_edit
                df.loc[row_idx, "Os. výdaje (Kč)"] = os_vydaje_edit
                df.loc[row_idx, "Cena za osobu (Kč)"] = round(cena_za_osobu_edit, 2)
                df.loc[row_idx, "Počet osob"] = pocet_osob_edit
                df.loc[row_idx, "Celkem (Kč)"] = round(celkem_edit, 2)
                df.loc[row_idx, "Termín"] = termín_edit.strftime("%Y-%m-%d")
                df.loc[row_idx, "Zadal"] = zadal_edit
                df.loc[row_idx, "Poznámka"] = poznamka_edit
                data[str(rok)] = df.to_dict(orient="records")
                save_data(data)
                st.success("Změny byly uloženy!")
                try:
                    st.experimental_rerun()
                except AttributeError:
                    pass

    st.markdown("<hr style='border-top: 5px solid white;'>", unsafe_allow_html=True)
    st.subheader(f"Přehled financí pro rok {rok}")
    total_budget = st.number_input("Zadejte celkový rozpočet na zahraniční cesty:", min_value=0.0, step=1000.0, format="%.2f", key="zsc_total_budget_input")
    if st.button("💾 Uložit rozpočet", key="zsc_save_budget"):
        save_budget(total_budget)
        st.success("Rozpočet byl uložen!")
    total_expenses = df["Celkem (Kč)"].sum() if not df.empty else 0.0
    zbyva = total_budget - total_expenses
    col1, col2, col3 = st.columns(3)
    col1.metric("Celkový rozpočet", f"{total_budget:.2f} Kč")
    col2.metric("Vydáno", f"{total_expenses:.2f} Kč")
    col3.metric("Zbývá", f"{zbyva:.2f} Kč")
    
    st.markdown("<hr style='border-top: 5px solid white;'>", unsafe_allow_html=True)
    st.subheader("Uložení dat do historie a zahájení nového roku")
    if st.button("💾 Uložit rok a začít nový", key="zsc_save_year"):
        if os.path.exists(HIST_FILE):
            with open(HIST_FILE, "r", encoding="utf-8") as f:
                historie = json.load(f)
        else:
            historie = {}
        historie[str(rok)] = data[str(rok)]
        with open(HIST_FILE, "w", encoding="utf-8") as f:
            json.dump(historie, f, ensure_ascii=False, indent=4)
        data[str(rok+1)] = []
        save_data(data)
        st.success(f"Data za rok {rok} byla uložena. Začínáme rok {rok+1}.")

if __name__ == "__main__":
    run_zsc()
