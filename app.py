import streamlit as st
st.set_page_config(layout="wide", page_title="Vojenský obor FTVS UK")  # Musí být první streamlit příkaz!

import os
import json
import datetime
import pandas as pd
import csv
from io import BytesIO, StringIO
from docx import Document
from docx.shared import Pt, Inches
from streamlit_quill import st_quill  # WYSIWYG editor

# ===== KONFIGURACE SUPABASE =====
from supabase import create_client, Client
SUPABASE_URL = st.secrets["supabase"]["supabase_url"]
SUPABASE_KEY = st.secrets["supabase"]["supabase_key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# =================================

# Dummy moduly – pokud dpp, pri a zsc nejsou dostupné
try:
    import dpp
except ModuleNotFoundError:
    class DummyDPP:
        def run_dpp(self):
            st.info("Modul DPP není k dispozici.")
    dpp = DummyDPP()

try:
    import pri
except ModuleNotFoundError:
    class DummyPRI:
        def run_pri(self, year):
            st.info("Modul PRI není k dispozici.")
    pri = DummyPRI()

try:
    import zsc
except ModuleNotFoundError:
    class DummyZSC:
        def run_zsc(self):
            st.info("Modul ZSC není k dispozici.")
    zsc = DummyZSC()

# Sidebar – expander s nastavením položek vyhodnocení
with st.sidebar.expander("Nastavení položek vyhodnocení"):
    items = [
        "Souhrnný přehled APVVP",
        "VŠ vzdělávání",
        "Přijímačky",
        "Akreditace",
        "Vědecká činnost",
        "Zahraniční spolupráce",
        "Personální oblast",
        "Logistika",
        "Ekonomika",
        "Odborné kurzy",
        "Vojenská příprava",
        "Jazykové vzdělávání"
    ]
    selected_items = {}
    for item in items:
        st.markdown(f"#### {item}")
        include = st.checkbox("Zobrazit", key=f"include_{item}")
        finished = st.checkbox("Hotovo", key=f"finished_{item}")
        if finished:
            st.markdown(f"<span style='color: green;'>{item} - hotovo</span>", unsafe_allow_html=True)
        selected_items[item] = include
    st.markdown("---")
    include_celkovy = st.checkbox("Zobrazit celkové vyhodnocení", key="include_celkovy")

# Autentizace
PASSWORD = st.secrets["app"]["login_password"]
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("Přihlášení")
    pwd = st.text_input("Zadejte heslo", type="password")
    if st.button("Přihlásit se"):
        if pwd == PASSWORD:
            st.session_state["authenticated"] = True
            st.success("Přihlášení proběhlo úspěšně!")
        else:
            st.error("Špatné heslo!")
    st.stop()

# Hlavička – logo a název
col1, col2 = st.columns([1, 6])
with col1:
    st.image("Logo.png", width=50)
with col2:
    st.markdown("<h1 style='margin-bottom: 0;'>Vojenský obor FTVS UK</h1>", unsafe_allow_html=True)

# Custom CSS
st.markdown("""
    <style>
    .ql-editor { font-family: "Times New Roman", serif; font-size:14px; }
    .stTextInput>div>div>input { max-width:100px; }
    </style>
""", unsafe_allow_html=True)

def format_table(doc_table, font_size=10):
    doc_table.style = "Table Grid"
    for row in doc_table.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(font_size)

# Funkce pro souhrn studentů
def run_summary():
    st.header("Souhrn všech studentů")
    try:
        resp = supabase.table("students").select("*").execute()
        students = resp.data or []
    except Exception as e:
        st.error(f"Chyba při načítání studentů: {e}")
        return
    if not students:
        st.info("Žádní studenti nejsou zaregistrováni.")
        return

    # Definice sloupců a mapování
    desired_columns = [
        "TaD-I","TaD-II","TaD-III","TaD-1","TaD-2","TaD-3",
        "ZSTP-I","ZSTP-II","ZSTP-III","ZSTP-1","ZSTP-2",
        "STP-I","STP-II","STP-III","STP-1","STP-2",
        "Kurz BZ-I","Kurz BZ-II","Kurz BZ-III","Kurz BZ-IV",
        "Kurz VL-I","Kurz VL-II","Kurz VL-III","Kurz VL-IV",
        "Kurz PSL","Kurz PSL-I","Kurz PSL-II",
        "Kurz ZP-I","Kurz ZP-II","Kurz VPL-I","Kurz VPL-II",
        "Kurz STP-I","Kurz STP-II",
        "Instr. BZ","Instr. VL","Instr. PSL","Instr. ZP","Instr. VPL"
    ]
    mapping = {
        "Teorie a didaktika AČR-I":"TaD-I","Teorie a didaktika AČR-II":"TaD-II",
        "Teorie a didaktika AČR-III":"TaD-III","Teorie a didaktika AČR-1":"TaD-1",
        "Teorie a didaktika AČR-2":"TaD-2","Teorie a didaktika AČR-3":"TaD-3",
        "Základy STP-I":"ZSTP-I","Základy STP-II":"ZSTP-II","Základy STP-III":"ZSTP-III",
        "Základy STP-1":"ZSTP-1","Základy STP-2":"ZSTP-2",
        "Speciální TP-I":"STP-I","Speciální TP-II":"STP-II","Speciální TP-III":"STP-III",
        "Speciální TP-1":"STP-1","Speciální TP-2":"STP-2",
        **{f"Kurz BZ-{i}":f"Kurz BZ-{i}" for i in ["I","II","III","IV"]},
        **{f"Kurz VL-{i}":f"Kurz VL-{i}" for i in ["I","II","III","IV"]},
        "Kurz PSL":"Kurz PSL","Kurz PSL-I":"Kurz PSL-I","Kurz PSL-II":"Kurz PSL-II",
        "Kurz ZP-I":"Kurz ZP-I","Kurz ZP-II":"Kurz ZP-II",
        "Kurz VPL-I":"Kurz VPL-I","Kurz VPL-II":"Kurz VPL-II",
        "Kurz STP-I":"Kurz STP-I","Kurz STP-II":"Kurz STP-II",
        "BZ-IV Instruktor":"Instr. BZ","VL-IV Instruktor":"Instr. VL",
        "PSL-II Instruktor":"Instr. PSL","ZP-II Instruktor":"Instr. ZP",
        "VPL-II Instruktor":"Instr. VPL"
    }
    grade_req = {"TaD-III","TaD-3","ZSTP-III","ZSTP-2","STP-2","Kurz STP-II"}

    def extract_subjects(student):
        result = {c:"NE" for c in desired_columns}
        def walk(d):
            for k,v in d.items():
                if isinstance(v, dict) and any(isinstance(x, dict) for x in v.values()):
                    walk(v)
                else:
                    ab = mapping.get(k)
                    if not ab:
                        continue
                    if isinstance(v, dict) and "instruktor" in v:
                        val = "ANO" if v.get("instruktor") else "NE"
                    elif ab in grade_req:
                        val = v.get("grade","").strip() or ("ANO" if v.get("completed") else "NE")
                    else:
                        val = "ANO" if (isinstance(v, dict) and v.get("completed")) or v else "NE"
                    if result[ab] != "ANO" and val != "NE":
                        result[ab] = val
        walk(student.get("subjects", {}))
        return result

    records = []
    for s in students:
        base = {
            "Hodnost": s.get("hodnost",""),
            "Jméno": s.get("first_name",""),
            "Příjmení": s.get("last_name",""),
            "Ročník": s.get("cohort",""),
            "Kohorta": s.get("study_type","")
        }
        rec = {**base, **extract_subjects(s)}
        records.append(rec)

    df = pd.DataFrame(records, columns=["Hodnost","Jméno","Příjmení","Ročník","Kohorta"]+desired_columns)
    st.dataframe(df, use_container_width=True)
    if st.button("Exportovat do Excelu"):
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Studenti")
        st.download_button("Stáhnout Excel soubor",
                           buf.getvalue(),
                           "Studenti_souhrn.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Funkce pro evaluace
def load_evaluations():
    res = supabase.table("evaluations").select("data").eq("id", 1).execute()
    return res.data[0]["data"] if res.data and res.data[0].get("data") else {}

def save_evaluations(data):
    return supabase.table("evaluations").update({"data": data}).eq("id", 1).execute()

if "evaluations" not in st.session_state:
    st.session_state.evaluations = load_evaluations()

evaluation_periods = {
    "1. čtvrtletí": ("1. leden", "31. březen"),
    "1. pololetí": ("1. leden", "30. červen"),
    "3. čtvrtletí": ("1. červenec", "31. září"),
    "Celý rok": ("1. leden", "31. prosinec")
}

# Hlavní záložky
tabs = st.tabs(["Vyhodnocení VO FTVS UK", "Historie vyhodnocení", "DPP", "PR-I", "ZSC", "Student"])

with tabs[0]:
    st.header("Vyhodnocení VO FTVS UK")
    current_year = st.number_input("Rok", min_value=2000, max_value=2100,
                                   value=datetime.datetime.now().year, step=1)
    selected_period = st.selectbox("Vyberte období", list(evaluation_periods.keys()))
    period_range = evaluation_periods[selected_period]
    st.write(f"Zvolená doba: {selected_period} ({period_range[0]} až {period_range[1]})")
    key = f"{current_year}_{selected_period}"
    saved = st.session_state.evaluations.get(key, {})
    to_eval = items if include_celkovy else [i for i in items if st.session_state.get(f"include_{i}")]
    if not to_eval:
        st.info("Vyberte prosím alespoň jednu položku.")
    else:
        st.markdown("### Vyplňte nebo upravte vyhodnocení")
        new_data = {}
        for it in to_eval:
            txt = st_quill(key=f"eval_{current_year}_{selected_period}_{it}",
                           value=saved.get(it, {}).get("text",""))
            fin = st.checkbox("Hotovo", key=f"fin_{current_year}_{selected_period}_{it}",
                              value=saved.get(it, {}).get("finished", False))
            new_data[it] = {"text": txt, "finished": fin}
        if st.button("Uložit vyhodnocení"):
            st.session_state.evaluations[key] = new_data
            save_evaluations(st.session_state.evaluations)
            st.success("Vyhodnocení uloženo!")

with tabs[1]:
    st.header("Historie vyhodnocení")
    hy = st.number_input("Zvolte rok", 2000, 2100,
                         value=datetime.datetime.now().year, key="hist_year")
    hp = st.selectbox("Vyberte období", list(evaluation_periods.keys()), key="hist_period")
    k = f"{hy}_{hp}"
    if k in st.session_state.evaluations:
        st.subheader(f"Vyhodnocení za {k}")
        for it, d in st.session_state.evaluations[k].items():
            mark = " (hotovo)" if d.get("finished") else ""
            st.markdown(f"### {it}{mark}")
            st.write(d.get("text",""))
    else:
        st.info("Pro zvolený rok a období nejsou data.")

with tabs[2]:
    dpp.run_dpp()

with tabs[3]:
    y = st.number_input("Zvolte rok pro PR-I", 2000, 2100,
                        value=datetime.datetime.now().year)
    pri.run_pri(y)

with tabs[4]:
    zsc.run_zsc()

with tabs[5]:
    st.header("Student")
    sub = st.tabs(["Vojenské předměty", "Přidat studenta", "Editace studenta", "Souhrn"])
    with sub[0]:
        cohort_tabs = st.tabs(["První ročník", "Druhý ročník", "Třetí ročník", "Čtvrtý ročník", "Pátý ročník"])
        import student_1Bc, student_2Bc, student_3Bc, student_1Mgr, student_2Mgr
        with cohort_tabs[0]:
            student_1Bc.run_student()
        with cohort_tabs[1]:
            student_2Bc.run_student()
        with cohort_tabs[2]:
            student_3Bc.run_student()
        with cohort_tabs[3]:
            student_1Mgr.run_student()
        with cohort_tabs[4]:
            student_2Mgr.run_student()
    with sub[1]:
        import student; student.run_add_student()
    with sub[2]:
        import student; student.run_edit_student()
    with sub[3]:
        run_summary()
