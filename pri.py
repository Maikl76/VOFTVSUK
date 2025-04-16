import streamlit as st
import pandas as pd
import json
import datetime
from io import BytesIO
from supabase import create_client, Client

# ===== KONFIGURACE SUPABASE =====
from supabase import create_client, Client
# Načtení hodnot ze st.secrets
SUPABASE_URL = st.secrets["supabase"]["supabase_url"]
SUPABASE_KEY = st.secrets["supabase"]["supabase_key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# =================================

def load_data(current_year, next_year):
    response = supabase.table("pri_rehabilitace").select("data").eq("id", 1).execute()
    if response.data and "data" in response.data[0]:
        data = response.data[0]["data"]
    else:
        data = {}
    if str(current_year) not in data:
        data[str(current_year)] = []
    if str(next_year) not in data:
        data[str(next_year)] = []
    return data

def save_data(data):
    response = supabase.table("pri_rehabilitace").update({"data": data}).eq("id", 1).execute()
    return response

def run_pri(selected_year):
    current_year = int(selected_year)
    next_year = current_year + 1

    st.title("Poukazy rehabiitace")
    st.markdown(f"Evidence rehabilitačních poukazů pro roky {current_year} a {next_year}.")

    if "pri_data" not in st.session_state:
        st.session_state.pri_data = load_data(current_year, next_year)
    data = st.session_state.pri_data

    st.subheader("Přidat nový poukaz")
    with st.form("pri_form", clear_on_submit=True):
        cislo = st.text_input("Číslo poukazu")
        datum_od = st.date_input("Datum od")
        datum_do = st.date_input("Datum do")
        rehabilitacni_zarizeni = st.text_input("Rehabilitační zařízení")
        typ_rehabilitace = st.text_input("Typ rehabilitace")
        prijmeni = st.text_input("Příjmení")
        poznamka = st.text_area("Poznámka")
        rok_vyber = st.selectbox("Rok", options=[str(current_year), str(next_year)], index=0)
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

    for rok in [str(current_year), str(next_year)]:
        st.subheader(f"Poukazy na rok {rok}")
        df = pd.DataFrame(data[rok])
        if df.empty:
            st.info("Žádné záznamy.")
        else:
            st.dataframe(df, use_container_width=True)
            row_to_delete = st.selectbox("Vyberte řádek k odstranění", options=df.index, key="pri_delete_" + rok,
                                         format_func=lambda idx: f"{df.loc[idx, 'Číslo poukazu']} - {df.loc[idx, 'Příjmení']}")
            if st.button("❌ Smazat řádek", key="pri_delete_btn_" + rok):
                data[rok].pop(row_to_delete)
                save_data(data)
                st.success("Řádek byl smazán!")
                st.experimental_rerun()
            if hasattr(st, "experimental_data_editor"):
                edited_df = st.experimental_data_editor(df, num_rows="dynamic", key="pri_editor_" + rok, use_container_width=True)
                if st.button("💾 Uložit změny", key="pri_save_" + rok):
                    data[rok] = edited_df.to_dict(orient="records")
                    save_data(data)
                    st.success("Změny byly uloženy!")
                    st.experimental_rerun()
            else:
                st.info("Inline editor není podporován.")
                
if __name__ == "__main__":
    run_pri(datetime.datetime.now().year)
