import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client

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
    resp = supabase.table("zsc_cesty").select("data").eq("id", 1).execute()
    return resp.data[0]["data"] if resp.data and "data" in resp.data[0] else {}

def save_data(data):
    return supabase.table("zsc_cesty").update({"data": data}).eq("id", 1).execute()

def load_budget():
    resp = supabase.table("zsc_budget").select("value").eq("id", 1).execute()
    return resp.data[0]["value"] if resp.data else 0.0

def save_budget(budget):
    return supabase.table("zsc_budget").update({"value": budget}).eq("id", 1).execute()

def load_history():
    resp = supabase.table("zsc_historie").select("data").eq("id", 1).execute()
    return resp.data[0]["data"] if resp.data and "data" in resp.data[0] else {}

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
        planovana = st.text_input("Plánovaná cesta", placeholder="Destinace nebo popis")
        letenka = st.number_input("Letenka (Kč)", min_value=0.0, step=100.0, format="%.2f")
        poplatek = st.number_input("Účast poplatek (Kč)", min_value=0.0, step=100.0, format="%.2f")
        ubytovani = st.number_input("Ubytování (Kč)", min_value=0.0, step=100.0, format="%.2f")
        stravne = st.number_input("Stravné (Kč)", min_value=0.0, step=50.0, format="%.2f")
        kapesne = st.number_input("Kapesné (Kč)", min_value=0.0, step=50.0, format="%.2f")
        os_vydaje = st.number_input("Os. výdaje (Kč)", min_value=0.0, step=50.0, format="%.2f")
        pocet_os = st.number_input("Počet osob", min_value=1, step=1)
        termin = st.date_input("Termín")
        zadal = st.text_input("Zadal")
        poznamka = st.text_area("Poznámka")
        if st.form_submit_button("➕ Přidat cestu"):
            cena_os = letenka + poplatek + ubytovani + stravne + kapesne + os_vydaje
            celkem = cena_os * pocet_os
            rok = datetime.datetime.now().year
            nova = {
                "Plánovaná cesta": planovana,
                "Letenka (Kč)": letenka,
                "Účast poplatek (Kč)": poplatek,
                "Ubytování (Kč)": ubytovani,
                "Stravné (Kč)": stravne,
                "Kapesné (Kč)": kapesne,
                "Os. výdaje (Kč)": os_vydaje,
                "Cena za osobu (Kč)": round(cena_os, 2),
                "Počet osob": pocet_os,
                "Celkem (Kč)": round(celkem, 2),
                "Termín": termin.strftime("%Y-%m-%d"),
                "Zadal": zadal,
                "Poznámka": poznamka
            }
            data.setdefault(str(rok), []).append(nova)
            save_data(data)
            st.success("Cesta přidána!")
            safe_rerun()

    hr()

    # Přehled a editace záznamů
    st.subheader("Přehled záznamů cest")
    rok = datetime.datetime.now().year
    df = pd.DataFrame(data.get(str(rok), []))
    if df.empty:
        st.info("Žádné záznamy.")
        return

    # Mazání řádku
    row_del = st.selectbox(
        "Vyberte řádek k odstranění",
        options=df.index,
        format_func=lambda i: f"{df.loc[i, 'Plánovaná cesta']} - {df.loc[i, 'Termín']}",
        key="zsc_delete"
    )
    if st.button("❌ Smazat řádek", key="zsc_delete_btn"):
        data[str(rok)].pop(row_del)
        save_data(data)
        st.success("Záznam smazán!")
        safe_rerun()

    hr()
    st.markdown("##### Upravit záznam")
    row_edit = st.selectbox(
        "Vyberte řádek k úpravě",
        options=df.index,
        format_func=lambda i: f"{df.loc[i, 'Plánovaná cesta']} - {df.loc[i, 'Termín']}",
        key="zsc_edit_select"
    )
    orig = data[str(rok)][row_edit]
    with st.form(f"zsc_edit_form_{row_edit}", clear_on_submit=True):
        plan_e = st.text_input("Plánovaná cesta", value=orig.get("Plánovaná cesta", ""))
        let_e = st.number_input("Letenka (Kč)", min_value=0.0, value=orig.get("Letenka (Kč)", 0.0), step=100.0, format="%.2f")
        pop_e = st.number_input("Účast poplatek (Kč)", min_value=0.0, value=orig.get("Účast poplatek (Kč)", 0.0), step=100.0, format="%.2f")
        ubyt_e = st.number_input("Ubytování (Kč)", min_value=0.0, value=orig.get("Ubytování (Kč)", 0.0), step=100.0, format="%.2f")
        str_e = st.number_input("Stravné (Kč)", min_value=0.0, value=orig.get("Stravné (Kč)", 0.0), step=50.0, format="%.2f")
        kap_e = st.number_input("Kapesné (Kč)", min_value=0.0, value=orig.get("Kapesné (Kč)", 0.0), step=50.0, format="%.2f")
        osv_e = st.number_input("Os. výdaje (Kč)", min_value=0.0, value=orig.get("Os. výdaje (Kč)", 0.0), step=50.0, format="%.2f")
        poc_e = st.number_input("Počet osob", min_value=1, value=orig.get("Počet osob", 1), step=1)
        term_e = st.date_input("Termín", value=datetime.datetime.strptime(orig.get("Termín", "1970-01-01"), "%Y-%m-%d"))
        zad_e = st.text_input("Zadal", value=orig.get("Zadal", ""))
        poz_e = st.text_area("Poznámka", value=orig.get("Poznámka", ""))
        if st.form_submit_button("💾 Uložit změny", key=f"zsc_edit_submit_{row_edit}"):
            cena_os_e = let_e + pop_e + ubyt_e + str_e + kap_e + osv_e
            celkem_e = cena_os_e * poc_e
            updated = {
                "Plánovaná cesta": plan_e,
                "Letenka (Kč)": let_e,
                "Účast poplatek (Kč)": pop_e,
                "Ubytování (Kč)": ubyt_e,
                "Stravné (Kč)": str_e,
                "Kapesné (Kč)": kap_e,
                "Os. výdaje (Kč)": osv_e,
                "Cena za osobu (Kč)": round(cena_os_e, 2),
                "Počet osob": poc_e,
                "Celkem (Kč)": round(celkem_e, 2),
                "Termín": term_e.strftime("%Y-%m-%d"),
                "Zadal": zad_e,
                "Poznámka": poz_e
            }
            data[str(rok)][row_edit] = updated
            save_data(data)
            st.success("Záznam upraven!")
            safe_rerun()

    hr()
    st.subheader(f"Přehled financí pro rok {rok}")
    total_bud = st.number_input(
        "Zadejte celkový rozpočet (Kč):",
        value=st.session_state.zsc_total_budget,
        min_value=0.0,
        step=1000.0,
        format="%.2f",
        key="zsc_budget"
    )
    if st.button("💾 Uložit rozpočet", key="zsc_budget_save"):
        save_budget(total_bud)
        st.success("Rozpočet uložen!")
    spent = df["Celkem (Kč)"].sum() if not df.empty else 0.0
    remaining = total_bud - spent
    c1, c2, c3 = st.columns(3)
    c1.metric("Celkový rozpočet", f"{total_bud:.2f} Kč")
    c2.metric("Vydáno", f"{spent:.2f} Kč")  
    c3.metric("Zbývá", f"{remaining:.2f} Kč")

    hr()
    st.subheader("Historie ZSC")
    history = load_history()
    if history:
        years = sorted(history.keys(), reverse=True)
        sel = st.selectbox("Vyberte rok pro zobrazení", years)
        hdf = pd.DataFrame(history.get(sel, []))
        if not hdf.empty:
            hdf["Celkem (Kč)"] = hdf["Celkem (Kč)"].map("{:.2f} Kč".format)
            st.dataframe(hdf, use_container_width=True)
            total_hist = hdf["Celkem (Kč)"].str.replace(" Kč", "").astype(float).sum()
            st.markdown(f"**Celková částka za {sel}: {total_hist:.2f} Kč**")
        else:
            st.info("Tento rok nemá záznamy.")
    else:
        st.info("Historie zatím není nastavena.")

    hr()
    st.subheader("Uložení do historie a nový rok")
    if st.button("💾 Uložit a začít nový rok", key="zsc_new_year"):
        history = load_history()
        history[str(rok)] = data.get(str(rok), [])
        save_history(history)
        data[str(rok+1)] = []
        save_data(data)
        st.success(f"Data za {rok} uložena. Začínáme rok {rok+1}.")
        safe_rerun()

if __name__ == "__main__":
    run_zsc()
