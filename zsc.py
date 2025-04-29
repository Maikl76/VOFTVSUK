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

    # tlačítko pro rerun
    if st.button("Aktualizovat", key="zsc_update"):
        safe_rerun()

    hr()

    # Načtení / inicializace dat
    if "zsc_data" not in st.session_state:
        st.session_state.zsc_data = load_data()
    data = st.session_state.zsc_data

    if "zsc_budget" not in st.session_state:
        st.session_state.zsc_budget = load_budget()

    # --- Přidání nové cesty ---
    st.subheader("Přidat novou cestu")
    with st.form("zsc_add_form", clear_on_submit=True):
        dest      = st.text_input("Plánovaná cesta", placeholder="Destinace nebo popis")
        ticket    = st.number_input("Letenka (Kč)", min_value=0.0, step=100.0, format="%.2f")
        fee       = st.number_input("Účast poplatek (Kč)", min_value=0.0, step=100.0, format="%.2f")
        lodging   = st.number_input("Ubytování (Kč)", min_value=0.0, step=100.0, format="%.2f")
        per_diem  = st.number_input("Stravné (Kč)", min_value=0.0, step=50.0, format="%.2f")
        pocket    = st.number_input("Kapesné (Kč)", min_value=0.0, step=50.0, format="%.2f")
        misc      = st.number_input("Os. výdaje (Kč)", min_value=0.0, step=50.0, format="%.2f")
        persons   = st.number_input("Počet osob", min_value=1, step=1)
        date      = st.date_input("Termín")
        author    = st.text_input("Zadal")
        note      = st.text_area("Poznámka")
        submitted = st.form_submit_button("➕ Přidat cestu")
        if submitted:
            per_person = ticket + fee + lodging + per_diem + pocket + misc
            total      = round(per_person * persons, 2)
            year       = str(datetime.date.today().year)
            record = {
                "Plánovaná cesta": dest,
                "Letenka (Kč)": ticket,
                "Účast poplatek (Kč)": fee,
                "Ubytování (Kč)": lodging,
                "Stravné (Kč)": per_diem,
                "Kapesné (Kč)": pocket,
                "Os. výdaje (Kč)": misc,
                "Cena za osobu (Kč)": round(per_person, 2),
                "Počet osob": persons,
                "Celkem (Kč)": total,
                "Termín": date.strftime("%Y-%m-%d"),
                "Zadal": author,
                "Poznámka": note
            }
            data.setdefault(year, []).append(record)
            save_data(data)
            st.success("Cesta přidána!")
            safe_rerun()

    hr()

    # --- Přehled záznamů ---
    st.subheader("Přehled záznamů")
    year = str(datetime.date.today().year)
    df = pd.DataFrame(data.get(year, []))
    if df.empty:
        st.info("Žádné záznamy k zobrazení.")
    else:
        # pevné pořadí sloupců
        cols = [
            "Plánovaná cesta","Letenka (Kč)","Účast poplatek (Kč)",
            "Ubytování (Kč)","Stravné (Kč)","Kapesné (Kč)",
            "Os. výdaje (Kč)","Cena za osobu (Kč)","Počet osob",
            "Celkem (Kč)","Termín","Zadal","Poznámka"
        ]
        df = df[cols]
        st.dataframe(df, use_container_width=True, height=40*(len(df)+1))

        # mazání
        hr()
        st.markdown("##### Smazat záznam")
        idx_del = st.selectbox(
            "Vyberte řádek k odstranění",
            df.index,
            format_func=lambda i: f"{df.loc[i,'Plánovaná cesta']} – {df.loc[i,'Termín']}",
            key="zsc_del"
        )
        if st.button("❌ Smazat řádek", key="zsc_del_btn"):
            data[year].pop(idx_del)
            save_data(data)
            st.success("Záznam smazán!")
            safe_rerun()

        # manuální editace
        hr()
        st.markdown("##### Upravit záznam")
        idx_edit = st.selectbox(
            "Vyberte řádek k úpravě",
            df.index,
            format_func=lambda i: f"{df.loc[i,'Plánovaná cesta']} – {df.loc[i,'Termín']}",
            key="zsc_edit"
        )
        orig = data[year][idx_edit]
        with st.form(f"zsc_edit_form_{idx_edit}", clear_on_submit=True):
            plan_e     = st.text_input("Plánovaná cesta", value=orig.get("Plánovaná cesta",""))
            ticket_e   = st.number_input("Letenka (Kč)", min_value=0.0, value=float(orig.get("Letenka (Kč)",0)), step=100.0, format="%.2f")
            fee_e      = st.number_input("Účast poplatek (Kč)", min_value=0.0, value=float(orig.get("Účast poplatek (Kč)",0)), step=100.0, format="%.2f")
            lodging_e  = st.number_input("Ubytování (Kč)", min_value=0.0, value=float(orig.get("Ubytování (Kč)",0)), step=100.0, format="%.2f")
            per_diem_e = st.number_input("Stravné (Kč)", min_value=0.0, value=float(orig.get("Stravné (Kč)",0)), step=50.0, format="%.2f")
            pocket_e   = st.number_input("Kapesné (Kč)", min_value=0.0, value=float(orig.get("Kapesné (Kč)",0)), step=50.0, format="%.2f")
            misc_e     = st.number_input("Os. výdaje (Kč)", min_value=0.0, value=float(orig.get("Os. výdaje (Kč)",0)), step=50.0, format="%.2f")
            persons_e  = st.number_input("Počet osob", min_value=1, value=int(orig.get("Počet osob",1)), step=1)
            date_e     = st.date_input("Termín", value=datetime.datetime.strptime(orig.get("Termín","1970-01-01"),"%Y-%m-%d"))
            author_e   = st.text_input("Zadal", value=orig.get("Zadal",""))
            note_e     = st.text_area("Poznámka", value=orig.get("Poznámka",""))
            submitted  = st.form_submit_button("💾 Uložit změny")
            if submitted:
                per_person_e = ticket_e + fee_e + lodging_e + per_diem_e + pocket_e + misc_e
                total_e      = round(per_person_e * persons_e, 2)
                updated = {
                    "Plánovaná cesta": plan_e,
                    "Letenka (Kč)": ticket_e,
                    "Účast poplatek (Kč)": fee_e,
                    "Ubytování (Kč)": lodging_e,
                    "Stravné (Kč)": per_diem_e,
                    "Kapesné (Kč)": pocket_e,
                    "Os. výdaje (Kč)": misc_e,
                    "Cena za osobu (Kč)": round(per_person_e, 2),
                    "Počet osob": persons_e,
                    "Celkem (Kč)": total_e,
                    "Termín": date_e.strftime("%Y-%m-%d"),
                    "Zadal": author_e,
                    "Poznámka": note_e
                }
                data[year][idx_edit] = updated
                save_data(data)
                st.success("Záznam upraven!")
                safe_rerun()

    # --- Finance, historie a archiv zůstávají beze změn ---

if __name__ == "__main__":
    run_zsc()
