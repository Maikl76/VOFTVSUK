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
SUPABASE_URL = "https://bgtpylewilzcqfqaoixx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJndHB5bGV3aWx6Y3FmcWFvaXh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ1NzQxNTQsImV4cCI6MjA2MDE1MDE1NH0.6NutsH1g8k0ruhpylqltrWD53HQFy-ZQjcUN-SULktM"  # Nahraďte svým skutečným klíčem
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
    selected_items = {}
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
    for item in items:
        st.markdown(f"#### {item}")
        include = st.checkbox("Zobrazit", key=f"include_{item}")
        finished = st.checkbox("Hotovo", key=f"finished_{item}")
        if finished:
            st.markdown(f"<span style='color: green;'>{item} - hotovo</span>", unsafe_allow_html=True)
        selected_items[item] = include
    st.markdown("---")
    include_celkovy = st.checkbox("Zobrazit celkové vyhodnocení", key="include_celkovy")
    st.write("")

# Nastavení hesla
PASSWORD = "1954"
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
    st.image("Logo.png", width=50)  # Upravte podle potřeby
with col2:
    st.markdown("<h1 style='margin-bottom: 0;'>Vojenský obor FTVS UK</h1>", unsafe_allow_html=True)

# Custom CSS
st.markdown(
    """
    <style>
    .ql-editor {
        font-family: "Times New Roman", serif;
        font-size: 14px;
    }
    .stTextInput>div>div>input {
        max-width: 100px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def format_table(doc_table, font_size=10):
    doc_table.style = "Table Grid"
    for row in doc_table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(font_size)

# Funkce pro evaluace pomocí Supabase
def load_evaluations():
    response = supabase.table("evaluations").select("data").eq("id", 1).execute()
    if response.data and "data" in response.data[0]:
        return response.data[0]["data"]
    else:
        return {}

def save_evaluations(new_data):
    response = supabase.table("evaluations").update({"data": new_data}).eq("id", 1).execute()
    return response

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
    current_year = st.number_input("Rok", min_value=2000, max_value=2100, value=datetime.datetime.now().year, step=1)
    selected_period = st.selectbox("Vyberte období", list(evaluation_periods.keys()))
    period_range = evaluation_periods[selected_period]
    st.write(f"Zvolená doba: {selected_period} ({period_range[0]} až {period_range[1]})")
    key_period = f"{current_year}_{selected_period}"
    saved_eval = st.session_state.evaluations.get(key_period, {})
    if st.session_state.get("include_celkovy", False):
        eval_items = items
    else:
        eval_items = [item for item in items if st.session_state.get(f"include_{item}", False)]
    if not eval_items:
        st.info("Vyberte alespoň jednu položku v postranním panelu.")
    else:
        st.markdown("### Vyplňte nebo upravte vyhodnocení")
        eval_data = {}
        for item in eval_items:
            default_text = saved_eval.get(item, {}).get("text", "")
            st.markdown(f"Vyhodnocení pro {item}:")
            text = st_quill(key=f"eval_{current_year}_{selected_period}_{item}", value=default_text)
            default_finished = saved_eval.get(item, {}).get("finished", False)
            finished_flag = st.checkbox("Hotovo", key=f"finished_form_{current_year}_{selected_period}_{item}", value=default_finished)
            eval_data[item] = {"text": text, "finished": finished_flag}
        if st.button("Uložit vyhodnocení", key="save_eval"):
            st.session_state.evaluations[key_period] = eval_data
            save_evaluations(st.session_state.evaluations)
            st.success("Vyhodnocení uloženo!")
with tabs[1]:
    st.header("Historie vyhodnocení")
    hist_year = st.number_input("Zvolte rok", min_value=2000, max_value=2100, value=datetime.datetime.now().year, step=1, key="hist_year")
    hist_period = st.selectbox("Vyberte období", list(evaluation_periods.keys()), key="hist_period")
    key = f"{hist_year}_{hist_period}"
    if key in st.session_state.evaluations:
        st.subheader(f"Vyhodnocení za {key}")
        evals = st.session_state.evaluations[key]
        for item, data in evals.items():
            finished_mark = " (hotovo)" if data.get("finished") else ""
            st.markdown(f"### {item}{finished_mark}")
            st.write(data.get("text", ""))
    else:
        st.info("Pro zvolený rok a období nejsou uložena žádná vyhodnocení.")
with tabs[2]:
    dpp.run_dpp()
with tabs[3]:
    selected_year = st.number_input("Zvolte rok pro evidenci PR-I", min_value=2000, max_value=2100, value=datetime.datetime.now().year, step=1)
    pri.run_pri(selected_year)
with tabs[4]:
    zsc.run_zsc()
with tabs[5]:
    st.header("Student")
    student_subtabs = st.tabs(["Vojenské předměty", "Přidat studenta", "Editace studenta", "Souhrn"])
    with student_subtabs[0]:
        st.subheader("Vojenské předměty")
        cohort_tabs = st.tabs(["První ročník", "Druhý ročník", "Třetí ročník", "Čtvrtý ročník", "Pátý ročník"])
        with cohort_tabs[0]:
            import student_1Bc
            student_1Bc.run_student()
        with cohort_tabs[1]:
            import student_2Bc
            student_2Bc.run_student()
        with cohort_tabs[2]:
            import student_3Bc
            student_3Bc.run_student()
        with cohort_tabs[3]:
            import student_1Mgr
            student_1Mgr.run_student()
        with cohort_tabs[4]:
            import student_2Mgr
            student_2Mgr.run_student()
    with student_subtabs[1]:
        import student
        student.run_add_student()
    with student_subtabs[2]:
        import student
        student.run_edit_student()
    with student_subtabs[3]:
        run_summary()
