import streamlit as st
from supabase import create_client, Client
import json, os, datetime
import pandas as pd
from docx import Document
from docx.shared import Pt, Inches
from io import BytesIO
from streamlit_quill import st_quill  # WYSIWYG editor
import csv
from io import StringIO

# --- Přihlašovací formulář (stejné jako dříve) ---
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
col1, col2 = st.columns([1, 6])
with col1:
    st.image("Logo.png", width=50)
with col2:
    st.markdown("<h1 style='margin-bottom: 0;'>Vojenský obor FTVS UK</h1>", unsafe_allow_html=True)

# --- Inicializace Supabase klienta ---
SUPABASE_URL = "https://bgtpylewilzcqfqaoixx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJndHB5bGV3aWx6Y3FmcWFvaXh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ1NzQxNTQsImV4cCI6MjA2MDE1MDE1NH0.6NutsH1g8k0ruhpylqltrWD53HQFy-ZQjcUN-SULktM"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Pomocné funkce ---
def format_table(doc_table, font_size=10):
    doc_table.style = "Table Grid"
    for row in doc_table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(font_size)

# --- Funkce pro práci s vyhodnocením v Supabase ---
def load_evaluations():
    response = supabase.table("evaluations").select("*").execute()
    if response.error:
        st.error("Chyba při načítání vyhodnocení: " + response.error.message)
        return {}
    evaluations = {}
    for row in response.data:
        evaluations[row["key_period"]] = row["eval_data"]
    return evaluations

def save_evaluation(key_period, eval_data):
    # Zkontrolujeme, zda již záznam existuje
    response = supabase.table("evaluations").select("*").eq("key_period", key_period).execute()
    if response.error:
        st.error("Chyba při načítání vyhodnocení: " + response.error.message)
        return
    if len(response.data) == 0:
        insert_resp = supabase.table("evaluations").insert({"key_period": key_period, "eval_data": eval_data}).execute()
        if insert_resp.error:
            st.error("Chyba při ukládání vyhodnocení: " + insert_resp.error.message)
    else:
        update_resp = supabase.table("evaluations").update({"eval_data": eval_data}).eq("key_period", key_period).execute()
        if update_resp.error:
            st.error("Chyba při aktualizaci vyhodnocení: " + update_resp.error.message)

# --- Načtení vyhodnocení z databáze ---
stored_evals = load_evaluations()
if "evaluations" not in st.session_state:
    st.session_state.evaluations = stored_evals

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
}

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
    # Načteme studenty z Supabase
    response = supabase.table("students").select("*").execute()
    if response.error:
        st.error("Chyba při načítání studentů: " + response.error.message)
        return
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

# --- Import modulů pro studenta ---
import student   # Tento modul slouží pro přidání a editaci studentů
import student_1Bc, student_2Bc, student_3Bc, student_1Mgr, student_2Mgr

with st.sidebar.expander("Nastavení položek vyhodnocení"):
    selected_items = {}
    for item in items:
        st.markdown(f"#### {item}")
        include = st.checkbox("Zobrazit", key=f"include_{item}")
        finished = st.checkbox("Hotovo", key=f"finished_{item}")
        if finished:
            st.markdown(f"<span style='color: green;'>{item} - hotovo</span>", unsafe_allow_html=True)
        selected_items[item] = include
    st.markdown("---")
    include_celkovy = st.checkbox("Zobrazit celkové vyhodnocení", key="include_celkovy")

tabs = st.tabs(["Vyhodnocení VO FTVS UK", "Historie vyhodnocení", "DPP", "PR-I", "ZSC", "Student"])

with tabs[0]:
    st.header("Vyhodnocení VO FTVS UK")
    current_year = st.number_input("Rok", min_value=2000, max_value=2100,
                                   value=datetime.datetime.now().year, step=1)
    selected_period = st.selectbox("Vyberte období", list(evaluation_periods.keys()))
    period_range = evaluation_periods[selected_period]
    st.write(f"Zvolená doba: {selected_period} ({period_range[0]} až {period_range[1]})")
    key_period = f"{current_year}_{selected_period}"
    saved_eval = st.session_state.evaluations.get(key_period, {})
    if st.session_state.get("include_celkovy", False):
        items_to_eval = items
    else:
        items_to_eval = [item for item in items if st.session_state.get(f"include_{item}", False)]
    if not items_to_eval:
        st.info("Vyberte prosím v postranním panelu alespoň jednu položku, kterou chcete vyhodnotit.")
    else:
        st.markdown("### Vyplňte nebo upravte již uložené vyhodnocení (pokud existuje)")
        eval_data = {}
        for item in items_to_eval:
            if item == "Souhrnný přehled APVVP":
                st.markdown("##### Nahrajte excel soubor s přehledem APVVP:")
                if item in saved_eval and saved_eval[item].get("table"):
                    st.info("Nahraný soubor byl již uložen:")
                    st.table(saved_eval[item]["table"])
                    if st.button("Smazat nahraný soubor", key="delete_apvvp"):
                        saved_eval[item]["table"] = None
                        st.session_state.evaluations[key_period] = saved_eval
                        save_evaluation(key_period, saved_eval)
                        st.success("Nahraný soubor byl smazán.")
                uploaded_file = st.file_uploader("Vyberte soubor", type=["xlsx"], key="upload_apvvp")
                table_data = None
                if uploaded_file is not None:
                    try:
                        df_tmp = pd.read_excel(uploaded_file)
                        df_tmp = df_tmp.fillna("").astype(str)
                        st.dataframe(df_tmp)
                        table_data = [list(df_tmp.columns)] + df_tmp.values.tolist()
                    except Exception as e:
                        st.error("Chyba při načítání excel souboru.")
                eval_data[item] = {"table": table_data if table_data is not None else saved_eval.get(item, {}).get("table")}
            elif item == "Ekonomika":
                st.markdown("##### Nahrajte excel soubor pro Ekonomiku:")
                if item in saved_eval and saved_eval[item].get("table"):
                    st.info("Nahraný soubor byl již uložen:")
                    st.table(saved_eval[item]["table"])
                uploaded_file = st.file_uploader("Vyberte soubor", type=["xlsx"], key="upload_ekonomika")
                table_data = None
                if uploaded_file is not None:
                    try:
                        df_tmp = pd.read_excel(uploaded_file)
                        df_tmp = df_tmp.fillna("").astype(str)
                        st.dataframe(df_tmp)
                        table_data = [list(df_tmp.columns)] + df_tmp.values.tolist()
                    except Exception as e:
                        st.error("Chyba při načítání excel souboru pro Ekonomiku.")
                default_text = saved_eval.get(item, {}).get("text", "")
                st.markdown("Vyhodnocení pro Ekonomiku:")
                text = st_quill(key=f"eval_{current_year}_{selected_period}_{item}", value=default_text)
                default_finished = saved_eval.get(item, {}).get("finished", False)
                finished_flag = st.checkbox("Hotovo", key=f"finished_form_{current_year}_{selected_period}_{item}", value=default_finished)
                eval_data[item] = {"table": table_data if table_data is not None else saved_eval.get(item, {}).get("table"),
                                    "text": text, "finished": finished_flag}
            else:
                default_text = saved_eval.get(item, {}).get("text", "")
                st.markdown(f"Vyhodnocení pro {item}:")
                text = st_quill(key=f"eval_{current_year}_{selected_period}_{item}", value=default_text)
                default_finished = saved_eval.get(item, {}).get("finished", False)
                finished_flag = st.checkbox("Hotovo", key=f"finished_form_{current_year}_{selected_period}_{item}", value=default_finished)
                eval_data[item] = {"text": text, "finished": finished_flag}
        if st.button("Uložit vyhodnocení", key="save_eval"):
            st.session_state.evaluations[key_period] = eval_data
            save_evaluation(key_period, eval_data)
            st.success("Vyhodnocení uloženo!")
        
        st.subheader("Generování dokumentů")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Generovat Word dokument", key="gen_word"):
                try:
                    intro_path = "upload/Úvodní strana vyhodnocení.docx"
                    if os.path.exists(intro_path):
                        intro_doc = Document(intro_path)
                    else:
                        st.error("Soubor Úvodní strana vyhodnocení.docx nebyl nalezen v adresáři upload.")
                        intro_doc = Document()
                    
                    eval_doc = Document()
                    eval_doc.add_heading(f"Vyhodnocení za: {selected_period} roku {current_year}", level=0)
                    eval_doc.add_page_break()
                    
                    # Výběr položek podle nastavení
                    if st.session_state.get("include_celkovy", False):
                        doc_items = items
                    else:
                        doc_items = items_to_eval
                                        
                    for idx, item in enumerate(doc_items):
                        data = st.session_state.evaluations.get(key_period, {}).get(item, {})
                        if idx < 6:
                            if item == "VŠ vzdělávání":
                                vs_text = (
                                    "2. Vyhodnocení plnění dílčích úkolů „Ročního plánu VO FTVS UK na rok 202X“ dle stanovené metodiky měření\n\n"
                                    "Název cíle 3. úrovně \n"
                                    "120302 \tZajistit optimální podmínky pro vzdělávání a permanentní rozvoj znalostí a dovedností personálu v souladu s potřebami rezortu MO\n\n"
                                    "Opatření a úkoly k dosažení cíle \n"
                                    "Opatření \n"
                                    "12030201 Vysokoškolské vzdělávání personálu pro potřeby rezortu MO \n"
                                    "Úkol \n"
                                    "12030201 Komplexně realizovat studijní a pedagogickou činnost v akreditovaných programech na VO FTVS UK\n"
                                    "Dílčí úkol \n"
                                    "1203020102 Komplexně realizovat studijní a pedagogickou činnost v bakalářském a navazujícím magisterském studijním programu na VO \n"
                                    "FTVS UK\n"
                                    "Dílčí úkol \n"
                                    "120302010201 Harmonogram akademického roku 2023/2024\n"
                                    "Opatření\n"
                                    "120302010202 Zabezpečit vojenskou činnost a chod VO FTVS UK\n\n"
                                    "V rámci dílčího úkolu plnit tyto hlavní úkoly:\n\n"
                                    "2.1 Zabezpečit vysokoškolské vzdělávání"
                                )
                                eval_doc.add_paragraph(vs_text)
                            custom_heading = custom_headings.get(item, item)
                            eval_doc.add_heading(custom_heading, level=2)
                        elif idx == 6:
                            eval_doc.add_heading("2.2 Zabezpečit činnost VO FTVS UK", level=2)
                            eval_doc.add_heading("Dílčí úkol", level=3)
                            eval_doc.add_paragraph("120302010202 Zabezpečit vojenskou činnost a chod VO FTVS UK")
                            custom_heading = custom_headings.get(item, item)
                            eval_doc.add_heading(custom_heading, level=2)
                        else:
                            custom_heading = custom_headings.get(item, item)
                            eval_doc.add_heading(custom_heading, level=2)
                        
                        if item in ["Souhrnný přehled APVVP", "Ekonomika"] and data.get("table"):
                            table_data = data["table"]
                            if table_data:
                                rows = len(table_data)
                                cols = len(table_data[0])
                                table = eval_doc.add_table(rows=rows, cols=cols)
                                for i, row in enumerate(table_data):
                                    for j, cell_value in enumerate(row):
                                        table.cell(i, j).text = str(cell_value)
                                format_table(table, font_size=10)
                        if data.get("text"):
                            eval_doc.add_paragraph(data.get("text", ""))
                    
                    from docxcompose.composer import Composer
                    composer = Composer(intro_doc)
                    composer.append(eval_doc)
                    
                    buffer = BytesIO()
                    composer.save(buffer)
                    buffer.seek(0)
                    st.download_button(
                        label="Stáhnout Word dokument",
                        data=buffer.getvalue(),
                        file_name="Vyhodnoceni.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key="download_word"
                    )
                except Exception as e:
                    st.error(f"Chyba při generování Word dokumentu: {e}")
        
        with col2:
            if st.button("Generovat PDF dokument", key="gen_pdf"):
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, Spacer
                from reportlab.lib.pagesizes import letter
                from reportlab.lib.styles import getSampleStyleSheet
                from reportlab.lib import colors
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont

                try:
                    pdfmetrics.registerFont(TTFont('TimesNewRoman', 'Times New Roman.ttf'))
                    pdfmetrics.registerFont(TTFont('TimesNewRoman-Bold', 'Times New Roman Bold.ttf'))
                except Exception as e:
                    st.error("Chyba při registraci fontů pro PDF dokument.")
                
                buffer = BytesIO()
                doc_pdf = SimpleDocTemplate(buffer, pagesize=letter)
                styles = getSampleStyleSheet()
                style_heading = styles['Heading1']
                style_heading_item = styles['Heading2']
                style_normal = styles['Normal']
                story = []
                story.append(Paragraph(f"Vyhodnocení za: {selected_period} roku {current_year}", style_heading))
                for idx, item in enumerate(doc_items if st.session_state.get("include_celkovy", False) else items_to_eval):
                    data = st.session_state.evaluations.get(key_period, {}).get(item, {})
                    if idx < 6:
                        if item == "VŠ vzdělávání":
                            vs_text = ("2. Vyhodnocení plnění dílčích úkolů „Ročního plánu VO FTVS UK na rok 202X“ dle stanovené metodiky měření\n\n"
                                       "Název cíle 3. úrovně \n"
                                       "120302 \tZajistit optimální podmínky pro vzdělávání a permanentní rozvoj znalostí a dovedností personálu v souladu s potřebami rezortu MO\n\n"
                                       "Opatření a úkoly k dosažení cíle \n"
                                       "Opatření \n"
                                       "12030201 Vysokoškolské vzdělávání personálu pro potřeby rezortu MO \n"
                                       "Úkol \n"
                                       "12030201 Komplexně realizovat studijní a pedagogickou činnost v akreditovaných programech na VO FTVS UK\n"
                                       "Dílčí úkol \n"
                                       "1203020102 Komplexně realizovat studijní a pedagogickou činnost v bakalářském a navazujícím magisterském studijním programu na VO \n"
                                       "FTVS UK\n"
                                       "Dílčí úkol \n"
                                       "120302010201 Harmonogram akademického roku 2023/2024\n"
                                       "Opatření\n"
                                       "120302010202 Zabezpečit vojenskou činnost a chod VO FTVS UK\n\n"
                                       "V rámci dílčího úkolu plnit tyto hlavní úkoly:\n\n"
                                       "2.1 Zabezpečit vysokoškolské vzdělávání")
                            story.append(Paragraph(vs_text, style_normal))
                        custom_heading = custom_headings.get(item, item)
                        story.append(Paragraph(custom_heading, style_heading_item))
                    elif idx == 6:
                        story.append(Paragraph("2.2 Zabezpečit činnost VO FTVS UK", style_heading_item))
                        story.append(Paragraph("Dílčí úkol", styles['Heading3']))
                        story.append(Paragraph("120302010202 Zabezpečit vojenskou činnost a chod VO FTVS UK", style_normal))
                        custom_heading = custom_headings.get(item, item)
                        story.append(Paragraph(custom_heading, style_heading_item))
                    else:
                        custom_heading = custom_headings.get(item, item)
                        story.append(Paragraph(custom_heading, style_heading_item))
                    
                    if item in ["Souhrnný přehled APVVP", "Ekonomika"] and data.get("table"):
                        table_data = data["table"]
                        if table_data:
                            rows = len(table_data)
                            cols = len(table_data[0])
                            table = eval_doc.add_table(rows=rows, cols=cols)
                            for i, row in enumerate(table_data):
                                for j, cell_value in enumerate(row):
                                    table.cell(i, j).text = str(cell_value)
                            format_table(table, font_size=10)
                    if data.get("text"):
                        story.append(Paragraph(data.get("text", ""), style_normal))
                doc_pdf.build(story)
                st.download_button(
                    label="Stáhnout PDF dokument",
                    data=buffer.getvalue(),
                    file_name="Vyhodnoceni.pdf",
                    mime="application/pdf",
                    key="download_pdf"
                )

with tabs[1]:
    st.header("Historie vyhodnocení")
    hist_year = st.number_input("Zvolte rok", min_value=2000, max_value=2100,
                                  value=datetime.datetime.now().year, step=1, key="hist_year")
    hist_period = st.selectbox("Vyberte období", list(evaluation_periods.keys()), key="hist_period")
    key = f"{hist_year}_{hist_period}"
    if key in st.session_state.evaluations:
        st.subheader(f"Vyhodnocení za {key}")
        evals = st.session_state.evaluations[key]
        for item, data in evals.items():
            finished_mark = " (hotovo)" if data.get("finished") else ""
            st.markdown(f"### {item}{finished_mark}")
            if item == "Souhrnný přehled APVVP" and data.get("table") and len(data["table"]) > 0:
                st.table(data["table"])
            elif item == "Ekonomika" and data.get("table") and len(data["table"]) > 0:
                st.table(data["table"])
                st.write(data.get("text", ""))
            else:
                st.write(data.get("text", ""))
    else:
        st.info("Pro zvolený rok a období nejsou uložena žádná vyhodnocení.")

with tabs[2]:
    import dpp
    dpp.run_dpp()

with tabs[3]:
    import pri
    selected_year = st.number_input("Zvolte aktuální rok pro evidenci PR-I", 
                                    min_value=2000, max_value=2100, 
                                    value=datetime.datetime.now().year, step=1)
    pri.run_pri(selected_year)

with tabs[4]:
    import zsc
    zsc.run_zsc()

with tabs[5]:
    st.header("Student")
    if st.button("Aktualizovat data"):
        from streamlit.runtime.scriptrunner import RerunException, RerunData
        raise RerunException(RerunData(st.query_params))
    import student
    student_subtabs = st.tabs(["Vojenské předměty", "Přidat studenta", "Editace studenta", "Absolventi"])
    with student_subtabs[0]:
        st.subheader("Vojenské předměty")
        cohort_tabs = st.tabs(["První ročník", "Druhý ročník", "Třetí ročník", "Čtvrtý ročník", "Pátý ročník", "Souhrn"])
        with cohort_tabs[0]:
            import student_1Bc
            student_1Bc.run_student()
        with cohort_tabs[1]:
            import student_2Bc
            student_2Bc.run_student()
        with cohort_tabs[2]:
            import student_3Bc
            student_3Bc.run_student()
        with cohort_tabs[3]:
            import student_1Mgr
            student_1Mgr.run_student()
        with cohort_tabs[4]:
            import student_2Mgr
            student_2Mgr.run_student()
        with cohort_tabs[5]:
            run_summary()
    with student_subtabs[1]:
        import student
        student.run_add_student()
    with student_subtabs[2]:
        import student
        student.run_edit_student()
    with student_subtabs[3]:
        import student
        student.run_graduates()
