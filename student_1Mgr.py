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

# ===== KONFIGURACE SUPABASE =====
from supabase import create_client, Client
# Načtení hodnot ze st.secrets
SUPABASE_URL = st.secrets["supabase"]["supabase_url"]
SUPABASE_KEY = st.secrets["supabase"]["supabase_key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# =================================

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

default_structure_1Mgr = {
    "zimni": {
        "Teorie a didaktika AČR-1": {"completed": False, "teacher": ""},
        "Základy STP-1": {
            "Vojenské lezení": {"completed": False, "teacher": ""},
            "Boj zblízka": {"completed": False, "teacher": ""},
            "Teoretický test": {"completed": False, "teacher": ""},
            "Zápočet": {"completed": False, "teacher": ""}
        }
    },
    "letni": {
        "Teorie a didaktika AČR-2": {"completed": False, "teacher": ""},
        "Základy STP-2": {
            "Vojenské lezení": {"completed": False, "teacher": ""},
            "Boj zblízka": {"completed": False, "teacher": ""},
            "Teoretický test": {"completed": False, "teacher": ""},
            "Zápočet": {"completed": False, "teacher": ""},
            "Zkouška": {"completed": False, "grade": "", "teacher": ""}
        },
        "Speciální TP-1": {
            "STP-II": {"completed": False, "teacher": ""},
            "VL-III": {"completed": False, "teacher": ""},
            "VPL-II": {"completed": False, "teacher": ""},
            "ZP-II": {"completed": False, "teacher": ""},
            "Zápočet": {"completed": False, "teacher": ""}
        }
    }
}

COHORT = "1. Mgr."
DISPLAY_NAME = "Čtvrtý ročník (1. Mgr.)"

def run_student():
    st.title("Studenti - " + DISPLAY_NAME)
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
        current_student["subjects"] = deepcopy(default_structure_1Mgr)
    else:
        for sem in default_structure_1Mgr:
            current_student["subjects"].setdefault(sem, {})
            for subj, details in default_structure_1Mgr[sem].items():
                current_student["subjects"][sem].setdefault(subj, deepcopy(details))
    st.markdown("## Předmětové hodnocení")
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Zimní semestr")
        st.markdown("#### Teorie a didaktika AČR-1")
        with st.expander("Detail hodnocení", expanded=True):
            col1, col2 = st.columns([0.3, 0.3])
            with col1:
                zim_chk = st.checkbox("Zápočet", value=current_student["subjects"]["zimni"]["Teorie a didaktika AČR-1"].get("completed", False), key="1Mgr_zim_TACR1_chk")
            with col2:
                zim_teacher = st.text_input("Učitel, který zapsal", value=current_student["subjects"]["zimni"]["Teorie a didaktika AČR-1"].get("teacher", ""), key="1Mgr_zim_TACR1_teacher", max_chars=10)
            current_student["subjects"]["zimni"]["Teorie a didaktika AČR-1"] = {"completed": zim_chk, "teacher": zim_teacher}
            st.markdown("Splněno: **" + ("ANO" if zim_chk else "NE") + "**")
    with col_right:
        st.subheader("Letní semestr")
        st.markdown("#### Teorie a didaktika AČR-2")
        with st.expander("Detail hodnocení", expanded=True):
            col1, col2 = st.columns([0.3, 0.3])
            with col1:
                let_TACR2_chk = st.checkbox("Zápočet", value=current_student["subjects"]["letni"]["Teorie a didaktika AČR-2"].get("completed", False), key="1Mgr_let_TACR2_Zápočet")
            with col2:
                let_TACR2_teacher = st.text_input("Učitel, který zapsal", value=current_student["subjects"]["letni"]["Teorie a didaktika AČR-2"].get("teacher", ""), key="1Mgr_let_TACR2_Zápočet_teacher", max_chars=10)
            current_student["subjects"]["letni"]["Teorie a didaktika AČR-2"] = {"completed": let_TACR2_chk, "teacher": let_TACR2_teacher}
            st.markdown("Splněno: **" + ("ANO" if let_TACR2_chk else "NE") + "**")
        st.markdown("#### Základy STP-2")
        with st.expander("Detail hodnocení", expanded=True):
            for subj in ["Vojenské lezení", "Boj zblízka", "Teoretický test", "Zápočet"]:
                col1, col2 = st.columns([0.3, 0.3])
                with col1:
                    let_stp2_chk = st.checkbox(subj, value=current_student["subjects"]["letni"]["Základy STP-2"].get(subj, {}).get("completed", False), key="1Mgr_STP2_" + subj)
                with col2:
                    let_stp2_teacher = st.text_input("Učitel, který zapsal", value=current_student["subjects"]["letni"]["Základy STP-2"].get(subj, {}).get("teacher", ""), key="1Mgr_STP2_" + subj + "_teacher", max_chars=10)
                current_student["subjects"]["letni"]["Základy STP-2"][subj] = {"completed": let_stp2_chk, "teacher": let_stp2_teacher}
            zk_cols = st.columns([0.25, 0.1, 0.15])
            with zk_cols[0]:
                let_stp2_zk_chk = st.checkbox("Zkouška", value=current_student["subjects"]["letni"]["Základy STP-2"].get("Zkouška", {}).get("completed", False), key="1Mgr_STP2_Zkouška")
            with zk_cols[1]:
                let_stp2_zk_grade = st.text_input("Známka", value=current_student["subjects"]["letni"]["Základy STP-2"].get("Zkouška", {}).get("grade", ""), key="1Mgr_STP2_Zkouška_grade", max_chars=3)
            with zk_cols[2]:
                let_stp2_zk_teacher = st.text_input("Učitel, který zapsal", value=current_student["subjects"]["letni"]["Základy STP-2"].get("Zkouška", {}).get("teacher", ""), key="1Mgr_STP2_Zkouška_teacher", max_chars=10)
            current_student["subjects"]["letni"]["Základy STP-2"]["Zkouška"] = {"completed": let_stp2_zk_chk, "grade": let_stp2_zk_grade, "teacher": let_stp2_zk_teacher}
            cond_stp2 = all(current_student["subjects"]["letni"]["Základy STP-2"][s]["completed"] for s in ["Vojenské lezení", "Boj zblízka", "Teoretický test", "Zápočet"]) \
                       and let_stp2_zk_chk and let_stp2_zk_grade.strip() not in ["", "4"]
            st.markdown("Splněno: **" + ("ANO" if cond_stp2 else "NE") + "**")
        st.markdown("#### Speciální TP-1")
        with st.expander("Detail hodnocení", expanded=True):
            for subj in ["STP-II", "VL-III", "VPL-II", "ZP-II", "Zápočet"]:
                col1, col2 = st.columns([0.3, 0.3])
                with col1:
                    let_spt1_chk = st.checkbox(subj, value=current_student["subjects"]["letni"]["Speciální TP-1"].get(subj, {}).get("completed", False), key="1Mgr_SPT1_" + subj)
                with col2:
                    let_spt1_teacher = st.text_input("Učitel, který zapsal", value=current_student["subjects"]["letni"]["Speciální TP-1"].get(subj, {}).get("teacher", ""), key="1Mgr_SPT1_" + subj + "_teacher", max_chars=10)
                current_student["subjects"]["letni"]["Speciální TP-1"][subj] = {"completed": let_spt1_chk, "teacher": let_spt1_teacher}
            cond_spt1 = all(current_student["subjects"]["letni"]["Speciální TP-1"][s]["completed"] for s in ["STP-II", "VL-III", "VPL-II", "ZP-II", "Zápočet"])
            st.markdown("Splněno: **" + ("ANO" if cond_spt1 else "NE") + "**")
    if st.button("Uložit hodnocení", key="save_1Mgr_" + str(current_student.get("id_op", ""))):
        save_student_record(current_student)
        st.success("Předmětová hodnocení uložena!")
        try:
            st.experimental_rerun()
        except AttributeError:
            pass

if __name__ == "__main__":
    run_student()
