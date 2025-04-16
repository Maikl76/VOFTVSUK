import streamlit as st
import pandas as pd
from supabase import create_client, Client
import datetime
from io import BytesIO
import json, os
from copy import deepcopy

# Inicializace Supabase klienta
SUPABASE_URL = "https://bgtpylewilzcqfqaoixx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJndHB5bGV3aWx6Y3FmcWFvaXh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ1NzQxNTQsImV4cCI6MjA2MDE1MDE1NH0.6NutsH1g8k0ruhpylqltrWD53HQFy-ZQjcUN-SULktM"  # Nahraďte svým skutečným klíčem
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_students():
    try:
        response = supabase.table("students").select("*").execute()
        return response.data or []
    except Exception as e:
        st.error("Chyba při načítání studentů: " + str(e))
        return []

def save_students(data):
    try:
        response = supabase.table("students").update(data).execute()
        return response.data
    except Exception as e:
        st.error("Chyba při ukládání studentů: " + str(e))
        return None

def run_edit_student():
    st.header("Editace studenta")
    students = load_students()
    if not students:
        st.info("Žádní studenti nejsou k dispozici ke změně.")
        return

    df = pd.DataFrame(students)
    # Zobrazíme DataFrame bez sloupce "subjects"
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
            # Aktualizace studenta v databázi (zde se odesílá kompletní seznam)
            # Pokud chcete aktualizovat jen konkrétního studenta, můžete využít i metodu update s eq("id_op", id)
            # Zde použijeme logiku: najdeme studenta v seznamu a nahradíme jej
            all_students = load_students()
            for i, s in enumerate(all_students):
                if s.get("id_op") == selected_student.get("id_op"):
                    all_students[i] = updated_student
                    break
            save_students(all_students)
            st.success("Student upraven!")
            try:
                st.experimental_rerun()
            except AttributeError:
                pass

    st.markdown("## Smazání studenta")
    confirm_delete = st.checkbox("Opravdu smazat tohoto studenta?", key=f"confirm_delete_{selected_index}")
    if confirm_delete:
        if st.button("Smazat studenta", key="delete_student_edit"):
            all_students = load_students()
            updated_students = [s for s in all_students if s.get("id_op") != selected_student.get("id_op")]
            save_students(updated_students)
            st.success("Student smazán!")
            try:
                st.experimental_rerun()
            except AttributeError:
                pass

if __name__ == "__main__":
    run_edit_student()
