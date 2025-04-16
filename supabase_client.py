# supabase_client.py
import streamlit as st
from supabase import create_client, Client

# Load from st.secrets so you only define it once:
SUPABASE_URL = st.secrets["supabase"]["supabase_url"]
SUPABASE_KEY = st.secrets["supabase"]["supabase_key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_students():
    try:
        resp = supabase.table("students").select("*").execute()
        return resp.data or []
    except Exception as e:
        st.error(f"Chyba při načítání studentů: {e}")
        return []

def save_student_record(student):
    try:
        resp = supabase.table("students") \
                         .update(student) \
                         .eq("id_op", student["id_op"]) \
                         .execute()
        return resp.data
    except Exception as e:
        st.error(f"Chyba při ukládání studenta: {e}")
        return None
