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

    # Načtení dat a rozpočtu
    if "dpp_data" not in st.session_state:
        st.session_state.dpp_data = load_data()
    data = st.session_state.dpp_data
    if "dpp_total_budget" not in st.session_state:
        st.session_state.dpp_total_budget = load_budget()

    # Přidat novou akci
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
        submitted = st.form_submit_button("➕ Přidat akci")
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
            data.setdefault(str(current_year), []).append(nova_akce)
            save_data(data)
            st.success("Akce byla přidána!")
            safe_rerun()

    # Přehled záznamů
    hr()
    st.subheader("Přehled záznamů DPP")
    current_year = datetime.datetime.now().year
    df = pd.DataFrame(data.get(str(current_year), []))
    if df.empty or "Cena" not in df.columns:
        st.info("Zatím nebyly přidány žádné akce.")
    else:
        # Pořadí sloupců
        df = df[["Provede", "Název akce", "Cena/h", "Pč/h", "Cena", "Zadal", "Poznámka"]]
        table_height = 40 * (len(df) + 1)
        st.dataframe(df, use_container_width=True, height=table_height)

        # Export do Excelu
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="DPP")
        buf.seek(0)
        st.download_button(
            "📥 Exportovat do Excelu",
            data=buf.getvalue(),
            file_name=f"dpp_zaznamy_{current_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Mazání řádku
        hr()
        st.markdown("##### Mazání řádku")
        row_to_delete = st.selectbox(
            "Vyberte řádek k odstranění",
            options=df.index,
            key="dpp_select_delete",
            format_func=lambda idx: f"{df.loc[idx, 'Provede']} - {df.loc[idx, 'Název akce']}"
        )
        if st.button("❌ Smazat vybraný řádek", key="dpp_delete_row"):
            data[str(current_year)].pop(row_to_delete)
            save_data(data)
            st.success("Řádek byl smazán!")
            safe_rerun()

        # Upravit záznam
        hr()
        st.markdown("##### Upravit záznam")
        row_to_edit = st.selectbox(
            "Vyberte řádek k úpravě",
            options=df.index,
            key="dpp_select_edit",
            format_func=lambda idx: f"{df.loc[idx, 'Provede']} - {df.loc[idx, 'Název akce']}"
        )
        orig = data[str(current_year)][row_to_edit]
        # Dynamický formulář s clear_on_submit
        with st.form(f"dpp_edit_form_{row_to_edit}", clear_on_submit=True):
            provede_e = st.text_input("Provede", value=orig.get("Provede", ""))
            nazev_e = st.text_input("Název akce", value=orig.get("Název akce", ""))
            zadal_e = st.text_input("Zadal", value=orig.get("Zadal", ""))
            cena_h_e = st.number_input(
                "Cena/h",
                min_value=0.0,
                step=1.0,
                format="%.2f",
                value=orig.get("Cena/h", 0.0)
            )
            pocet_h_e = st.number_input(
                "Pč/h",
                min_value=0.0,
                step=1.0,
                format="%.2f",
                value=orig.get("Pč/h", 0.0)
            )
            poznamka_e = st.text_input("Poznámka", value=orig.get("Poznámka", ""))
            submitted_e = st.form_submit_button("💾 Uložit změny")
            if submitted_e:
                updated = {
                    "Provede": provede_e,
                    "Název akce": nazev_e,
                    "Cena/h": cena_h_e,
                    "Pč/h": pocet_h_e,
                    "Cena": round(cena_h_e * pocet_h_e, 2),
                    "Zadal": zadal_e,
                    "Poznámka": poznamka_e
                }
                data[str(current_year)][row_to_edit] = updated
                save_data(data)
                st.success("Záznam byl upraven!")
                safe_rerun()

    # Přehled financí
    hr()
    st.subheader(f"Přehled financí pro rok {current_year}")
    total_budget = st.number_input(
        "Zadejte celkový rozpočet (Kč):",
        min_value=0.0,
        step=1000.0,
        format="%.2f",
        key="dpp_total_budget"
    )
    if st.button("💾 Uložit rozpočet", key="dpp_save_budget"):
        save_budget(total_budget)
        st.success("Rozpočet byl uložen!")
    celkove_cerpano = df["Cena"].sum() if not df.empty else 0.0
    zbyva = total_budget - celkove_cerpano
    col1, col2, col3 = st.columns(3)
    col1.metric("Celkový rozpočet", f"{total_budget:.2f} Kč")
    col2.metric("Vydáno", f"{celkove_cerpano:.2f} Kč")
    col3.metric("Zbývá", f"{zbyva:.2f} Kč")

    # Archiv a historie
    hr()
    st.subheader("Uložení do historie a nový rok")
    if st.button("💾 Uložit rok a začít nový", key="dpp_save_year"):
        history = load_history()
        history[str(current_year)] = data.get(str(current_year), [])
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
            vybrany_rok = st.selectbox("Vyberte rok pro zobrazení:", roky_hist)
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
