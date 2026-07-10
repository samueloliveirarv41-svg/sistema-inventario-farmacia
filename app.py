import streamlit as st
from supabase import create_client

# Configuração (Use os seus dados)
SUPABASE_URL = "https://ywkxkwmseaqfghnyghpz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl3a3hrd21zZWFxZmdobnlnaHB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM1MDQ4ODIsImV4cCI6MjA5OTA4MDg4Mn0.JM4ZZ1SUqCXp2GU13p3xoHWxO1WJmZeQ4KL_jN_u1TE"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Inventário CCE", layout="centered")

if 'user' not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("🔐 Login")
    email = st.text_input("E-mail:")
    if st.button("Entrar"):
        res = supabase.table("usuarios").select("*").eq("email", email).execute()
        if res.data:
            st.session_state.user = res.data[0]
            st.rerun()
else:
    st.title("📦 Inventário")
    
    # 1. Leitor de QR Code/Barcode (Câmera do celular)
    img_file_buffer = st.camera_input("Bipe o QR Code da Posição")
    
    posicao_manual = st.text_input("Ou digite o código da Posição:")
    posicao_lida = posicao_manual # (No futuro, integraremos o processamento da imagem aqui)

    if posicao_lida:
        # Busca com select('*') para garantir que traz a coluna descricao_sku
        res = supabase.table("posicoes").select("*").eq("id_posicao", posicao_lida).execute()
        
        if res.data:
            st.success(f"Posição {posicao_lida} carregada!")
            
            # Formata lista de produtos
            opcoes = {f"{item['sku']} - {item.get('descricao_sku', 'Sem descrição')}": item for item in res.data}
            sku_selecionado = st.selectbox("Selecione o produto:", list(opcoes.keys()))
            
            # 2. Formulário com campo GTIN
            with st.form("form_contagem", clear_on_submit=True):
                lote = st.text_input("Lote")
                qtd = st.number_input("Quantidade", min_value=0)
                gtin = st.text_input("GTIN do produto (Código de Barras)")
                
                if st.form_submit_button("Registrar"):
                    item = opcoes[sku_selecionado]
                    supabase.table("inventario").insert({
                        "id_posicao_fk": item['id'],
                        "sku_contado": item['sku'],
                        "lote": lote,
                        "quantidade": qtd,
                        "gtin_lido": gtin,
                        "usuario_email": st.session_state.user['email']
                    }).execute()
                    st.success("Salvo com sucesso!")
        else:
            st.warning("Posição não encontrada.")
