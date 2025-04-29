import streamlit as st
import pandas as pd
import datetime
from io import BytesIO
from supabase import create_client, Client

# ===== KONFIGURACE SUPABASE =====
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


def load_data():
    response = supabase.table("zsc_cesty").select("data").eq("id", 1).execute()
    if response.data and "data" in response.data[0]:
        return response.data[0]["data"]
    return {}


def save_data(data):
    return supabase.table("zsc_cesty").update({"data": data}).eq("id", 1).execute()


def load_budget():
    response = supabase.table("zsc_budget").select("value").eq("id", 1).execute()
    if response.data:
        return response.data[0]["value"]
    return 0.0


def save_budget(budget):
    return supabase.table("zsc_budget").update({"value": budget}).eq("id", 1).execute()


def load_history():
    response = supabase.table("zsc_historie").select("data").eq("id", 1).execute()
    if response.data and "data" in response.data[0]:
        return response.data[0]["data"]
    return {}


def save_history(history):
    return supabase.table("zsc_historie").update({"data": history}).eq("id", 1).execute()


def hr():
    st.markdown("<hr style='border-top:5px solid white;'>", unsafe_allow_html=True)


def run_zsc():
    st.title("Zahraniční cesty")
    st.markdown("Evidence zahraničních cest pro aktuální rok")
    if st.button("Aktualizovat", key="zsc_update"):
        safe_rerun()

    hr()

    # Načtení dat
    if "zsc_data" not in st.session_state:
        st.session_state.zsc_data = load_data()
    data = st.session_state.zsc_data

    if "zsc_total_budget" not in st.session_state:
        st.session_state.zsc_total_budget = load_budget()

    # Přidání nové cesty
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
            cena_os = letenka + ucast_poplatek + ubytovani + stravne + kapesne + os_vydaje
            celkem = cena_os * pocet_osob
            rok = str(datetime.datetime.now().year)
            nova_cesta = {
                "Plánovaná cesta": planovana_cesta,
                "Letenka (Kč)": letenka,
                "Účast poplatek (Kč)": ucast_poplatek,
                "Ubytování (Kč)": ubytovani,
                "Stravné (Kč)": stravne,
                "Kapesné (Kč)": kapesne,
                "Os. výdaje (Kč)": os_vydaje,
                "Cena za osobu (Kč)": round(cena_os, 2),
                "Počet osob": pocet_osob,
                "Celkem (Kč)": round(celkem, 2),
                "Termín": termin.strftime("%Y-%m-%d"),
                "Zadal": zadal,
                "Poznámka": poznamka
            }
            data.setdefault(rok, []).append(nova_cesta)
            save_data(data)
            st.success("Cesta byla přidána!")
            safe_rerun()

    hr()
    st.subheader("Přehled záznamů cest")
    rok = str(datetime.datetime.now().year)
    df = pd.DataFrame(data.get(rok, []))
    if df.empty:
        st.info("Žádné záznamy.")
        return
    st.dataframe(df, use_container_width=True)

    # Mazání záznamu
    hr()
    st.markdown("##### Smazat záznam")
    idx_del = st.selectbox(
        "Vyberte řádek k odstranění", options=df.index,
        format_func=lambda i: f"{df.loc[i,'Plánovaná cesta']} - {df.loc[i,'Termín']}",
        key="zsc_del"
    )
    if st.button("❌ Smazat řádek", key="zsc_delete_row"):
        data[rok].pop(idx_del)
        save_data(data)
        st.success("Záznam smazán!")
        safe_rerun()

    # Upravit záznam
    hr()
    st.markdown("##### Upravit záznam")
    idx_edit = st.selectbox(
        "Vyberte řádek k úpravě", options=df.index,
        format_func=lambda i: f"{df.loc[i,'Plánovaná cesta']} - {df.loc[i,'Termín']}",
        key="zsc_edit"
    )
    orig = data[rok][idx_edit]
    with st.form(f"zsc_edit_form_{idx_edit}", clear_on_submit=True):
        planovana_e = st.text_input("Plánovaná cesta", value=orig.get("Plánovaná cesta", ""))
        letenka_e = st.number_input("Letenka (Kč)", min_value=0.0, value=orig.get("Letenka (Kč)", 0.0), step=100.0, format="%.2f")
        poplat_e = st.number_input("Účast poplatek (Kč)", min_value=0.0, value=orig.get("Účast poplatek (Kč)", 0.0), step=100.0, format="%.2f")
        ubyt_e = st.number_input("Ubytování (Kč)", min_value=0.0, value=orig.get("Ubytování (Kč)", 0.0), step=100.0, format="%.2f")
        strav_e = st.number_input("Stravné (Kč)", min_value=0.0, value=orig.get("Stravné (Kč)", 0.0), step=50.0, format="%.2f")
        kap_e = st.number_input("Kapesné (Kč)", min_value=0.0, value=orig.get("Kapesné (Kč)", 0.0), step=50.0, format="%.2f")
        os_e = st.number_input("Os. výdaje (Kč)", min_value=0.0, value=orig.get("Os. výdaje (Kč)", 0.0), step=50.0, format="%.2f")
        poc_os_e = st.number_input("Počet osob", min_value=1, value=orig.get("Počet osob", 1), step=1)
        term_e = st.date_input("Termín", value=datetime.datetime.strptime(orig.get("Termín", "1970-01-01"), "%Y-%m-%d"))
        zadal_e = st.text_input("Zadal", value=orig.get("Zadal", ""))
        poz_e = st.text_area("Poznámka", value=orig.get("Poznámka", ""))
        submitted_edit = st.form_submit_button("💾 Uložit změny")
        if submitted_edit:
            cena_os_e = letenka_e + poplat_e + ubyt_e + strav_e + kap_e + os_e
            celkem_e = cena_os_e * poc_os_e
            updated = {
                "Plánovaná cesta": planovana_e,
                "Letenka (Kč)": letenka_e,
                "Účast poplatek (Kč)": poplat_e,
                "Ubytování (Kč)": ubyt_e,
                "Stravné (Kč)": strav_e,
                "Kapesné (Kč)": kap_e,
                "Os. výdaje (Kč)": os_e,
                "Cena za osobu (Kč)": round(cena_os_e, 2),
                "Počet osob": poc_os_e,
                "Celkem (Kč)": round(celkem_e, 2),
                "Termín": term_e.strftime("%Y-%m-%d"),
                "Zadal": zadal_e,
                "Poznámka": poz_e
            }
            data[rok][idx_edit] = updated
            save_data(data)
            st.success("Záznam upraven!")
            safe_rerun()

    # Přehled financí a historie... (beze změn)

if __name__ == "__main__":
    run_zsc()
