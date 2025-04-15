import streamlit as st
import pandas as pd
import json, os, datetime
from copy import deepcopy

# CSS pro omezení šířky vstupních polí
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

default_structure_2Bc = {
    "zimni": {
        "Základy STP-II": {
            "Vojenské lezení": {"completed": False, "teacher": ""},
            "Boj zblízka": {"completed": False, "teacher": ""},
            "Teoretický test": {"completed": False, "teacher": ""},
            "Zápočet": {"completed": False, "teacher": ""}
        }
    },
    "letni": {
        "Teorie a didaktika AČR-II": {"completed": False, "teacher": ""},
        "Speciální TP-II": {
            "Kurz BZ-II": {"completed": False, "teacher": ""},
            "Kurz VL-II": {"completed": False, "teacher": ""},
            "Kurz VPL-I": {"completed": False, "teacher": ""},
            "Kurz ZP-I": {"completed": False, "teacher": ""},
            "Zápočet": {"completed": False, "teacher": ""}
        }
    }
}

COHORT = "2. Bc."
DISPLAY_NAME = "Druhý ročník (2. Bc.)"

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
        current_student["subjects"] = deepcopy(default_structure_2Bc)
    else:
        for sem in default_structure_2Bc:
            current_student["subjects"].setdefault(sem, {})
            for subj, details in default_structure_2Bc[sem].items():
                current_student["subjects"][sem].setdefault(subj, deepcopy(details))
    
    st.markdown("## Předmětové hodnocení")

    # Rozložení do dvou sloupců: levý pro Zimní semestr a pravý pro Letní semestr
    col_left, col_right = st.columns(2)

    ## Levý sloupec – Zimní semestr
    with col_left:
        st.subheader("Zimní semestr")
        st.markdown("#### Základy STP-II")
        with st.expander("Detail hodnocení", expanded=True):
            subject_list = ["Vojenské lezení", "Boj zblízka", "Teoretický test", "Zápočet"]
            for subj in subject_list:
                col1, col2 = st.columns([0.3, 0.3])
                with col1:
                    zim_chk = st.checkbox(subj, value=current_student["subjects"]["zimni"]["Základy STP-II"].get(subj, {}).get("completed", False),
                                          key="2Bc_zim_STP2_" + subj)
                with col2:
                    zim_teacher = st.text_input("Učitel, který zapsal", value=current_student["subjects"]["zimni"]["Základy STP-II"].get(subj, {}).get("teacher", ""),
                                                 key="2Bc_zim_STP2_" + subj + "_teacher", max_chars=10)
                current_student["subjects"]["zimni"]["Základy STP-II"][subj] = {"completed": zim_chk, "teacher": zim_teacher}
            cond_zim = all(current_student["subjects"]["zimni"]["Základy STP-II"][s]["completed"] for s in subject_list)
            st.markdown("Splněno: **" + ("ANO" if cond_zim else "NE") + "**")

    ## Pravý sloupec – Letní semestr
    with col_right:
        st.subheader("Letní semestr")
        st.markdown("### Teorie a didaktika AČR-II")
        with st.expander("Detail hodnocení", expanded=True):
            col1, col2 = st.columns([0.3, 0.3])
            with col1:
                let_tacr2_chk = st.checkbox("Zápočet", value=current_student["subjects"]["letni"].get("Teorie a didaktika AČR-II", {}).get("completed", False),
                                            key="2Bc_let_TACR2_Zapo")
            with col2:
                let_tacr2_teacher = st.text_input("Učitel, který zapsal", value=current_student["subjects"]["letni"].get("Teorie a didaktika AČR-II", {}).get("teacher", ""),
                                                  key="2Bc_let_TACR2_Zapo_teacher", max_chars=10)
            current_student["subjects"]["letni"]["Teorie a didaktika AČR-II"] = {"completed": let_tacr2_chk, "teacher": let_tacr2_teacher}
            st.markdown("Splněno: **" + ("ANO" if let_tacr2_chk else "NE") + "**")
        
        st.markdown("### Speciální TP-II")
        with st.expander("Detail hodnocení", expanded=True):
            subject_list2 = ["Kurz BZ-II", "Kurz VL-II", "Kurz VPL-I", "Kurz ZP-I", "Zápočet"]
            for subj in subject_list2:
                col1, col2 = st.columns([0.3, 0.3])
                with col1:
                    let_spt2_chk = st.checkbox(subj, value=current_student["subjects"]["letni"]["Speciální TP-II"].get(subj, {}).get("completed", False),
                                               key="2Bc_let_SPT2_" + subj)
                with col2:
                    let_spt2_teacher = st.text_input("Učitel, který zapsal", value=current_student["subjects"]["letni"]["Speciální TP-II"].get(subj, {}).get("teacher", ""),
                                                      key="2Bc_let_SPT2_" + subj + "_teacher", max_chars=10)
                current_student["subjects"]["letni"]["Speciální TP-II"][subj] = {"completed": let_spt2_chk, "teacher": let_spt2_teacher}
            cond_spt2 = all(current_student["subjects"]["letni"]["Speciální TP-II"][s]["completed"] for s in subject_list2)
            st.markdown("Splněno: **" + ("ANO" if cond_spt2 else "NE") + "**")
    
    if st.button("Uložit hodnocení", key="save_2Bc_" + str(current_student.get("id_op", ""))):
        students_list = load_students()
        for i, s in enumerate(students_list):
            if s.get("id_op") == current_student.get("id_op"):
                students_list[i] = current_student
                break
        save_students(students_list)
        st.success("Hodnocení uloženo!")
        try:
            st.experimental_rerun()
        except AttributeError:
            pass

if __name__ == "__main__":
    run_student()
