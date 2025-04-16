import streamlit as st
import pandas as pd
from supabase import create_client, Client
import datetime
from io import BytesIO
import json, os
from copy import deepcopy

# Inicializace Supabase klienta
SUPABASE_URL = "https://bgtpylewilzcqfqaoixx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJndHB5bGV3aWx6Y3FmcWFvaXh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ1NzQxNTQsImV4cCI6MjA2MDE1MDE1NH0.6NutsH1g8k0ruhpylqltrWD53HQFy-ZQjcUN-SULktM"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_students():
    try:
        response = supabase.table("students").select("*").execute()
        return response.data or []
    except Exception as e:
        st.error("Chyba při načítání studentů: " + str(e))
        return []

def save_students(updated_student):
    try:
        response = supabase.table("students").update(updated_student).eq("id_op", updated_student["id_op"]).execute()
        return response.data
    except Exception as e:
        st.error("Chyba při aktualizaci studenta: " + str(e))
        return None

def insert_student(new_student):
    try:
        response = supabase.table("students").insert(new_student).execute()
        return response.data
    except Exception as e:
        st.error("Chyba při vkládání nového studenta: " + str(e))
        return None

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
    if not students:
        st.info("Žádní studenti nejsou k dispozici ke změně.")
        return

    df = pd.DataFrame(students)
    if df.empty:
        st.info("Žádní studenti nejsou k dispozici ke změně.")
        return

    df_display = df.drop(columns=["subjects"], errors="ignore")
    st.dataframe(df_display, use_container_width=True)
    
    selected_index = st.selectbox(
        "Vyberte studenta ke změně",
        options=list(df.index),
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
