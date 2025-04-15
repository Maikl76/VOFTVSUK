# supabase_client.py
import streamlit as st
from supabase import create_client, Client

# Načtěte údaje z .streamlit/secrets.toml, kde máte například:
# [supabase]
# url = "https://your-supabase-project-url.supabase.co"
# key = "your_anon_or_service_key"
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
