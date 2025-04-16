import streamlit as st
import pandas as pd
import datetime
from copy import deepcopy
from supabase import create_client, Client

st.markdown("""
<style>
.stTextInput>div>div>input {
    max-width: 150px;
}
</style>
""", unsafe_allow_html=True)

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

def save_student_record(student):
    try:
        response = supabase.table("students").update(student).eq("id_op", student["id_op"]).execute()
        return response.data
    except Exception as e:
        st.error("Chyba při ukládání: " + str(e))
        return None

default_structure_3Bc = {
    "zimni": {
        "Základy STP-III": {
            "Zápočet": {"completed": False, "teacher": ""},
            "Zkouška": {"completed": False, "grade": "", "teacher": ""}
        },
        "Speciální TP-III": {
            "Kurz BZ-III": {"completed": False, "teacher": ""},
            "Kurz PSL-I": {"completed": False, "teacher": ""},
            "Zápočet": {"completed": False, "grade": "", "teacher": ""}
        }
    },
    "letni": {
        "Teorie a didaktika AČR-III": {
            "Zápočet": {"completed": False, "teacher": ""},
            "Zkouška": {"completed": False, "grade": "", "teacher": ""}
        }
    }
}

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
