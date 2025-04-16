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

def load_data():
    response = supabase.table("zsc_cesty").select("data").eq("id", 1).execute()
    if response.data and "data" in response.data[0]:
        return response.data[0]["data"]
    else:
        return {}

def save_data(data):
    response = supabase.table("zsc_cesty").update({"data": data}).eq("id", 1).execute()
    return response

def load_budget():
    response = supabase.table("zsc_budget").select("value").eq("id", 1).execute()
    if response.data:
        return response.data[0]["value"]
    else:
        return 0.0

def save_budget(budget):
    response = supabase.table("zsc_budget").update({"value": budget}).eq("id", 1).execute()
    return response

def load_history():
    response = supabase.table("zsc_historie").select("data").eq("id", 1).execute()
    if response.data and "data" in response.data[0]:
        return response.data[0]["data"]
    else:
        return {}

def save_history(history):
    response = supabase.table("zsc_historie").update({"data": history}).eq("id", 1).execute()
    return response

def run_zsc():
    st.title("Zahraniční cesty")
    st.markdown("Evidence zahraničních cest pro aktuální rok")
    if st.button("Aktualizovat", key="zsc_update"):
        try:
            st.experimental_rerun()
        except AttributeError:
            pass

    st.markdown("<hr style='border-top: 5px solid white;'>", unsafe_allow_html=True)

    if "zsc_data" not in st.session_state:
        st.session_state.zsc_data = load_data()
    data = st.session_state.zsc_data

    if "zsc_total_budget" not in st.session_state:
        st.session_state.zsc_total_budget = load_budget()

    st.subheader("Přidat novou cestu")
    with st.form("zsc_form", clear_on_submit=True):
        planovana_cesta = st.text_input("Plánovaná cesta", placeholder="Název destinace nebo popis")
        letenka = st.number_input("Letenka (Kč)", min_value=0.0, step=100.0, format="%.2f")
        ucast_poplatek = st.number_input("Účast poplatek (Kč)", min_value=0.0, step=100.0, format="%.2f")
        ubytovani = st.number_input("Ubytování (Kč)", min_value=0.0, step=100.0, format="%.2f")
        stravne = st.number_input("Stravné (Kč)", min_value=0.0, step=50.0, format="%.2f")
        kapesne = st.number_input("Kapesné (Kč)", min_value=0.0, step=50.0, format="%.2f")
        os_vydaje = st.number_input("Os. výdaje (Kč)", min_value=0.0, step=50.0, format="%.2f")
        pocet_osob = st.number_input("Počet osob", min_value=1, step=1)
        termin = st.date_input("Termín")
        zadal = st.text_input("Zadal")
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
                "Termín": termin.strftime("%Y-%m-%d"),
                "Zadal": zadal,
                "Poznámka": poznamka
            }
            rok = datetime.datetime.now().year
            if str(rok) not in data:
                data[str(rok)] = []
            data[str(rok)].append(nova_cesta)
            save_data(data)
            st.success("Cesta byla přidána!")
            st.experimental_rerun()

    st.markdown("<hr style='border-top: 5px solid white;'>", unsafe_allow_html=True)
    st.subheader("Přehled záznamů cest")
    rok = datetime.datetime.now().year
    df = pd.DataFrame(data.get(str(rok), []))
    if df.empty:
        st.info("Žádné záznamy.")
    else:
        st.dataframe(df, use_container_width=True)
        row_to_delete = st.selectbox("Vyberte řádek k odstranění", options=df.index, key="zsc_select_delete", 
                                     format_func=lambda idx: f"{df.loc[idx, 'Plánovaná cesta']} - {df.loc[idx, 'Termín']}")
        if st.button("❌ Smazat řádek", key="zsc_delete_row"):
            data[str(rok)].pop(row_to_delete)
            save_data(data)
            st.success("Řádek smazán!")
            st.experimental_rerun()
        if hasattr(st, "experimental_data_editor"):
            edited_df = st.experimental_data_editor(df, num_rows="dynamic", key="zsc_editor", use_container_width=True)
            if st.button("💾 Uložit změny", key="zsc_save_inline"):
                data[str(rok)] = edited_df.to_dict(orient="records")
                save_data(data)
                st.success("Změny byly uloženy!")
                st.experimental_rerun()
        else:
            st.info("Inline editor není podporován.")
    
    st.markdown("<hr style='border-top: 5px solid white;'>", unsafe_allow_html=True)
    st.subheader(f"Přehled financí pro rok {rok}")
    total_budget = st.number_input("Zadejte celkový rozpočet (Kč):", min_value=0.0, step=1000.0, format="%.2f", key="zsc_total_budget")
    if st.button("💾 Uložit rozpočet", key="zsc_save_budget"):
        save_budget(total_budget)
        st.success("Rozpočet uložen!")
    total_expenses = df["Celkem (Kč)"].sum() if not df.empty and "Celkem (Kč)" in df.columns else 0.0
    zbyva = total_budget - total_expenses
    col1, col2, col3 = st.columns(3)
    col1.metric("Celkový rozpočet", f"{total_budget:.2f} Kč")
    col2.metric("Vydáno", f"{total_expenses:.2f} Kč")
    col3.metric("Zbývá", f"{zbyva:.2f} Kč")
    
    st.markdown("<hr style='border-top: 5px solid white;'>", unsafe_allow_html=True)
    st.subheader("Historie ZSC")
    history = load_history()
    if history:
        roky_hist = sorted(history.keys(), reverse=True)
        if roky_hist:
            vybrany_rok = st.selectbox("Vyberte rok pro zobrazení:", roky_hist)
            hist_df = pd.DataFrame(history[vybrany_rok])
            if not hist_df.empty:
                hist_df["Celkem (Kč)"] = hist_df["Celkem (Kč)"].map("{:.2f} Kč".format)
                st.dataframe(hist_df, use_container_width=True)
                total_hist = hist_df["Celkem (Kč)"].str.replace(" Kč", "").astype(float).sum()
                st.markdown(f"**Celková částka za {vybrany_rok}: {total_hist:.2f} Kč**")
            else:
                st.info("Tento rok neobsahuje záznamy.")
        else:
            st.info("Historie zatím neobsahuje záznamy.")
    else:
        st.info("Historie zatím není nastavena.")
    
    st.markdown("<hr style='border-top: 5px solid white;'>", unsafe_allow_html=True)
    st.subheader("Uložení do historie a nový rok")
    if st.button("💾 Uložit a začít nový rok", key="zsc_new_year"):
        history = load_history()
        history[str(rok)] = data.get(str(rok), [])
        save_history(history)
        data[str(rok+1)] = []
        save_data(data)
        st.success(f"Data za {rok} uložena. Začínáme rok {rok+1}.")
        st.experimental_rerun()

if __name__ == "__main__":
    run_zsc()
