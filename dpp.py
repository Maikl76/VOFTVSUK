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
    response = supabase.table("dpp_planovani").select("data").eq("id", 1).execute()
    if response.data and "data" in response.data[0]:
        return response.data[0]["data"]
    return {}


def save_data(data):
    return supabase.table("dpp_planovani").update({"data": data}).eq("id", 1).execute()


def load_budget():
    response = supabase.table("dpp_budget").select("value").eq("id", 1).execute()
    if response.data:
        return response.data[0]["value"]
    return 0.0


def save_budget(budget):
    return supabase.table("dpp_budget").update({"value": budget}).eq("id", 1).execute()


def load_history():
    response = supabase.table("dpp_historie").select("data").eq("id", 1).execute()
    if response.data and "data" in response.data[0]:
        return response.data[0]["data"]
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

    # Načtení dat
    if "dpp_data" not in st.session_state:
        st.session_state.dpp_data = load_data()
    data = st.session_state.dpp_data
    if "dpp_total_budget" not in st.session_state:
        st.session_state.dpp_total_budget = load_budget()

    current_year = datetime.datetime.now().year

    # Přidání nové akce
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
        if st.form_submit_button("➕ Přidat akci"):
            nova = {"Provede": provede, "Název akce": nazev_akce,
                   "Cena/h": cena_h, "Pč/h": pocet_h,
                   "Cena": round(cena_h * pocet_h, 2),
                   "Zadal": zadal, "Poznámka": poznamka}
            data.setdefault(str(current_year), []).append(nova)
            save_data(data)
            st.success("Akce byla přidána!")
            safe_rerun()

    # Přehled a úpravy
    hr()
    st.subheader("Přehled záznamů DPP")
    df = pd.DataFrame(data.get(str(current_year), []))
    if df.empty or "Cena" not in df.columns:
        st.info("Zatím nebyly přidány žádné akce.")
    else:
        st.dataframe(df, use_container_width=True, height=40*(len(df)+1))

        # Mazání
        hr()
        st.markdown("##### Mazání řádku")
        idx_del = st.selectbox("Vyberte řádek k odstranění", options=df.index,
                                format_func=lambda i: f"{df.loc[i,'Provede']} - {df.loc[i,'Název akce']}", key="del")
        if st.button("❌ Smazat vybraný řádek", key="del_btn"):
            data[str(current_year)].pop(idx_del)
            save_data(data)
            st.success("Řádek smazán!")
            safe_rerun()

        # Editace
        hr()
        st.markdown("##### Upravit existující záznam")
        idx_edit = st.selectbox("Vyberte řádek k úpravě", options=df.index,
                                 format_func=lambda i: f"{df.loc[i,'Provede']} - {df.loc[i,'Název akce']}", key="edit")
        orig = data[str(current_year)][idx_edit]
        with st.form("edit_form"):
            prov = st.text_input("Provede", value=orig.get("Provede", ""))
            naz = st.text_input("Název akce", value=orig.get("Název akce", ""))
            zad = st.text_input("Zadal", value=orig.get("Zadal", ""))
            ch = st.number_input("Cena/h", min_value=0.0, value=float(orig.get("Cena/h", 0.0)), step=1.0, format="%.2f")
            ph = st.number_input("Pč/h", min_value=0.0, value=float(orig.get("Pč/h", 0.0)), step=1.0, format="%.2f")
            poz = st.text_input("Poznámka", value=orig.get("Poznámka", ""))
            if st.form_submit_button("💾 Uložit změny"):
                upd = {"Provede": prov, "Název akce": naz, "Cena/h": ch,
                       "Pč/h": ph, "Cena": round(ch * ph, 2),
                       "Zadal": zad, "Poznámka": poz}
                data[str(current_year)][idx_edit] = upd
                save_data(data)
                st.success("Záznam upraven!")
                safe_rerun()

    # Financování
    hr()
    st.subheader(f"Přehled financí pro rok {current_year}")
    total = st.number_input("Zadejte celkový rozpočet (Kč):", value=st.session_state.dpp_total_budget,
                             min_value=0.0, step=1000.0, format="%.2f", key="budget")
    if st.button("💾 Uložit rozpočet", key="save_bud"):
        save_budget(total)
        st.success("Rozpočet uložen!")
    spent = df["Cena"].sum() if not df.empty else 0.0
    remaining = total - spent
    c1, c2, c3 = st.columns(3)
    c1.metric("Celkový rozpočet", f"{total:.2f} Kč")
    c2.metric("Vydáno", f"{spent:.2f} Kč")
    c3.metric("Zbývá", f"{remaining:.2f} Kč")

    # Archiv
    hr()
    st.subheader("Uložení do historie a nový rok")
    if st.button("💾 Uložit rok a začít nový", key="save_year"):
        hist = load_history()
        hist[str(current_year)] = data.get(str(current_year), [])
        save_history(hist)
        data[str(current_year+1)] = []
        save_data(data)
        st.success(f"Data za rok {current_year} uložena. Začátek roku {current_year+1}.")
        safe_rerun()

    # Zobrazení historie
    hr()
    st.subheader("Historie DPP")
    history = load_history()
    if history:
        years = sorted(history.keys(), reverse=True)
        yr = st.selectbox("Vyberte rok pro zobrazení", years)
        dfh = pd.DataFrame(history.get(yr, []))
        if not dfh.empty:
            dfh["Cena"] = dfh["Cena"].map("{:.2f} Kč".format)
            st.dataframe(dfh, use_container_width=True)
            totalh = dfh["Cena"].str.replace(" Kč", "").astype(float).sum()
            st.markdown(f"**Celkem za rok {yr}: {totalh:.2f} Kč**")
        else:
            st.info("Tento rok nemá záznamy.")
    else:
        st.info("Žádná historie.")

if __name__ == "__main__":
    run_dpp()
