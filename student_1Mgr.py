import streamlit as st
import pandas as pd
import json, os, datetime
from copy import deepcopy

# CSS – omezení šířky vstupních polí
st.markdown("""
<style>
.stTextInput>div>div>input {
    max-width: 150px;
}
</style>
""", unsafe_allow_html=True)

DATA_FILE = "students.json"

def load_students():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return []

def save_students(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Výchozí struktura pro 1. Mgr.
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
            # U předmětů s instruktorským hodnocením budeme ukládat instruktorskou evaluaci do samostatného klíče
            "VPL-II": {"completed": False, "teacher": ""},
            "ZP-II": {"completed": False, "teacher": ""},
            "Zápočet": {"completed": False, "teacher": ""}
        }
    }
}

COHORT = "1. Mgr."
DISPLAY_NAME = "Čtvrtý ročník (1. Mgr.)"

def run_student():
    st.title("Systém studentů - " + DISPLAY_NAME)
    students = load_students()
    cohort_students = [s for s in students if s.get("cohort") == COHORT]
    if not cohort_students:
        st.info("Žádní studenti z tohoto ročníku nejsou zaregistrováni.")
        return

    df = pd.DataFrame(cohort_students)
    st.dataframe(df, use_container_width=True)

    selected_idx = st.selectbox(
        "Vyberte studenta",
        options=df.index,
        format_func=lambda i: f"{df.loc[i, 'hodnost']} {df.loc[i, 'first_name']} {df.loc[i, 'last_name']}"
    )
    current_student = deepcopy(cohort_students[selected_idx])
    if "subjects" not in current_student:
        current_student["subjects"] = deepcopy(default_structure_1Mgr)
    else:
        for sem in default_structure_1Mgr:
            current_student["subjects"].setdefault(sem, {})
            for subj, details in default_structure_1Mgr[sem].items():
                current_student["subjects"][sem].setdefault(subj, deepcopy(details))

    st.markdown("## Předmětové hodnocení")

    # Rozdělení do dvou sloupců: levý = Zimní semestr, pravý = Letní semestr.
    col_left, col_right = st.columns(2)

    ### Levý sloupec – Zimní semestr
    with col_left:
        st.subheader("Zimní semestr")
        st.markdown("#### Teorie a didaktika AČR-1")
        with st.expander("Detail hodnocení", expanded=True):
            col1, col2 = st.columns([0.3, 0.3])
            with col1:
                zim_TACR1_chk = st.checkbox("Zápočet", value=current_student["subjects"]["zimni"]["Teorie a didaktika AČR-1"].get("completed", False), key="1Mgr_zim_TACR1_chk")
            with col2:
                zim_TACR1_teacher = st.text_input("Učitel, který zapsal", value=current_student["subjects"]["zimni"]["Teorie a didaktika AČR-1"].get("teacher", ""), key="1Mgr_zim_TACR1_teacher", max_chars=10)
            current_student["subjects"]["zimni"]["Teorie a didaktika AČR-1"] = {"completed": zim_TACR1_chk, "teacher": zim_TACR1_teacher}
            st.markdown("Splněno: **" + ("ANO" if zim_TACR1_chk else "NE") + "**")
        
        st.markdown("#### Základy STP-1")
        with st.expander("Detail hodnocení", expanded=True):
            for subj in ["Vojenské lezení", "Boj zblízka", "Teoretický test", "Zápočet"]:
                col1, col2 = st.columns([0.3, 0.3])
                with col1:
                    zim_STP1_chk = st.checkbox(subj, value=current_student["subjects"]["zimni"]["Základy STP-1"].get(subj, {}).get("completed", False), key="1Mgr_STP1_" + subj)
                with col2:
                    zim_STP1_teacher = st.text_input("Učitel, který zapsal", value=current_student["subjects"]["zimni"]["Základy STP-1"].get(subj, {}).get("teacher", ""), key="1Mgr_STP1_" + subj + "_teacher", max_chars=10)
                current_student["subjects"]["zimni"]["Základy STP-1"][subj] = {"completed": zim_STP1_chk, "teacher": zim_STP1_teacher}
            cond_STP1 = all(current_student["subjects"]["zimni"]["Základy STP-1"][s]["completed"] for s in ["Vojenské lezení", "Boj zblízka", "Teoretický test", "Zápočet"])
            st.markdown("Splněno: **" + ("ANO" if cond_STP1 else "NE") + "**")

    ### Pravý sloupec – Letní semestr
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
                    let_STP2_chk = st.checkbox(subj, value=current_student["subjects"]["letni"]["Základy STP-2"].get(subj, {}).get("completed", False), key="1Mgr_STP2_" + subj)
                with col2:
                    let_STP2_teacher = st.text_input("Učitel, který zapsal", value=current_student["subjects"]["letni"]["Základy STP-2"].get(subj, {}).get("teacher", ""), key="1Mgr_STP2_" + subj + "_teacher", max_chars=10)
                current_student["subjects"]["letni"]["Základy STP-2"][subj] = {"completed": let_STP2_chk, "teacher": let_STP2_teacher}
            # Řádek pro Zkouška – vše na jednom řádku pomocí 3 sloupců
            zk_cols = st.columns([0.25, 0.1, 0.15])
            with zk_cols[0]:
                let_STP2_Zk_chk = st.checkbox("Zkouška", value=current_student["subjects"]["letni"]["Základy STP-2"].get("Zkouška", {}).get("completed", False), key="1Mgr_STP2_Zkouška")
            with zk_cols[1]:
                let_STP2_Zk_grade = st.text_input("Známka", value=current_student["subjects"]["letni"]["Základy STP-2"].get("Zkouška", {}).get("grade", ""), key="1Mgr_STP2_Zkouška_grade", max_chars=3)
            with zk_cols[2]:
                let_STP2_Zk_teacher = st.text_input("Učitel, který zapsal", value=current_student["subjects"]["letni"]["Základy STP-2"].get("Zkouška", {}).get("teacher", ""), key="1Mgr_STP2_Zkouška_teacher", max_chars=10)
            current_student["subjects"]["letni"]["Základy STP-2"]["Zkouška"] = {"completed": let_STP2_Zk_chk, "grade": let_STP2_Zk_grade, "teacher": let_STP2_Zk_teacher}
            cond_STP2 = all(current_student["subjects"]["letni"]["Základy STP-2"][s]["completed"] for s in ["Vojenské lezení", "Boj zblízka", "Teoretický test", "Zápočet"]) \
                       and let_STP2_Zk_chk and let_STP2_Zk_grade.strip() not in ["", "4"]
            st.markdown("Splněno: **" + ("ANO" if cond_STP2 else "NE") + "**")
        
        st.markdown("#### Speciální TP-1")
        with st.expander("Detail hodnocení", expanded=True):
            for subj in ["STP-II", "VL-III", "VPL-II", "ZP-II", "Zápočet"]:
                if subj in ["VPL-II", "ZP-II"]:
                    # Řádek se třemi sloupci: 
                    # 1. checkbox předmětu
                    # 2. checkbox Instruktor
                    # 3. textové pole pro Učitele
                    row = st.columns([0.1, 0.2, 0.3])
                    with row[0]:
                        subj_chk = st.checkbox(subj, value=current_student["subjects"]["letni"]["Speciální TP-1"].get(subj, {}).get("completed", False), key="1Mgr_SPT1_" + subj)
                    with row[1]:
                        instr_chk = st.checkbox("Instruktor", value=current_student["subjects"]["letni"]["Speciální TP-1"].get(subj + " Instruktor", False), key="1Mgr_SPT1_" + subj + "_instruktor")
                    with row[2]:
                        teacher_val = st.text_input("Učitel, který zapsal", value=current_student["subjects"]["letni"]["Speciální TP-1"].get(subj, {}).get("teacher", ""), key="1Mgr_SPT1_" + subj + "_teacher", max_chars=10)
                    current_student["subjects"]["letni"]["Speciální TP-1"][subj] = {"completed": subj_chk, "teacher": teacher_val}
                    current_student["subjects"]["letni"]["Speciální TP-1"][subj + " Instruktor"] = instr_chk
                else:
                    row = st.columns([0.3, 0.3])
                    with row[0]:
                        s_chk = st.checkbox(subj, value=current_student["subjects"]["letni"]["Speciální TP-1"].get(subj, {}).get("completed", False), key="1Mgr_SPT1_" + subj)
                    with row[1]:
                        s_teacher = st.text_input("Učitel, který zapsal", value=current_student["subjects"]["letni"]["Speciální TP-1"].get(subj, {}).get("teacher", ""), key="1Mgr_SPT1_" + subj + "_teacher", max_chars=10)
                    current_student["subjects"]["letni"]["Speciální TP-1"][subj] = {"completed": s_chk, "teacher": s_teacher}
            cond_SPT1 = all(current_student["subjects"]["letni"]["Speciální TP-1"][s]["completed"] for s in ["STP-II", "VL-III", "VPL-II", "ZP-II", "Zápočet"])
            st.markdown("Splněno: **" + ("ANO" if cond_SPT1 else "NE") + "**")
    
    if st.button("Uložit předmětová hodnocení", key="save_1Mgr_" + str(current_student.get("id_op", ""))):
        students_list = load_students()
        for i, s in enumerate(students_list):
            if s.get("id_op") == current_student.get("id_op"):
                students_list[i] = current_student
                break
        save_students(students_list)
        st.success("Předmětová hodnocení uložena!")
        try:
            st.experimental_rerun()
        except AttributeError:
            pass

if __name__ == "__main__":
    run_student()
