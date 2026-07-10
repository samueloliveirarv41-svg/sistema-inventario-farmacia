import streamlit as st
from supabase import create_client
from streamlit_qrcode_scanner import qrcode_scanner

# --- CONFIGURAÇÃO ---
SUPABASE_URL = "https://ywkxkwmseaqfghnyghpz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl3a3hrd21zZWFxZmdobnlnaHB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM1MDQ4ODIsImV4cCI6MjA5OTA4MDg4Mn0.JM4ZZ1SUqCXp2GU13p3xoHWxO1WJmZeQ4KL_jN_u1TE"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Inventário CCE", layout="centered")

if 'user' not in st.session_state:
    st.session_state.user = None

# --- TELA DE LOGIN ---
if st.session_state.user is None:
    st.title("🔐 Login Inventário")
    email = st.text_input("E-mail:")
    if st.button("Entrar"):
        try:
            res = supabase.table("usuarios").select("*").eq("email", email.strip()).execute()
            if res.data and len(res.data) > 0:
                st.session_state.user = res.data[0]
                st.rerun()
            else:
                st.error("Usuário não encontrado.")
        except Exception as e:
            st.error(f"Erro ao conectar: {e}")
else:
    # --- TELA DE CONTAGEM ---
    st.title("📦 Inventário CCE")
    st.write(f"Usuário: {st.session_state.user['email']}")
    
    st.subheader("Bipe a Posição")
    valor_lido = qrcode_scanner(key='scanner')
    
    posicao_digitada = st.text_input("Código da Posição:", value=valor_lido if valor_lido else "")

    if posicao_digitada:
        try:
            res = supabase.table("posicoes").select("*").eq("id_posicao", posicao_digitada).execute()
            
            if res.data:
                st.success(f"Posição {posicao_digitada} encontrada!")
                
                # Ajuste para não mostrar "None"
                opcoes = {}
                for item in res.data:
                    sku = item.get('sku', '')
                    desc = item.get('descricao_sku')
                    # Cria um label limpo
                    label = f"{sku} - {desc}" if desc and desc.lower() != 'none' else f"{sku}"
                    opcoes[label] = item
                
                sku_selecionado = st.selectbox("Selecione o produto:", list(opcoes.keys()))
                
                with st.form("form_contagem", clear_on_submit=True):
                    lote = st.text_input("Lote")
                    qtd = st.number_input("Quantidade Contada", min_value=0, step=1)
                    gtin = st.text_input("GTIN / Código de Barras")
                    
                    if st.form_submit_button("Registrar Contagem"):
                        item = opcoes[sku_selecionado]
                        supabase.table("inventario").insert({
                            "id_posicao_fk": item['id'],
                            "sku_contado": item['sku'],
                            "lote": lote,
                            "quantidade": qtd,
                            "gtin_lido": gtin,
                            "usuario_email": st.session_state.user['email']
                        }).execute()
                        st.success("Contagem registrada com sucesso!")
            else:
                st.warning("Posição não encontrada no banco de dados.")
        except Exception as e:
            st.error(f"Erro ao processar: {e}")

    if st.button("Sair"):
        st.session_state.user = None
        st.rerun()
