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
    return resp.data[0].get("data", {}) if resp.data else {}


def save_data(data):
    return supabase.table("zsc_cesty").update({"data": data}).eq("id", 1).execute()


def load_budget():
    resp = supabase.table("zsc_budget").select("value").eq("id", 1).execute()
    return resp.data[0].get("value", 0.0) if resp.data else 0.0


def save_budget(value):
    return supabase.table("zsc_budget").update({"value": value}).eq("id", 1).execute()


def load_history():
    resp = supabase.table("zsc_historie").select("data").eq("id", 1).execute()
    return resp.data[0].get("data", {}) if resp.data else {}


def save_history(hist):
    return supabase.table("zsc_historie").update({"data": hist}).eq("id", 1).execute()


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

    if "zsc_budget" not in st.session_state:
        st.session_state.zsc_budget = load_budget()

    # Přidání nové cesty
    st.subheader("Přidat novou cestu")
    with st.form("zsc_form", clear_on_submit=True):
        planovana = st.text_input("Plánovaná cesta", placeholder="Název destinace nebo popis")
        letenka = st.number_input("Letenka (Kč)", min_value=0.0, step=100.0, format="%.2f")
        poplatek = st.number_input("Účast poplatek (Kč)", min_value=0.0, step=100.0, format="%.2f")
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
            per_person = letenka + poplatek + ubytovani + stravne + kapesne + os_vydaje
            celkem = round(per_person * pocet_osob, 2)
            rok = str(datetime.datetime.now().year)
            record = {
                "Plánovaná cesta": planovana,
                "Letenka (Kč)": letenka,
                "Účast poplatek (Kč)": poplatek,
                "Ubytování (Kč)": ubytovani,
                "Stravné (Kč)": stravne,
                "Kapesné (Kč)": kapesne,
                "Os. výdaje (Kč)": os_vydaje,
                "Cena za osobu (Kč)": round(per_person, 2),
                "Počet osob": pocet_osob,
                "Celkem (Kč)": celkem,
                "Termín": termin.strftime("%Y-%m-%d"),
                "Zadal": zadal,
                "Poznámka": poznamka
            }
            data.setdefault(rok, []).append(record)
            save_data(data)
            st.success("Cesta byla přidána!")
            safe_rerun()

    # Přehled záznamů
    hr()
    st.subheader("Přehled záznamů cest")
    rok = str(datetime.datetime.now().year)
    df = pd.DataFrame(data.get(rok, []))
    if df.empty:
        st.info("Žádné záznamy.")
    else:
        cols = [
            "Plánovaná cesta","Letenka (Kč)","Účast poplatek (Kč)",
            "Ubytování (Kč)","Stravné (Kč)","Kapesné (Kč)",
            "Os. výdaje (Kč)","Cena za osobu (Kč)","Počet osob",
            "Celkem (Kč)","Termín","Zadal","Poznámka"
        ]
        df = df[cols]
        st.dataframe(df, use_container_width=True, height=40*(len(df)+1))

        # Mazání řádku
        hr()
        st.markdown("##### Smazat záznam")
        idx_del = st.selectbox(
            "Vyberte řádek k odstranění",
            df.index,
            format_func=lambda i: f"{df.loc[i,'Plánovaná cesta']} - {df.loc[i,'Termín']}",
            key="zsc_del"
        )
        if st.button("❌ Smazat řádek", key="zsc_del_btn"):
            data[rok].pop(idx_del)
            save_data(data)
            st.success("Záznam smazán!")
            safe_rerun()

        # Editace záznamu
        hr()
        st.markdown("##### Upravit záznam")
        idx_edit = st.selectbox(
            "Vyberte řádek k úpravě",
            df.index,
            format_func=lambda i: f"{df.loc[i,'Plánovaná cesta']} - {df.loc[i,'Termín']}",
            key="zsc_edit"
        )
        orig = data[rok][idx_edit]
        with st.form(f"zsc_edit_form_{idx_edit}", clear_on_submit=True):
            plan_e     = st.text_input("Plánovaná cesta", value=orig.get("Plánovaná cesta",""))
            let_e      = st.number_input("Letenka (Kč)", min_value=0.0, value=float(orig.get("Letenka (Kč)",0)), step=100.0, format="%.2f")
            pop_e      = st.number_input("Účast poplatek (Kč)", min_value=0.0, value=float(orig.get("Účast poplatek (Kč)",0)), step=100.0, format="%.2f")
            ubyt_e     = st.number_input("Ubytování (Kč)", min_value=0.0, value=float(orig.get("Ubytování (Kč)",0)), step=100.0, format="%.2f")
            strs_e     = st.number_input("Stravné (Kč)", min_value=0.0, value=float(orig.get("Stravné (Kč)",0)), step=50.0, format="%.2f")
            kap_e      = st.number_input("Kapesné (Kč)", min_value=0.0, value=float(orig.get("Kapesné (Kč)",0)), step=50.0, format="%.2f")
            os_e       = st.number_input("Os. výdaje (Kč)", min_value=0.0, value=float(orig.get("Os. výdaje (Kč)",0)), step=50.0, format="%.2f")
            poc_e      = st.number_input("Počet osob", min_value=1, value=int(orig.get("Počet osob",1)), step=1)
            term_e     = st.date_input("Termín", value=datetime.datetime.strptime(orig.get("Termín","1970-01-01"),"%Y-%m-%d"))
            zad_e      = st.text_input("Zadal", value=orig.get("Zadal",""))
            poz_e      = st.text_area("Poznámka", value=orig.get("Poznámka",""))
            submitted  = st.form_submit_button("💾 Uložit změny")
            if submitted:
                per_p = let_e + pop_e + ubyt_e + strs_e + kap_e + os_e
                tot_e = round(per_p * poc_e, 2)
                updated = {
                    "Plánovaná cesta": plan_e,
                    "Letenka (Kč)": let_e,
                    "Účast poplatek (Kč)": pop_e,
                    "Ubytování (Kč)": ubyt_e,
                    "Stravné (Kč)": strs_e,
                    "Kapesné (Kč)": kap_e,
                    "Os. výdaje (Kč)": os_e,
                    "Cena za osobu (Kč)": round(per_p,2),
                    "Počet osob": poc_e,
                    "Celkem (Kč)": tot_e,
                    "Termín": term_e.strftime("%Y-%m-%d"),
                    "Zadal": zad_e,
                    "Poznámka": poz_e
                }
                data[rok][idx_edit] = updated
                save_data(data)
                st.success("Záznam upraven!")
                safe_rerun()

        # Přehled financí
        hr()
        st.subheader(f"Přehled financí pro rok {rok}")
        total_budget = st.number_input(
            "Zadejte celkový rozpočet (Kč):",
            min_value=0.0, step=1000.0, format="%.2f",
            value=st.session_state.zsc_total_budget,
            key="zsc_budget"
        )
        if st.button("💾 Uložit rozpočet", key="zsc_budget_btn"):
            save_budget(total_budget)
            st.success("Rozpočet uložen!")
        spent = df["Celkem (Kč)"].sum()
        remaining = total_budget - spent
        c1, c2, c3 = st.columns(3)
        c1.metric("Celkový rozpočet", f"{total_budget:.2f} Kč")
        c2.metric("Vydáno", f"{spent:.2f} Kč")
        c3.metric("Zbývá", f"{remaining:.2f} Kč")

        # Historie a archiv
        hr()
        st.subheader("Historie ZSC")
        history = load_history()
        if history:
            yrs = sorted(history.keys(), reverse=True)
            sel = st.selectbox("Vyberte rok", yrs, key="zsc_hist")
            hist_df = pd.DataFrame(history.get(sel, []))
            if not hist_df.empty:
                hist_df["Celkem (Kč)"] = hist_df["Celkem (Kč)"].map("{:.2f} Kč".format)
                st.dataframe(hist_df, use_container_width=True)
                total_hist = hist_df["Celkem (Kč)"].str.replace(" Kč", "").astype(float).sum()
                st.markdown(f"**Celkem za {sel}: {total_hist:.2f} Kč**")
            else:
                st.info("Tento rok neobsahuje záznamy.")
        else:
            st.info("Historie zatím není nastavena.")

        hr()
        st.subheader("Uložení do historie a nový rok")
        if st.button("💾 Uložit a další rok", key="zsc_archive_btn"):
            history = load_history()
            history[rok] = data.get(rok, [])
            save_history(history)
            next_year = str(int(rok) + 1)
            data[next_year] = []
            save_data(data)
            st.success(f"Data za {rok} uložena. Nový rok: {next_year}.")
            safe_rerun()

if __name__ == "__main__":
    run_zsc()
