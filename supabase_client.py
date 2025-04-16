# supabase_client.py
import streamlit as st
from supabase import create_client, Client

# Načtěte údaje z .streamlit/secrets.toml, kde máte například:
# [supabase]
# url = "https://your-supabase-project-url.supabase.co"
# key = "your_anon_or_service_key"
# ===== KONFIGURACE SUPABASE =====
from supabase import create_client, Client
# Načtení hodnot ze st.secrets
SUPABASE_URL = st.secrets["supabase"]["supabase_url"]
SUPABASE_KEY = st.secrets["supabase"]["supabase_key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# =================================
