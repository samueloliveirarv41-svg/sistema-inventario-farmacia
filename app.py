import streamlit as st
from supabase import create_client

# --- CONFIGURAÇÃO E CONEXÃO ---
# Substitua pelos seus dados reais do Supabase
SUPABASE_URL = "https://ywkxkwmseaqfghnyghpz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl3a3hrd21zZWFxZmdobnlnaHB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM1MDQ4ODIsImV4cCI6MjA5OTA4MDg4Mn0.JM4ZZ1SUqCXp2GU13p3xoHWxO1WJmZeQ4KL_jN_u1TE"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Inventário CCE", layout="centered")

# --- ESTADO DA SESSÃO ---
if 'user' not in st.session_state:
    st.session_state.user = None

# --- TELA DE LOGIN ---
if st.session_state.user is None:
    st.title("🔐 Inventário CCE - Acesso")
    email = st.text_input("E-mail:")
    if st.button("Entrar"):
        try:
            res = supabase.table("usuarios").select("*").eq("email", email).execute()
            if res.data:
                st.session_state.user = res.data[0]
                st.rerun()
            else:
                st.error("Usuário não encontrado.")
        except Exception as e:
            st.error(f"Erro: {e}")

# --- SISTEMA DE CONTAGEM ---
else:
    st.sidebar.title("Menu")
    st.sidebar.write(f"Usuário: {st.session_state.user['email']}")
    if st.sidebar.button("Sair"):
        st.session_state.user = None
        st.rerun()

    st.title("📦 Painel de Contagem")
    posicao_lida = st.text_input("Código da Posição:")
    
    if posicao_lida:
        # Busca produtos vinculados à posição
        res = supabase.table("posicoes").select("*").eq("id_posicao", posicao_lida).execute()
        
        if res.data:
            st.success(f"Posição {posicao_lida} encontrada!")
            
            # Dropdown para selecionar o SKU (trata Multi-SKU)
            opcoes = [f"{item['sku']} - {item['descricao_sku']}" for item in res.data]
            sku_selecionado = st.selectbox("Selecione o produto desta posição:", opcoes)
            
            with st.form("form_contagem", clear_on_submit=True):
                lote = st.text_input("Lote")
                qtd = st.number_input("Quantidade", min_value=0, step=1)
                
                if st.form_submit_button("Salvar Contagem"):
                    try:
                        # Insere na tabela inventario
                        supabase.table("inventario").insert({
                            "id_posicao_fk": res.data[0]['id'],
                            "sku_contado": sku_selecionado.split(' - ')[0],
                            "lote": lote,
                            "quantidade": qtd,
                            "usuario_email": st.session_state.user['email']
                        }).execute()
                        st.success(f"Registrado: {sku_selecionado.split(' - ')[0]} | Qtd: {qtd}")
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
        else:
            st.warning("Posição não cadastrada. Verifique o código.")