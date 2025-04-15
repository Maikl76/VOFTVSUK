import streamlit as st
import pandas as pd
import json
import os
import datetime
from io import BytesIO

# Soubory pro uložení dat
DATA_FILE = "dpp_planovani.json"
HIST_FILE = "dpp_historie.json"
BUDGET_FILE = "dpp_budget.json"
rok = datetime.datetime.now().year

def safe_rerun():
    try:
        st.experimental_rerun()
    except AttributeError:
        pass

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

def hr():
    st.markdown("<hr style='border-top: 3px solid #fff;'>", unsafe_allow_html=True)

def run_dpp():
    st.title("Plánování DPP")
    st.markdown("##### Plánování dohod o pracovní činnosti pro aktuální rok")
    
    # Tlačítko pro aktualizaci a text vedle něj
    cols = st.columns([1, 3])
    with cols[0]:
        if st.button("Aktualizovat"):
            safe_rerun()
    with cols[1]:
        st.markdown("**Klikni pro aktualizaci a tím zobrazení změn**")
    
    # Načtení dat do session_state (pro okamžitou aktualizaci)
    if "dpp_data" not in st.session_state:
        st.session_state.dpp_data = load_data()
    data = st.session_state.dpp_data

    # Načtení rozpočtu do session_state
    if "dpp_total_budget" not in st.session_state:
        st.session_state.dpp_total_budget = load_budget()

    hr()
    # Formulář pro přidání nové akce
    st.subheader("Přidat novou akci")
    with st.form("dpp_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            provede = st.text_input("Provede", placeholder="Jméno a příjmení osoby")
            nazev_akce = st.text_input("Název Akce", placeholder="Popis činnosti")
            zadal = st.text_input("Zadal", placeholder="Jméno zadavatele")
        with col2:
            cena_h = st.number_input("Cena/h", min_value=0.0, step=1.0, format="%.2f")
            pocet_h = st.number_input("Pč/h", min_value=0.0, step=1.0, format="%.2f")
            poznamka = st.text_input("Poznámka", placeholder="Doplňující informace")
        submitted = st.form_submit_button("➕ Přidat řádek")
        if submitted:
            nova_akce = {
                "Provede": provede,
                "Název Akce": nazev_akce,
                "Cena/h": cena_h,
                "Pč/h": pocet_h,
                "Cena": round(cena_h * pocet_h, 2),
                "Zadal": zadal,
                "Poznámka": poznamka
            }
            data[str(rok)].append(nova_akce)
            save_data(data)
            st.success("DPP byla přidána!")
    
    hr()
    st.subheader("Přehled záznamů DPP")
    df = pd.DataFrame(data[str(rok)])
    if df.empty:
        st.info("Zatím nebyly přidány žádné akce.")
    else:
        # Dynamická výška tabulky (40px na řádek + 40px záhlaví)
        table_height = 40 * (len(df) + 1)
        st.dataframe(df, use_container_width=True, height=table_height)
        
        hr()
        # Sekce mazání řádku s potvrzením pomocí radio tlačítek
        st.markdown("##### Mazání řádku")
        row_to_delete = st.selectbox(
            "Vyberte řádek k odstranění", 
            options=df.index, 
            format_func=lambda x: f"{df.loc[x, 'Provede']} - {df.loc[x, 'Název Akce']}"
        )
        confirm = st.radio("Opravdu si přejete smazat tento řádek?", ("Ne", "Ano"))
        if confirm == "Ano":
            if st.button("❌ Smazat vybraný řádek"):
                data[str(rok)].pop(row_to_delete)
                save_data(data)
                st.success("Řádek byl smazán!")
                safe_rerun()
        
        hr()
        # Úprava záznamů
        if hasattr(st, "experimental_data_editor"):
            st.markdown("##### Upravit záznamy pomocí inline editoru")
            edited_df = st.experimental_data_editor(
                df,
                num_rows="dynamic",
                use_container_width=True,
                key="dpp_editor"
            )
            if st.button("💾 Uložit provedené změny (inline editor)"):
                if "Cena/h" in edited_df.columns and "Pč/h" in edited_df.columns:
                    edited_df["Cena"] = (edited_df["Cena/h"] * edited_df["Pč/h"]).round(2)
                data[str(rok)] = edited_df.to_dict(orient="records")
                save_data(data)
                st.success("Změny byly uloženy!")
        else:
            st.markdown("##### Upravit záznam (alternativní rozhraní)")
            row_idx = st.selectbox(
                "Vyberte řádek pro editaci", 
                options=df.index, 
                format_func=lambda x: f"{df.loc[x, 'Provede']} - {df.loc[x, 'Název Akce']}"
            )
            edited_provede = st.text_input("Provede", value=df.loc[row_idx, "Provede"])
            edited_nazev = st.text_input("Název Akce", value=df.loc[row_idx, "Název Akce"])
            edited_cena_h = st.number_input("Cena/h", value=float(df.loc[row_idx, "Cena/h"]), format="%.2f")
            edited_pocet_h = st.number_input("Pč/h", value=float(df.loc[row_idx, "Pč/h"]), format="%.2f")
            edited_zadal = st.text_input("Zadal", value=df.loc[row_idx, "Zadal"])
            edited_poznamka = st.text_input("Poznámka", value=df.loc[row_idx, "Poznámka"])
            if st.button("💾 Uložit změny pro vybraný řádek"):
                df.loc[row_idx, "Provede"] = edited_provede
                df.loc[row_idx, "Název Akce"] = edited_nazev
                df.loc[row_idx, "Cena/h"] = edited_cena_h
                df.loc[row_idx, "Pč/h"] = edited_pocet_h
                df.loc[row_idx, "Cena"] = round(edited_cena_h * edited_pocet_h, 2)
                df.loc[row_idx, "Zadal"] = edited_zadal
                df.loc[row_idx, "Poznámka"] = edited_poznamka
                data[str(rok)] = df.to_dict(orient="records")
                save_data(data)
                st.success("Změny byly uloženy!")
        
        hr()
        if st.button("📥 Vygenerovat Excel se záznamy"):
            towrite = BytesIO()
            excel_df = pd.DataFrame(data[str(rok)])
            excel_df.to_excel(towrite, index=False, sheet_name=f"DPP_{rok}")
            towrite.seek(0)
            st.download_button(
                label="Stáhnout Excel soubor",
                data=towrite,
                file_name=f"DPP_{rok}.xlsx",
                mime="application/vnd.ms-excel"
            )

    hr()
    st.subheader(f"Přehled financí pro rok {rok}")
    total_budget = st.number_input("Zadejte celkovou částku na rok:", min_value=0.0, step=1000.0, format="%.2f", key="dpp_total_budget")
    if st.button("💾 Uložit rozpočet"):
        save_budget(total_budget)
        st.success("Rozpočet byl uložen!")
    celkove_cerpano = df["Cena"].sum() if not df.empty else 0.0
    zbyva = total_budget - celkove_cerpano
    col1, col2, col3 = st.columns(3)
    col1.metric("Celková částka", f"{total_budget:.2f} Kč")
    col2.metric("Čerpáno", f"{celkove_cerpano:.2f} Kč")
    col3.metric("Zbývá", f"{zbyva:.2f} Kč")

    hr()
    st.subheader("Uložení dat do historie a zahájení nového roku")
    if st.button("💾 Uložit rok a začít nový"):
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

    hr()
    st.subheader("Historie DPP")
    if os.path.exists(HIST_FILE):
        with open(HIST_FILE, "r", encoding="utf-8") as f:
            historie = json.load(f)
        roky_hist = sorted(historie.keys(), reverse=True)
        if roky_hist:
            vybrany_rok = st.selectbox("Vyberte rok pro zobrazení:", roky_hist)
            historie_df = pd.DataFrame(historie[vybrany_rok])
            if not historie_df.empty:
                historie_df["Cena"] = historie_df["Cena"].map("{:.2f} Kč".format)
                st.dataframe(historie_df, use_container_width=True)
                total_historie = historie_df["Cena"].str.replace(" Kč", "").astype(float).sum()
                st.markdown(f"**Celková částka za rok {vybrany_rok}: {total_historie:.2f} Kč**")
            else:
                st.info("Tento rok neobsahuje žádné záznamy.")
        else:
            st.info("Historie zatím neobsahuje žádné záznamy.")
    else:
        st.info("Historie zatím neexistuje.")

if __name__ == "__main__":
    run_dpp()
