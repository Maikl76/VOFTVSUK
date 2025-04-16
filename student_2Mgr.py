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

default_structure_2Mgr = {
    "zimni": {
        "Speciální TP-2": {
            "Kurz BZ-IV": {"completed": False, "instruktor": False, "teacher": ""},
            "Kurz VL-IV": {"completed": False, "instruktor": False, "teacher": ""},
            "Kurz PSL-II": {"completed": False, "instruktor": False, "teacher": ""},
            "Klasifikovaný zápočet": {"completed": False, "grade": "", "teacher": ""},
            "Splněno": {"value": "NE"}
        }
    },
    "letni": {
        "Teorie a didaktika AČR-3": {
            "Zápočet 1": {"completed": False, "teacher": ""},
            "Zkouška": {"completed": False, "grade": "", "teacher": ""},
            "Splněno": {"value": "NE"}
        }
    }
}

COHORT = "2. Mgr."
DISPLAY_NAME = "Pátý ročník (2. Mgr.)"

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
        current_student["subjects"] = deepcopy(default_structure_2Mgr)
    else:
        for sem in default_structure_2Mgr:
            current_student["subjects"].setdefault(sem, {})
            for subj, details in default_structure_2Mgr[sem].items():
                current_student["subjects"][sem].setdefault(subj, deepcopy(details))
    
    st.markdown("## Předmětové hodnocení")
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("Zimní semestr")
        st.markdown("#### Speciální TP-2")
        with st.expander("Detail hodnocení", expanded=True):
            subject_zim = current_student["subjects"]["zimni"]["Speciální TP-2"]
            row1 = st.columns([0.1, 0.2, 0.3])
            with row1[0]:
                bziv_chk = st.checkbox("Kurz BZ-IV", value=subject_zim.get("Kurz BZ-IV", {}).get("completed", False), key="2Mgr_SPT2_BZIV")
            with row1[1]:
                bziv_instr = st.checkbox("Instruktor", value=subject_zim.get("BZ-IV Instruktor", False), key="2Mgr_SPT2_BZIV_instr")
            with row1[2]:
                bziv_teacher = st.text_input("Učitel, který zapsal", value=subject_zim.get("Kurz BZ-IV", {}).get("teacher", ""), key="2Mgr_SPT2_BZIV_teacher", max_chars=10)
            subject_zim["Kurz BZ-IV"] = {"completed": bziv_chk, "teacher": bziv_teacher}
            subject_zim["BZ-IV Instruktor"] = bziv_instr

            row2 = st.columns([0.1, 0.2, 0.3])
            with row2[0]:
                vliv_chk = st.checkbox("Kurz VL-IV", value=subject_zim.get("Kurz VL-IV", {}).get("completed", False), key="2Mgr_SPT2_VLIV")
            with row2[1]:
                vliv_instr = st.checkbox("Instruktor", value=subject_zim.get("VL-IV Instrukor", False), key="2Mgr_SPT2_VLIV_instr")
            with row2[2]:
                vliv_teacher = st.text_input("Učitel, který zapsal", value=subject_zim.get("Kurz VL-IV", {}).get("teacher", ""), key="2Mgr_SPT2_VLIV_teacher", max_chars=10)
            subject_zim["Kurz VL-IV"] = {"completed": vliv_chk, "teacher": vliv_teacher}
            subject_zim["VL-IV Instrukor"] = vliv_instr

            row3 = st.columns([0.1, 0.2, 0.3])
            with row3[0]:
                psl_chk = st.checkbox("Kurz PSL-II", value=subject_zim.get("Kurz PSL-II", {}).get("completed", False), key="2Mgr_SPT2_PSL")
            with row3[1]:
                psl_instr = st.checkbox("Instruktor", value=subject_zim.get("PSL-II Instruktor", False), key="2Mgr_SPT2_PSL_instr")
            with row3[2]:
                psl_teacher = st.text_input("Učitel, který zapsal", value=subject_zim.get("Kurz PSL-II", {}).get("teacher", ""), key="2Mgr_SPT2_PSL_teacher", max_chars=10)
            subject_zim["Kurz PSL-II"] = {"completed": psl_chk, "teacher": psl_teacher}
            subject_zim["PSL-II Instruktor"] = psl_instr

            row4 = st.columns([0.25, 0.1, 0.15])
            with row4[0]:
                klas_zap_chk = st.checkbox("Klasifikovaný zápočet", value=subject_zim.get("Klasifikovaný zápočet", {}).get("completed", False), key="2Mgr_SPT2_klasZapo")
            with row4[1]:
                klas_grade = st.text_input("Známka", value=subject_zim.get("Klasifikovaný zápočet", {}).get("grade", ""), key="2Mgr_SPT2_klasZapo_grade", max_chars=3)
            with row4[2]:
                klas_teacher = st.text_input("Učitel, který zapsal", value=subject_zim.get("Klasifikovaný zápočet", {}).get("teacher", ""), key="2Mgr_SPT2_klasZapo_teacher", max_chars=10)
            subject_zim["Klasifikovaný zápočet"] = {"completed": klas_zap_chk, "grade": klas_grade, "teacher": klas_teacher}
            
            cond_spec = (subject_zim["Kurz BZ-IV"]["completed"] and
                         subject_zim["Kurz VL-IV"]["completed"] and
                         subject_zim["Kurz PSL-II"]["completed"] and
                         subject_zim["Klasifikovaný zápočet"]["completed"])
            st.markdown("Splněno: **" + ("ANO" if cond_spec else "NE") + "**")
            subject_zim["Splněno"] = {"value": "ANO" if cond_spec else "NE"}
    
    with col_right:
        st.subheader("Letní semestr")
        st.markdown("#### Teorie a didaktika AČR-3")
        with st.expander("Detail hodnocení", expanded=True):
            subject_let = current_student["subjects"]["letni"]["Teorie a didaktika AČR-3"]
            row1_let = st.columns([0.3, 0.3])
            with row1_let[0]:
                zap1_chk = st.checkbox("Zápočet", value=subject_let.get("Zápočet 1", {}).get("completed", False), key="2Mgr_TACR3_zap1")
            with row1_let[1]:
                zap1_teacher = st.text_input("Učitel, který zapsal", value=subject_let.get("Zápočet 1", {}).get("teacher", ""), key="2Mgr_TACR3_zap1_teacher", max_chars=10)
            subject_let["Zápočet 1"] = {"completed": zap1_chk, "teacher": zap1_teacher}
    
            row2_let = st.columns([0.25, 0.1, 0.15])
            with row2_let[0]:
                zk_chk = st.checkbox("Zkouška", value=subject_let.get("Zkouška", {}).get("completed", False), key="2Mgr_TACR3_Zkouška")
            with row2_let[1]:
                zk_grade = st.text_input("Známka", value=subject_let.get("Zkouška", {}).get("grade", ""), key="2Mgr_TACR3_Zkouška_grade", max_chars=3)
            with row2_let[2]:
                zk_teacher = st.text_input("Učitel, který zapsal", value=subject_let.get("Zkouška", {}).get("teacher", ""), key="2Mgr_TACR3_Zkouška_teacher", max_chars=10)
            subject_let["Zkouška"] = {"completed": zk_chk, "grade": zk_grade, "teacher": zk_teacher}
    
            cond_let = subject_let["Zápočet 1"]["completed"] and subject_let["Zkouška"]["completed"]
            st.markdown("Splněno: **" + ("ANO" if cond_let else "NE") + "**")
            subject_let["Splněno"] = {"value": "ANO" if cond_let else "NE"}
    
    if st.button("Uložit předmětová hodnocení", key="save_2Mgr_" + str(current_student.get("id_op", ""))):
        save_student_record(current_student)
        st.success("Předmětová hodnocení uložena!")
        try:
            st.experimental_rerun()
        except AttributeError:
            pass

if __name__ == "__main__":
    run_student()
