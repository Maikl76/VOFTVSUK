import streamlit as st
st.set_page_config(layout="wide", page_title="Vojenský obor FTVS UK")  # Musí být první streamlit příkaz!

import json
import os
import datetime
import pandas as pd
from docx import Document
from docx.shared import Pt, Inches
from io import BytesIO, StringIO
import csv
from streamlit_quill import st_quill  # WYSIWYG editor

# ===== KONFIGURACE SUPABASE =====
from supabase import create_client, Client
# Nahraďte tyto hodnoty vašimi údaji
SUPABASE_URL = "https://bgtpylewilzcqfqaoixx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJndHB5bGV3aWx6Y3FmcWFvaXh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ1NzQxNTQsImV4cCI6MjA2MDE1MDE1NH0.6NutsH1g8k0ruhpylqltrWD53HQFy-ZQjcUN-SULktM"
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

# Nastavení hesla – změňte dle potřeby
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
    st.image("Logo.png", width=50)  # Upravte cestu/velikost podle potřeby
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

# Funkce pro práci s evaluacemi pomocí Supabase
def load_evaluations():
    # Předpokládáme, že tabulka evaluations má jediný řádek s ID = 1 a sloupec data (JSONB)
    response = supabase.table("evaluations").select("data").eq("id", 1).execute()
    if response.data and "data" in response.data[0]:
        return response.data[0]["data"]
    else:
        return {}

def save_evaluations(new_data):
    # Aktualizace řádku s ID = 1
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

items = [
    "Souhrnný přehled APVVP",
    "VŠ vzdělávání", "Přijímačky", "Akreditace", "Vědecká činnost",
    "Zahraniční spolupráce",
    "Personální oblast", "Logistika", "Ekonomika", "Odborné kurzy", "Vojenská příprava", "Jazykové vzdělávání"
]

custom_headings = {
    "Souhrnný přehled APVVP": "1. Souhrnný přehled o stavu plnění opatření, úkolů a dílčích úkolů – APV VP",
    "VŠ vzdělávání": "2.1.1 Vysokoškolské vzdělávání personálu pro potřeby rezortu MO",
    "Přijímačky": "2.1.2 Přijmout stanovené množství studentů podle požadavku rezortu MO",
    "Akreditace": "2.1.3 Akreditované studijní programy",
    "Vědecká činnost": "2.1.4 Vědecká činnost",
    "Zahraniční spolupráce": "2.1.5 Spolupracovat s vysokými školami a zajistit zahraniční styky",
    "Personální oblast": "2.2.1 Zabezpečit personální oblast VO FTVS UK",
    "Logistika": "2.2.2 Realizovat logistické zabezpečení VO FTVS UK",
    "Ekonomika": "2.2.3 Zabezpečit ekonomickou oblast VO FTVS UK",
    "Odborné kurzy": "2.2.5 Realizovat odborné a kariérové kurzy u VO FTVS UK",
    "Vojenská příprava": "2.2.6 Zabezpečit vojenskou oblast VO FTVS UK",
    "Jazykové vzdělávání": "2.2.7 Realizovat jazykové vzdělávání"
}

desired_columns = [
    "TaD-I", "TaD-II", "TaD-III",
    "TaD-1", "TaD-2", "TaD-3",
    "ZSTP-I", "ZSTP-II", "ZSTP-III",
    "ZSTP-1", "ZSTP-2",
    "STP-I", "STP-II", "STP-III",
    "STP-1", "STP-2",
    "Kurz BZ-I", "Kurz BZ-II", "Kurz BZ-III", "Kurz BZ-IV",
    "Kurz VL-I", "Kurz VL-II", "Kurz VL-III", "Kurz VL-IV",
    "Kurz PSL", "Kurz PSL-I", "Kurz PSL-II",
    "Kurz ZP-I", "Kurz ZP-II",
    "Kurz VPL-I", "Kurz VPL-II",
    "Kurz STP-I", "Kurz STP-II",
    "Instr. BZ", "Instr. VL", "Instr. PSL", "Instr. ZP", "Instr. VPL"
]

subject_mapping = {
    "Teorie a didaktika AČR-I": "TaD-I",
    "Teorie a didaktika AČR-II": "TaD-II",
    "Teorie a didaktika AČR-III": "TaD-III",
    "Teorie a didaktika AČR-1": "TaD-1",
    "Teorie a didaktika AČR-2": "TaD-2",
    "Teorie a didaktika AČR-3": "TaD-3",
    "Základy STP-I": "ZSTP-I",
    "Základy STP-II": "ZSTP-II",
    "Základy STP-III": "ZSTP-III",
    "Základy STP-1": "ZSTP-1",
    "Základy STP-2": "ZSTP-2",
    "Speciální TP-I": "STP-I",
    "Speciální TP-II": "STP-II",
    "Speciální TP-III": "STP-III",
    "Speciální TP-1": "STP-1",
    "Speciální TP-2": "STP-2",
    "Kurz BZ-I": "Kurz BZ-I",
    "Kurz BZ-II": "Kurz BZ-II",
    "Kurz BZ-III": "Kurz BZ-III",
    "Kurz BZ-IV": "Kurz BZ-IV",
    "Kurz VL-I": "Kurz VL-I",
    "Kurz VL-II": "Kurz VL-II",
    "Kurz VL-III": "Kurz VL-III",
    "Kurz VL-IV": "Kurz VL-IV",
    "Kurz PSL": "Kurz PSL",
    "Kurz PSL-I": "Kurz PSL-I",
    "Kurz PSL-II": "Kurz PSL-II",
    "Kurz ZP-I": "Kurz ZP-I",
    "Kurz ZP-II": "Kurz ZP-II",
    "Kurz VPL-I": "Kurz VPL-I",
    "Kurz VPL-II": "Kurz VPL-II",
    "Kurz STP-I": "Kurz STP-I",
    "Kurz STP-II": "Kurz STP-II",
    "VL-IV Instrukor": "Instr. VL",
    "BZ-IV Instruktor": "Instr. BZ",
    "PSL-II Instruktor": "Instr. PSL",
    "ZP-II Instruktor": "Instr. ZP",
    "VPL-II Instruktor": "Instr. VPL"
}

grade_required = {"TaD-III", "TaD-3", "ZSTP-III", "ZSTP-2", "STP-2", "Kurz STP-II"}

def extract_subjects(student):
    result = {col: "NE" for col in desired_columns}
    subj_struct = student.get("subjects", {})
    for sem, groups in subj_struct.items():
        if not isinstance(groups, dict):
            continue
        for group, subj_dict in groups.items():
            if not isinstance(subj_dict, dict):
                continue
            for subj_full, details in subj_dict.items():
                if subj_full in subject_mapping:
                    abbr = subject_mapping[subj_full]
                    if isinstance(details, dict) and "instruktor" in details:
                        value = "ANO" if details.get("instruktor", False) else "NE"
                    elif abbr in grade_required:
                        if isinstance(details, dict):
                            grade = details.get("grade", "").strip()
                            value = grade if grade else ("ANO" if details.get("completed", False) else "NE")
                        else:
                            value = "ANO" if details else "NE"
                    else:
                        if isinstance(details, dict):
                            value = "ANO" if details.get("completed", False) else "NE"
                        else:
                            value = "ANO" if details else "NE"
                    if abbr in result:
                        if result[abbr] != "ANO" and value != "NE":
                            result[abbr] = value
                        elif value == "ANO":
                            result[abbr] = "ANO"
                    else:
                        result[abbr] = value
    for abbr in desired_columns:
        if abbr not in result:
            result[abbr] = "NE"
    return result

def run_summary():
    st.header("Souhrn všech studentů")
    students = load_students()
    if not students:
        st.info("Žádní studenti nejsou zaregistrováni.")
        return
    base_cols = ["Hodnost", "Jméno", "Příjmení", "Ročník", "Kohorta"]
    summary_records = []
    for s in students:
        base = {
            "Hodnost": s.get("hodnost", ""),
            "Jméno": s.get("first_name", ""),
            "Příjmení": s.get("last_name", ""),
            "Ročník": s.get("cohort", ""),
            "Kohorta": s.get("study_type", "")
        }
        subj_vals = extract_subjects(s)
        record = {**base, **subj_vals}
        summary_records.append(record)
    columns = base_cols + desired_columns
    df = pd.DataFrame(summary_records, columns=columns)
    st.dataframe(df, use_container_width=True)
    if st.button("Exportovat do Excelu"):
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Studenti")
        data = buffer.getvalue()
        st.download_button(label="Stáhnout Excel soubor", data=data, file_name="Studenti_souhrn.xlsx", mime="application/vnd.ms-excel")

COHORT = "3. Bc."
DISPLAY_NAME = "Třetí ročník (3. Bc.)"

def run_student():
    st.title("Systém studentů - " + DISPLAY_NAME)
    students = load_students()
    cohort_students = [s for s in students if s.get("cohort") == COHORT]
    if not cohort_students:
        st.info("Žádní studenti z tohoto ročníku nejsou zaregistrováni.")
        return
    df = pd.DataFrame(cohort_students)
    st.dataframe(df, use_container_width=True)
    selected_idx = st.selectbox("Vyberte studenta", options=df.index,
                                format_func=lambda i: f"{df.loc[i, 'hodnost']} {df.loc[i, 'first_name']} {df.loc[i, 'last_name']}")
    current_student = deepcopy(cohort_students[selected_idx])
    if "subjects" not in current_student:
        current_student["subjects"] = deepcopy(default_structure_3Bc)
    else:
        for sem in default_structure_3Bc:
            current_student["subjects"].setdefault(sem, {})
            for subj, details in default_structure_3Bc[sem].items():
                current_student["subjects"][sem].setdefault(subj, deepcopy(details))
    
    st.markdown("## Předmětové hodnocení")
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("Zimní semestr")
        st.markdown("#### Základy STP-III")
        with st.expander("Detail hodnocení", expanded=True):
            col1, col2 = st.columns([0.3, 0.3])
            with col1:
                zim_zap_chk = st.checkbox("Zápočet", 
                                          value=current_student["subjects"]["zimni"]["Základy STP-III"].get("Zápočet", {}).get("completed", False),
                                          key="3Bc_STP3_Zápočet")
            with col2:
                zim_zap_teacher = st.text_input("Učitel, který zapsal", 
                                                value=current_student["subjects"]["zimni"]["Základy STP-III"].get("Zápočet", {}).get("teacher", ""),
                                                key="3Bc_STP3_Zápočet_teacher", max_chars=10)
            current_student["subjects"]["zimni"]["Základy STP-III"]["Zápočet"] = {"completed": zim_zap_chk, "teacher": zim_zap_teacher}
            
            col1, col2, col3 = st.columns([0.25, 0.1, 0.15])
            with col1:
                zim_zk_chk = st.checkbox("Zkouška", 
                                         value=current_student["subjects"]["zimni"]["Základy STP-III"].get("Zkouška", {}).get("completed", False),
                                         key="3Bc_STP3_Zkouška")
            with col2:
                zim_zk_grade = st.text_input("Známka", 
                                             value=current_student["subjects"]["zimni"]["Základy STP-III"].get("Zkouška", {}).get("grade", ""),
                                             key="3Bc_STP3_Zkouška_grade", max_chars=3)
            with col3:
                zim_zk_teacher = st.text_input("Učitel, který zapsal", 
                                               value=current_student["subjects"]["zimni"]["Základy STP-III"].get("Zkouška", {}).get("teacher", ""),
                                               key="3Bc_STP3_Zkouška_teacher", max_chars=10)
            current_student["subjects"]["zimni"]["Základy STP-III"]["Zkouška"] = {"completed": zim_zk_chk, "grade": zim_zk_grade, "teacher": zim_zk_teacher}
            cond_stp3 = all(current_student["subjects"]["zimni"]["Základy STP-III"][s]["completed"] for s in ["Zápočet", "Zkouška"])
            st.markdown("Splněno: **" + ("ANO" if cond_stp3 else "NE") + "**")
        
        st.markdown("#### Speciální TP-III")
        with st.expander("Detail hodnocení", expanded=True):
            for subj in ["Kurz BZ-III", "Kurz PSL-I", "Zápočet"]:
                col1, col2 = st.columns([0.3, 0.3])
                with col1:
                    spec_chk = st.checkbox(subj, value=current_student["subjects"]["zimni"]["Speciální TP-III"].get(subj, {}).get("completed", False), key="3Bc_SPT3_" + subj)
                with col2:
                    spec_teacher = st.text_input("Učitel, který zapsal", value=current_student["subjects"]["zimni"]["Speciální TP-III"].get(subj, {}).get("teacher", ""), key="3Bc_SPT3_" + subj + "_teacher", max_chars=10)
                current_student["subjects"]["zimni"]["Speciální TP-III"][subj] = {"completed": spec_chk, "teacher": spec_teacher}
            cond_spec = all(current_student["subjects"]["zimni"]["Speciální TP-III"][s]["completed"] for s in ["Kurz BZ-III", "Kurz PSL-I", "Zápočet"])
            st.markdown("Splněno: **" + ("ANO" if cond_spec else "NE") + "**")
    
    with col_right:
        st.subheader("Letní semestr")
        st.markdown("#### Teorie a didaktika AČR-III")
        with st.expander("Detail hodnocení", expanded=True):
            col1, col2 = st.columns([0.3, 0.3])
            with col1:
                let_tacr_zap_chk = st.checkbox("Zápočet", value=current_student["subjects"]["letni"]["Teorie a didaktika AČR-III"].get("Zápočet", {}).get("completed", False), key="3Bc_let_TACR_Zápočet")
            with col2:
                let_tacr_zap_teacher = st.text_input("Učitel, který zapsal", value=current_student["subjects"]["letni"]["Teorie a didaktika AČR-III"].get("Zápočet", {}).get("teacher", ""), key="3Bc_let_TACR_Zápočet_teacher", max_chars=10)
            current_student["subjects"]["letni"]["Teorie a didaktika AČR-III"]["Zápočet"] = {"completed": let_tacr_zap_chk, "teacher": let_tacr_zap_teacher}
            
            col3, col4, col5 = st.columns([0.25, 0.1, 0.15])
            with col3:
                let_tacr_zk_chk = st.checkbox("Zkouška", value=current_student["subjects"]["letni"]["Teorie a didaktika AČR-III"].get("Zkouška", {}).get("completed", False), key="3Bc_let_TACR_Zk")
            with col4:
                let_tacr_zk_grade = st.text_input("Známka", value=current_student["subjects"]["letni"]["Teorie a didaktika AČR-III"].get("Zkouška", {}).get("grade", ""), key="3Bc_let_TACR_Zk_grade", max_chars=3)
            with col5:
                let_tacr_zk_teacher = st.text_input("Učitel, který zapsal", value=current_student["subjects"]["letni"]["Teorie a didaktika AČR-III"].get("Zkouška", {}).get("teacher", ""), key="3Bc_let_TACR_Zk_teacher", max_chars=10)
            current_student["subjects"]["letni"]["Teorie a didaktika AČR-III"]["Zkouška"] = {"completed": let_tacr_zk_chk, "grade": let_tacr_zk_grade, "teacher": let_tacr_zk_teacher}
            cond_tacr = (current_student["subjects"]["letni"]["Teorie a didaktika AČR-III"].get("Zápočet", {}).get("completed", False) and 
                         current_student["subjects"]["letni"]["Teorie a didaktika AČR-III"].get("Zkouška", {}).get("completed", False))
            st.markdown("Splněno: **" + ("ANO" if cond_tacr else "NE") + "**")
            current_student["subjects"]["letni"]["Teorie a didaktika AČR-III"]["Splněno"] = {"value": "ANO" if cond_tacr else "NE"}
    
    if st.button("Uložit hodnocení", key="save_3Bc_" + str(current_student.get("id_op", ""))):
        save_student_record(current_student)
        st.success("Hodnocení uloženo!")
        try:
            st.experimental_rerun()
        except AttributeError:
            pass

if __name__ == "__main__":
    run_student()
