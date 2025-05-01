import streamlit as st
import pandas as pd
from supabase import create_client, Client
import datetime
from copy import deepcopy
from io import BytesIO
from streamlit.runtime.scriptrunner import RerunException, RerunData

# Inicializace Supabase klienta
url = st.secrets["supabase"]["supabase_url"]
key = st.secrets["supabase"]["supabase_key"]
supabase: Client = create_client(url, key)

def load_students():
    try:
        resp = supabase.table("students").select("*").execute()
        return resp.data or []
    except Exception as e:
        st.error(f"Chyba při načítání studentů: {e}")
        return []

def run_add_student():
    st.header("Přidat nového studenta")
    with st.form("add_student_form"):
        first    = st.text_input("Jméno")
        last     = st.text_input("Příjmení")
        dob      = st.date_input("Datum narození", min_value=datetime.date(1960,1,1))
        addr     = st.text_input("Bydliště")
        phone    = st.text_input("Telefon")
        email    = st.text_input("Email")
        id_op    = st.text_input("ID-OP")
        id_sp    = st.text_input("ID-SP")
        note     = st.text_area("Poznámka")
        study    = st.selectbox("Typ studia", ["Prezenční","Kombinované"])
        cohort   = st.selectbox("Ročník", ["1. Bc.","2. Bc.","3. Bc.","1. Mgr.","2. Mgr."])
        graduated = st.checkbox("Absolvent")
        if graduated:
            cohort = "Absolvent"
        if st.form_submit_button("Přidat studenta"):
            new_student = {
                "first_name":    first,
                "last_name":     last,
                "date_of_birth": dob.strftime("%Y-%m-%d"),
                "address":       addr,
                "phone":         phone,
                "email":         email,
                "id_op":         id_op,
                "id_sp":         id_sp,
                "note":          note,
                "study_type":    study,
                "cohort":        cohort,
                "is_graduated":  graduated
            }
            try:
                supabase.table("students").insert(new_student).execute()
                st.success("Nový student přidán!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Chyba při přidávání: {e}")

def run_edit_student():
    cols = st.columns([8, 1])
    cols[0].header("Editace studenta")
    if cols[1].button("Aktualizovat", key="update_edit"):
        raise RerunException(RerunData(st.experimental_get_query_params()))

    students = load_students()
    if not students:
        st.info("Žádní studenti nejsou k dispozici ke změně.")
        return

    cohort_map = {
        "Všichni":      None,
        "První ročník": "1. Bc.",
        "Druhý ročník": "2. Bc.",
        "Třetí ročník": "3. Bc.",
        "Čtvrtý ročník":"1. Mgr.",
        "Pátý ročník":  "2. Mgr."
    }
    choice = st.selectbox("Filtrovat ročník", list(cohort_map.keys()), key="filter_cohort")
    if cohort_map[choice]:
        filtered = [s for s in students if s.get("cohort") == cohort_map[choice]]
    else:
        filtered = [s for s in students if s.get("cohort") != "Absolvent"]

    # Tabulka náhledu
    df = pd.DataFrame(filtered)
    df = df.drop(columns=["id", "subjects", "is_graduated"], errors="ignore")
    order = {"1. Bc.":0, "2. Bc.":1, "3. Bc.":2, "1. Mgr.":3, "2. Mgr.":4}
    df["__order"] = df["cohort"].map(order).fillna(len(order))
    df = df.sort_values(["__order", "last_name", "first_name"])
    df = df.drop(columns="__order")
    st.dataframe(df, use_container_width=True)

    if st.button("Export do Excelu", key="export_edit"):
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Studenti")
        st.download_button(
            "Stáhnout Excel",
            buf.getvalue(),
            file_name="Editace_studenti.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_edit"
        )

    idx = st.selectbox(
        "Vyberte studenta ke změně",
        options=list(range(len(filtered))),
        format_func=lambda i: f"{filtered[i]['first_name']} {filtered[i]['last_name']} ({filtered[i]['cohort']})",
        key="select_student_edit"
    )
    student = deepcopy(filtered[idx])

    with st.form("edit_student_form"):
        new_hodnost = st.selectbox(
            "Hodnost",
            ["--","svob.","des.","čet.","rtn. Bc.","rtm. Bc."],
            index=["--","svob.","des.","čet.","rtn. Bc.","rtm. Bc."].index(student.get("hodnost","--")),
            key="edit_hodnost"
        )
        new_first = st.text_input("Jméno", value=student.get("first_name",""), key="edit_first_name")
        new_last  = st.text_input("Příjmení", value=student.get("last_name",""), key="edit_last_name")
        dob_def   = datetime.datetime.strptime(student.get("date_of_birth","1970-01-01"), "%Y-%m-%d")
        new_dob   = st.date_input("Datum narození", value=dob_def, min_value=datetime.date(1960,1,1), key="edit_dob")
        new_addr  = st.text_input("Bydliště", value=student.get("address",""), key="edit_address")
        new_phone = st.text_input("Telefon", value=student.get("phone",""), key="edit_phone")
        new_email = st.text_input("Email", value=student.get("email",""), key="edit_email")
        new_id_op = st.text_input("ID-OP", value=student.get("id_op",""), key="edit_id_op")
        new_id_sp = st.text_input("ID-SP", value=student.get("id_sp",""), key="edit_id_sp")
        new_note  = st.text_area("Poznámka", value=student.get("note",""), key="edit_note")
        new_type  = st.selectbox(
            "Typ studia",
            ["Prezenční","Kombinované"],
            index=["Prezenční","Kombinované"].index(student.get("study_type","Prezenční")),
            key="edit_study_type"
        )
        cohorts   = ["1. Bc.","2. Bc.","3. Bc.","1. Mgr.","2. Mgr.","Absolvent"]
        new_cohort= st.selectbox(
            "Ročník",
            cohorts,
            index=cohorts.index(student.get("cohort", cohorts[0])),
            key="edit_cohort"
        )
        graduated = st.checkbox("Absolvent", value=student.get("is_graduated", False), key="edit_graduated")

        # Pokud je označen jako absolvent, přepíšeme ročník
        if graduated:
            new_cohort = "Absolvent"

        if st.form_submit_button("Uložit změny"):
            updated = deepcopy(student)
            updated.update({
                "hodnost":        new_hodnost,
                "first_name":     new_first,
                "last_name":      new_last,
                "date_of_birth":  new_dob.strftime("%Y-%m-%d"),
                "address":        new_addr,
                "phone":          new_phone,
                "email":          new_email,
                "id_op":          new_id_op,
                "id_sp":          new_id_sp,
                "note":           new_note,
                "study_type":     new_type,
                "cohort":         new_cohort,
                "is_graduated":   graduated
            })
            try:
                supabase.table("students").update(updated).eq("id", student["id"]).execute()
                st.success("Změny uloženy!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Chyba při ukládání změn: {e}")

def run_graduates():
    cols = st.columns([8, 1])
    cols[0].header("Absolventi")
    if cols[1].button("Aktualizovat", key="update_grads"):
        raise RerunException(RerunData(st.experimental_get_query_params()))

    students = load_students()
    grads = [s for s in students if s.get("is_graduated", False)]
    if not grads:
        st.info("Žádní absolventi nejsou evidováni.")
        return

    df = pd.DataFrame(grads)
    df = df.drop(columns=["id","subjects","is_graduated"], errors="ignore")
    st.dataframe(df, use_container_width=True)
