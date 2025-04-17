import streamlit as st
import pandas as pd
from supabase import create_client, Client
import datetime
from copy import deepcopy

# ===== KONFIGURACE SUPABASE =====
SUPABASE_URL = st.secrets["supabase"]["supabase_url"]
SUPABASE_KEY = st.secrets["supabase"]["supabase_key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# =================================

def load_students():
    try:
        resp = supabase.table("students").select("*").execute()
        return resp.data or []
    except Exception as e:
        st.error("Chyba při načítání studentů: " + str(e))
        return []

def save_students(updated_student):
    try:
        resp = (
            supabase
            .table("students")
            .update(updated_student)
            .eq("id_op", updated_student["id_op"])
            .execute()
        )
        return resp.data
    except Exception as e:
        st.error("Chyba při aktualizaci studenta: " + str(e))
        return None

def insert_student(new_student):
    try:
        resp = supabase.table("students").insert(new_student).execute()
        return resp.data
    except Exception as e:
        st.error("Chyba při vkládání nového studenta: " + str(e))
        return None

def delete_student(student_id):
    try:
        resp = supabase.table("students").delete().eq("id_op", student_id).execute()
        return resp.data
    except Exception as e:
        st.error("Chyba při mazání studenta: " + str(e))
        return None

def run_add_student():
    cols = st.columns([8, 1])
    cols[0].header("Přidat nového studenta")
    if cols[1].button("Aktualizovat", key="update_add"):
        st.experimental_rerun()

    with st.form("add_student_form", clear_on_submit=True):
        hodnost       = st.selectbox("Hodnost", ["--","svob.","des.","čet.","rtn. Bc.","rtm. Bc."], key="add_hodnost")
        first_name    = st.text_input("Jméno", key="add_first_name")
        last_name     = st.text_input("Příjmení", key="add_last_name")
        date_of_birth = st.date_input("Datum narození", min_value=datetime.date(1960,1,1), key="add_dob")
        address       = st.text_input("Bydliště", key="add_address")
        phone         = st.text_input("Telefon", key="add_phone")
        email         = st.text_input("Email", key="add_email")
        id_op         = st.text_input("ID-OP", key="add_id_op")
        id_sp         = st.text_input("ID-SP", key="add_id_sp")
        note          = st.text_area("Poznámka", key="add_note")
        study_type    = st.selectbox("Typ studia", ["Prezenční","Kombinované"], key="add_study_type")
        cohorts       = ["1. Bc.","2. Bc.","3. Bc.","1. Mgr.","2. Mgr."]
        cohort        = st.selectbox("Ročník", cohorts, key="add_cohort")

        if st.form_submit_button("Přidat studenta"):
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
    cols = st.columns([8, 1])
    cols[0].header("Editace studenta")
    if cols[1].button("Aktualizovat", key="update_edit"):
        st.experimental_rerun()

    students = load_students()
    if not students:
        st.info("Žádní studenti nejsou k dispozici ke změně.")
        return

    df = pd.DataFrame(students)
    df_display = df.drop(columns=["id","subjects","is_graduated"], errors="ignore")
    st.dataframe(df_display, use_container_width=True)

    selected = st.selectbox(
        "Vyberte studenta ke změně",
        options=df.index,
        format_func=lambda i: f"{df.loc[i,'hodnost']} {df.loc[i,'first_name']} {df.loc[i,'last_name']} ({df.loc[i,'cohort']})",
        key="select_student_edit"
    )
    student = df.loc[selected].to_dict()

    with st.form("edit_student_form"):
        hodnost       = st.selectbox("Hodnost", ["--","svob.","des.","čet.","rtn. Bc.","rtm. Bc."],
                                     index=["--","svob.","des.","čet.","rtn. Bc.","rtm. Bc."].index(student.get("hodnost","--")),
                                     key="edit_hodnost")
        first_name    = st.text_input("Jméno", value=student.get("first_name",""), key="edit_first_name")
        last_name     = st.text_input("Příjmení", value=student.get("last_name",""), key="edit_last_name")
        dob_default   = datetime.datetime.strptime(student.get("date_of_birth","1970-01-01"), "%Y-%m-%d")
        date_of_birth = st.date_input("Datum narození", value=dob_default, min_value=datetime.date(1960,1,1), key="edit_dob")
        address       = st.text_input("Bydliště", value=student.get("address",""), key="edit_address")
        phone         = st.text_input("Telefon", value=student.get("phone",""), key="edit_phone")
        email         = st.text_input("Email", value=student.get("email",""), key="edit_email")
        id_op         = st.text_input("ID-OP", value=student.get("id_op",""), key="edit_id_op")
        id_sp         = st.text_input("ID-SP", value=student.get("id_sp",""), key="edit_id_sp")
        note          = st.text_area("Poznámka", value=student.get("note",""), key="edit_note")
        study_type    = st.selectbox("Typ studia", ["Prezenční","Kombinované"],
                                     index=["Prezenční","Kombinované"].index(student.get("study_type","Prezenční")),
                                     key="edit_study_type")
        cohorts       = ["1. Bc.","2. Bc.","3. Bc.","1. Mgr.","2. Mgr."]
        cohort        = st.selectbox("Ročník", cohorts,
                                     index=cohorts.index(student.get("cohort",cohorts[0])),
                                     key="edit_cohort")
        graduated     = st.checkbox("Absolvent", value=student.get("is_graduated", False), key="edit_graduated")

        if st.form_submit_button("Uložit změny"):
            updated = deepcopy(student)
            updated.update({
                "hodnost":       hodnost,
                "first_name":    first_name,
                "last_name":     last_name,
                "date_of_birth": date_of_birth.strftime("%Y-%m-%d"),
                "address":       address,
                "phone":         phone,
                "email":         email,
                "id_op":         id_op,
                "id_sp":         id_sp,
                "note":          note,
                "study_type":    study_type,
                "cohort":        cohort,
                "is_graduated":  graduated
            })
            save_students(updated)
            st.success("Student upraven!")
            st.experimental_rerun()

    st.markdown("## Smazání studenta")
    if st.checkbox("Opravdu smazat tohoto studenta?", key="confirm_delete"):
        if st.button("Smazat studenta", key="delete_student"):
            delete_student(student.get("id_op"))
            st.success("Student smazán!")
            st.experimental_rerun()

def run_graduates():
    cols = st.columns([8, 1])
    cols[0].header("Absolventi")
    if cols[1].button("Aktualizovat", key="update_grads"):
        st.experimental_rerun()

    students = load_students()
    grads = [s for s in students if s.get("is_graduated", False)]
    if not grads:
        st.info("Žádní absolventi nejsou evidováni.")
        return

    df = pd.DataFrame(grads)
    df = df.drop(columns=["id","subjects","is_graduated"], errors="ignore")
    st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    pass
