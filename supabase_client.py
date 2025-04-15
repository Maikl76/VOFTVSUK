# supabase_client.py
import streamlit as st
from supabase import create_client, Client

# Načtěte údaje z .streamlit/secrets.toml, kde máte například:
# [supabase]
# url = "https://your-supabase-project-url.supabase.co"
# key = "your_anon_or_service_key"
SUPABASE_URL = st.secrets["supabase"]["https://bgtpylewilzcqfqaoixx.supabase.co"]
SUPABASE_KEY = st.secrets["supabase"]["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJndHB5bGV3aWx6Y3FmcWFvaXh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ1NzQxNTQsImV4cCI6MjA2MDE1MDE1NH0.6NutsH1g8k0ruhpylqltrWD53HQFy-ZQjcUN-SULktM"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
