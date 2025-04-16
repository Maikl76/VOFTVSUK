import streamlit as st
import json, os, datetime
import pandas as pd
from docx import Document
from docx.shared import Pt, Inches
from io import BytesIO, StringIO
from streamlit_quill import st_quill  # WYSIWYG editor
import csv

# ===== KONFIGURACE SUPABASE =====
from supabase import create_client, Client
# Nahraďte tyto hodnoty vašimi údaji
SUPABASE_URL = "https://bgtpylewilzcqfqaoixx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJndHB5bGV3aWx6Y3FmcWFvaXh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ1NzQxNTQsImV4cCI6MjA2MDE1MDE1NH0.6NutsH1g8k0ruhpylqltrWD53HQFy-ZQjcUN-SULktM"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# =================================

# Dummy moduly, pokud dpp, pri a zsc nejsou k dispozici
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

st.set_page_config(layout="wide")

# Hlavička – logo a název
col1, col2 = st.columns([1, 6])
with col1:
    st.image("Logo.png", width=50)
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

# Načteme evaluace a uložíme je do session_state, pokud ještě neexistují
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
    # Načteme data ze Supabase – předpokládáme, že tabulka "students" obsahuje sloupec "subjects" s uloženými JSON daty.
    response = supabase.table("students").select("*").execute()
    students = response.data
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
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Studenti")
        processed_data = output.getvalue()
        st.download_button(label="Stáhnout Excel soubor", data=processed_data, file_name="Studenti_souhrn.xlsx", mime="application/vnd.ms-excel")

# Importované funkce se budou volat z hlavní aplikace
def run_add_student():
    st.header("Přidat nového studenta")
    with st.form(key="add_student_form", clear_on_submit=True):
        hodnost = st.selectbox("Hodnost", ["--", "svob.", "des.", "čet.", "rtn. Bc.", "rtm. Bc."], key="add_hodnost")
        first_name = st.text_input("Jméno", key="add_first_name")
        last_name = st.text_input("Příjmení", key="add_last_name")
        date_of_birth = st.date_input("Datum narození", min_value=datetime.date(1960, 1, 1), key="add_dob")
        address = st.text_input("Bydliště", key="add_address")
        phone = st.text_input("Telefon", key="add_phone")
        email = st.text_input("Email", key="add_email")
        id_op = st.text_input("ID-OP", key="add_id_op")
        id_sp = st.text_input("ID-SP", key="add_id_sp")
        note = st.text_area("Poznámka", key="add_note")
        study_type = st.selectbox("Typ studia", ["Prezenční", "Kombinované"], key="add_study_type")
        cohorts = ["1. Bc.", "2. Bc.", "3. Bc.", "1. Mgr.", "2. Mgr."]
        cohort = st.selectbox("Ročník", cohorts, key="add_cohort")
        submitted = st.form_submit_button("Přidat studenta")
        if submitted:
            new_student = {
                "hodnost": hodnost,
                "first_name": first_name,
                "last_name": last_name,
                "date_of_birth": date_of_birth.strftime("%Y-%m-%d"),
                "address": address,
                "phone": phone,
                "email": email,
                "id_op": id_op,
                "id_sp": id_sp,
                "note": note,
                "study_type": study_type,
                "cohort": cohort,
                "subjects": {},
                "is_graduated": False
            }
            insert_student(new_student)
            st.success("Nový student přidán!")
            st.experimental_rerun()

def run_edit_student():
    st.header("Editace studenta")
    students = load_students()
    if students:
        df = pd.DataFrame(students)
    else:
        df = pd.DataFrame(columns=["hodnost", "first_name", "last_name", "date_of_birth",
                                   "address", "phone", "email", "id_op", "id_sp", "note",
                                   "study_type", "cohort", "subjects", "is_graduated"])
    df_display = df.drop(columns=["subjects"], errors="ignore")
    st.dataframe(df_display, use_container_width=True)
    
    selected_index = st.selectbox(
        "Vyberte studenta ke změně",
        options=df.index,
        format_func=lambda i: f"{df.loc[i, 'hodnost']} {df.loc[i, 'first_name']} {df.loc[i, 'last_name']} ({df.loc[i, 'cohort']})",
        key="select_student_edit"
    )
    selected_student = df.loc[selected_index].to_dict()
    with st.form(key="edit_student_form"):
        new_hodnost = st.selectbox("Hodnost", ["--", "svob.", "des.", "čet.", "rtn. Bc.", "rtm. Bc."],
                                   index=["--", "svob.", "des.", "čet.", "rtn. Bc.", "rtm. Bc."].index(selected_student.get("hodnost", "svob.")),
                                   key="edit_hodnost")
        new_first_name = st.text_input("Jméno", value=selected_student.get("first_name", ""), key="edit_first_name")
        new_last_name = st.text_input("Příjmení", value=selected_student.get("last_name", ""), key="edit_last_name")
        dob_default = datetime.datetime.strptime(selected_student.get("date_of_birth"), "%Y-%m-%d") if selected_student.get("date_of_birth") else datetime.datetime.now()
        new_dob = st.date_input("Datum narození", value=dob_default, min_value=datetime.date(1960, 1, 1), key="edit_dob")
        new_address = st.text_input("Bydliště", value=selected_student.get("address", ""), key="edit_address")
        new_phone = st.text_input("Telefon", value=selected_student.get("phone", ""), key="edit_phone")
        new_email = st.text_input("Email", value=selected_student.get("email", ""), key="edit_email")
        new_id_op = st.text_input("ID-OP", value=selected_student.get("id_op", ""), key="edit_id_op")
        new_id_sp = st.text_input("ID-SP", value=selected_student.get("id_sp", ""), key="edit_id_sp")
        new_note = st.text_area("Poznámka", value=selected_student.get("note", ""), key="edit_note")
        new_study_type = st.selectbox("Typ studia", ["Prezenční", "Kombinované"],
                                      index=["Prezenční", "Kombinované"].index(selected_student.get("study_type", "Prezenční")),
                                      key="edit_study_type")
        cohorts = ["1. Bc.", "2. Bc.", "3. Bc.", "1. Mgr.", "2. Mgr."]
        new_cohort = st.selectbox("Ročník", cohorts,
                                  index=cohorts.index(selected_student.get("cohort", cohorts[0])),
                                  key="edit_cohort")
        graduated = st.checkbox("Absolvent", value=selected_student.get("is_graduated", False), key="edit_graduated")
        submitted_edit = st.form_submit_button("Uložit změny")
        if submitted_edit:
            updated_student = deepcopy(selected_student)
            updated_student.update({
                "hodnost": new_hodnost,
                "first_name": new_first_name,
                "last_name": new_last_name,
                "date_of_birth": new_dob.strftime("%Y-%m-%d"),
                "address": new_address,
                "phone": new_phone,
                "email": new_email,
                "id_op": new_id_op,
                "id_sp": new_id_sp,
                "note": new_note,
                "study_type": new_study_type,
                "cohort": new_cohort,
                "is_graduated": graduated
            })
            save_students(updated_student)
            st.success("Student upraven!")
            st.experimental_rerun()

def run_graduates():
    st.header("Absolventi")
    students = load_students()
    graduates = [s for s in students if s.get("is_graduated", False)]
    if not graduates:
        st.info("Žádní absolventi nejsou evidováni.")
        return
    df = pd.DataFrame(graduates)
    st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    # Pro testování odkomentujte jednu z funkcí:
    # run_add_student()
    # run_edit_student()
    # run_graduates()
    pass

