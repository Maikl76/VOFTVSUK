import streamlit as st
import pandas as pd
import datetime
from io import BytesIO
from supabase import create_client, Client
import json

SUPABASE_URL = "https://bgtpylewilzcqfqaoixx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJndHB5bGV3aWx6Y3FmcWFvaXh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ1NzQxNTQsImV4cCI6MjA2MDE1MDE1NH0.6NutsH1g8k0ruhpylqltrWD53HQFy-ZQjcUN-SULktM"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
    response = supabase.table("dpp_planovani").update({"data": data}).eq("id", 1).execute()
    return response

def load_budget():
    response = supabase.table("dpp_budget").select("value").eq("id", 1).execute()
    if response.data:
        return response.data[0]["value"]
    else:
        return 0.0

def save_budget(budget):
    response = supabase.table("dpp_budget").update({"value": budget}).eq("id", 1).execute()
    return response

def load_history():
    response = supabase.table("dpp_historie").select("data").eq("id", 1).execute()
    if response.data and "data" in response.data[0]:
        return response.data[0]["data"]
    else:
        return {}

def save_history(history):
    response = supabase.table("dpp_historie").update({"data": history}).eq("id", 1).execute()
    return response

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
    
    # Načtení dat z Supabase
    if "dpp_data" not in st.session_state:
        st.session_state.dpp_data = load_data()
    data = st.session_state.dpp_data
    
    if "dpp_total_budget" not in st.session_state:
        st.session_state.dpp_total_budget = load_budget()
    
    hr()
    st.subheader("Přidat novou akci")
    with st.form("dpp_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            provede = st.text_input("Provede", placeholder="Jméno a příjmení")
            nazev_akce = st.text_input("Název akce", placeholder="Popis činnosti")
            zadal = st.text_input("Zadal", placeholder="Jméno zadavatele")
        with col2:
            cena_h = st.number_input("Cena/h", min_value=0.0, step=1.0, format="%.2f")
            pocet_h = st.number_input("Pč/h", min_value=0.0, step=1.0, format="%.2f")
            poznamka = st.text_input("Poznámka")
        submitted = st.form_submit_button("➕ Přidat řádek")
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
            current_year = datetime.datetime.now().year
            if str(current_year) not in data:
                data[str(current_year)] = []
            data[str(current_year)].append(nova_akce)
            save_data(data)
            st.success("Akce byla přidána!")
            safe_rerun()
    
    hr()
    st.subheader("Přehled záznamů DPP")
    current_year = datetime.datetime.now().year
    if str(current_year) not in data:
        st.info("Zatím nebyly přidány žádné akce.")
    else:
        df = pd.DataFrame(data[str(current_year)])
        if df.empty:
            st.info("Zatím nebyly přidány žádné akce.")
        else:
            table_height = 40 * (len(df) + 1)
            st.dataframe(df, use_container_width=True, height=table_height)
            hr()
            st.markdown("##### Mazání řádku")
            row_to_delete = st.selectbox("Vyberte řádek k odstranění", options=df.index,
                                         key="dpp_select_delete", format_func=lambda idx: f"{df.loc[idx, 'Provede']} - {df.loc[idx, 'Název akce']}")
            if st.button("❌ Smazat vybraný řádek", key="dpp_delete_row"):
                data[str(current_year)].pop(row_to_delete)
                save_data(data)
                st.success("Řádek byl smazán!")
                safe_rerun()
            
            hr()
            st.markdown("##### Upravit záznamy")
            if hasattr(st, "experimental_data_editor"):
                edited_df = st.experimental_data_editor(df, num_rows="dynamic", key="dpp_editor", use_container_width=True)
                if st.button("💾 Uložit změny (inline)", key="dpp_save_inline"):
                    if "Cena/h" in edited_df.columns and "Pč/h" in edited_df.columns:
                        edited_df["Cena"] = (edited_df["Cena/h"] * edited_df["Pč/h"]).round(2)
                    data[str(current_year)] = edited_df.to_dict(orient="records")
                    save_data(data)
                    st.success("Změny byly uloženy!")
                    safe_rerun()
            else:
                st.markdown("##### Upravit záznam (alternativně)")
                row_idx = st.selectbox("Vyberte řádek pro editaci", options=df.index,
                                        key="dpp_select_edit", format_func=lambda idx: f"{df.loc[idx, 'Provede']} - {df.loc[idx, 'Název akce']}")
                edited_provede = st.text_input("Provede", value=df.loc[row_idx, "Provede"], key="dpp_edit_provede")
                edited_nazev = st.text_input("Název akce", value=df.loc[row_idx, "Název akce"], key="dpp_edit_nazev")
                edited_cena_h = st.number_input("Cena/h", value=float(df.loc[row_idx, "Cena/h"]), format="%.2f", key="dpp_edit_cena_h")
                edited_pocet_h = st.number_input("Pč/h", value=float(df.loc[row_idx, "Pč/h"]), format="%.2f", key="dpp_edit_pocet_h")
                edited_zadal = st.text_input("Zadal", value=df.loc[row_idx, "Zadal"], key="dpp_edit_zadal")
                edited_poznamka = st.text_input("Poznámka", value=df.loc[row_idx, "Poznámka"], key="dpp_edit_poznamka")
                if st.button("💾 Uložit změny (alternativně)", key="dpp_save_edit"):
                    df.loc[row_idx, "Provede"] = edited_provede
                    df.loc[row_idx, "Název akce"] = edited_nazev
                    df.loc[row_idx, "Cena/h"] = edited_cena_h
                    df.loc[row_idx, "Pč/h"] = edited_pocet_h
                    df.loc[row_idx, "Cena"] = round(edited_cena_h * edited_pocet_h, 2)
                    df.loc[row_idx, "Zadal"] = edited_zadal
                    df.loc[row_idx, "Poznámka"] = edited_poznamka
                    data[str(current_year)] = df.to_dict(orient="records")
                    save_data(data)
                    st.success("Změny byly uloženy!")
                    safe_rerun()
    
    hr()
    st.subheader(f"Přehled financí pro rok {current_year}")
    total_budget = st.number_input("Zadejte celkový rozpočet (Kč):", min_value=0.0, step=1000.0, format="%.2f", key="dpp_total_budget")
    if st.button("💾 Uložit rozpočet", key="dpp_save_budget"):
        save_budget(total_budget)
        st.success("Rozpočet byl uložen!")
    celkove_cerpano = df["Cena"].sum() if not df.empty else 0.0
    zbyva = total_budget - celkove_cerpano
    col1, col2, col3 = st.columns(3)
    col1.metric("Celkový rozpočet", f"{total_budget:.2f} Kč")
    col2.metric("Vydáno", f"{celkove_cerpano:.2f} Kč")
    col3.metric("Zbývá", f"{zbyva:.2f} Kč")
    
    hr()
    st.subheader("Uložení dat do historie a zahájení nového roku")
    if st.button("💾 Uložit rok a začít nový", key="dpp_save_year"):
        history = load_history()
        history[str(current_year)] = data[str(current_year)]
        save_history(history)
        data[str(current_year+1)] = []
        save_data(data)
        st.success(f"Data za rok {current_year} byla uložena. Začínáme rok {current_year+1}.")
        safe_rerun()

    hr()
    st.subheader("Historie DPP")
    history = load_history()
    if history:
        roky_hist = sorted(history.keys(), reverse=True)
        if roky_hist:
            vybrany_rok = st.selectbox("Vyberte rok:", roky_hist)
            hist_df = pd.DataFrame(history[vybrany_rok])
            if not hist_df.empty:
                hist_df["Cena"] = hist_df["Cena"].map("{:.2f} Kč".format)
                st.dataframe(hist_df, use_container_width=True)
                total_hist = hist_df["Cena"].str.replace(" Kč", "").astype(float).sum()
                st.markdown(f"**Celková částka za rok {vybrany_rok}: {total_hist:.2f} Kč**")
            else:
                st.info("Tento rok neobsahuje žádné záznamy.")
        else:
            st.info("Historie zatím neobsahuje žádné záznamy.")
    else:
        st.info("Historie zatím neexistuje.")

if __name__ == "__main__":
    run_dpp()
