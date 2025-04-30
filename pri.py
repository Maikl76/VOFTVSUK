import streamlit as st
import pandas as pd
import datetime
from io import BytesIO
from supabase import create_client, Client

# ===== KONFIGURACE SUPABASE =====
SUPABASE_URL = st.secrets["supabase"]["supabase_url"]
SUPABASE_KEY = st.secrets["supabase"]["supabase_key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# =================================

def safe_rerun():
    """Bezpečné vyvolání rerunu, pokud je podporováno"""
    try:
        st.experimental_rerun()
    except Exception:
        pass


def hr():
    """Vykreslí tlustou bílou čáru oddělující sekce"""
    st.markdown("<hr style='border-top:5px solid white;'>", unsafe_allow_html=True)


def load_data(current_year, next_year):
    resp = supabase.table("pri_rehabilitace").select("data").eq("id", 1).execute()
    if resp.data and "data" in resp.data[0]:
        data = resp.data[0]["data"]
    else:
        data = {}
    data.setdefault(str(current_year), [])
    data.setdefault(str(next_year), [])
    return data


def save_data(data):
    return supabase.table("pri_rehabilitace").update({"data": data}).eq("id", 1).execute()


def run_pri(selected_year):
    current_year = int(selected_year)
    next_year = current_year + 1

    st.title("Poukazy rehabilitace")
    st.markdown(f"Evidence rehabilitačních poukazů pro roky {current_year} a {next_year}.")

    # tlačítko Aktualizovat
    cols = st.columns([1, 3])
    with cols[0]:
        if st.button("Aktualizovat", key="pri_update"):
            safe_rerun()
    with cols[1]:
        st.markdown("**Klikni pro aktualizaci**")

    # Načtení dat do session
    if "pri_data" not in st.session_state:
        st.session_state.pri_data = load_data(current_year, next_year)
    data = st.session_state.pri_data

    # Formulář přidání
    st.subheader("Přidat nový poukaz")
    with st.form("pri_form", clear_on_submit=True):
        cislo = st.text_input("Číslo poukazu")
        datum_od = st.date_input("Datum od")
        datum_do = st.date_input("Datum do")
        zar = st.text_input("Rehabilitační zařízení")
        typ = st.text_input("Typ rehabilitace")
        prijmeni = st.text_input("Příjmení")
        poznamka = st.text_area("Poznámka")
        rok_vyber = st.selectbox("Rok", [str(current_year), str(next_year)], index=0)
        if st.form_submit_button("➕ Přidat řádek"):
            novy = {
                "Číslo poukazu": cislo,
                "Datum od": datum_od.strftime("%Y-%m-%d"),
                "Datum do": datum_do.strftime("%Y-%m-%d"),
                "Rehabilitační zařízení": zar,
                "Typ rehabilitace": typ,
                "Příjmení": prijmeni,
                "Poznámka": poznamka
            }
            data[rok_vyber].append(novy)
            save_data(data)
            st.success("Poukaz byl přidán!")
            safe_rerun()

    # Výpis, export, mazání a editace pro každý rok
    for rok in [str(current_year), str(next_year)]:
        hr()
        st.subheader(f"Poukazy na rok {rok}")
        df = pd.DataFrame(data[rok])
        if df.empty:
            st.info("Žádné záznamy.")
        else:
            # Zobraz DataFrame
            st.dataframe(df, use_container_width=True)

            # Export do Excelu
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name=f"Poukazy_{rok}")
            buf.seek(0)
            st.download_button(
                "📥 Exportovat do Excelu",
                data=buf.getvalue(),
                file_name=f"poukazy_rehabilitace_{rok}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # Oddělující čára pod tlačítkem exportu
            hr()

            # Mazání řádku
            row_to_delete = st.selectbox(
                "Vyberte řádek k odstranění",
                options=df.index,
                key=f"pri_delete_{rok}",
                format_func=lambda idx: f"{df.loc[idx,'Číslo poukazu']} – {df.loc[idx,'Příjmení']}"
            )
            if st.button("❌ Smazat řádek", key=f"pri_delete_btn_{rok}"):
                data[rok].pop(row_to_delete)
                save_data(data)
                st.success("Řádek byl smazán!")
                safe_rerun()

            # Ruční editace
            hr()
            st.markdown("##### Upravit ručně")
            idx_edit = st.selectbox(
                "Vyberte řádek k úpravě",
                options=df.index,
                key=f"pri_edit_select_{rok}",
                format_func=lambda i: f"{df.loc[i,'Číslo poukazu']} – {df.loc[i,'Příjmení']}"
            )
            orig = data[rok][idx_edit]
            with st.form(f"pri_edit_form_{rok}_{idx_edit}", clear_on_submit=True):
                cislo_e = st.text_input("Číslo poukazu", value=orig.get("Číslo poukazu",""))
                od_e    = st.date_input("Datum od", value=datetime.datetime.strptime(orig.get("Datum od","1970-01-01"),"%Y-%m-%d"))
                do_e    = st.date_input("Datum do", value=datetime.datetime.strptime(orig.get("Datum do","1970-01-01"),"%Y-%m-%d"))
                zar_e   = st.text_input("Rehabilitační zařízení", value=orig.get("Rehabilitační zařízení",""))
                typ_e   = st.text_input("Typ rehabilitace", value=orig.get("Typ rehabilitace",""))
                prij_e  = st.text_input("Příjmení", value=orig.get("Příjmení",""))
                poz_e   = st.text_area("Poznámka", value=orig.get("Poznámka",""))
                if st.form_submit_button("💾 Uložit změny"):
                    updated = {
                        "Číslo poukazu": cislo_e,
                        "Datum od": od_e.strftime("%Y-%m-%d"),
                        "Datum do": do_e.strftime("%Y-%m-%d"),
                        "Rehabilitační zařízení": zar_e,
                        "Typ rehabilitace": typ_e,
                        "Příjmení": prij_e,
                        "Poznámka": poz_e
                    }
                    data[rok][idx_edit] = updated
                    save_data(data)
                    st.success("Záznam upraven!")
                    safe_rerun()

if __name__ == "__main__":
    run_pri(datetime.datetime.now().year)
