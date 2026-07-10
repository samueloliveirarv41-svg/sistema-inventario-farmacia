import streamlit as st
from supabase import create_client

# --- CONFIGURAÇÃO ---
# Nota: No Streamlit Cloud, recomenda-se usar st.secrets["SUPABASE_URL"]
# Caso prefira manter fixo aqui, certifique-se de que as chaves estão corretas.
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
            st.error(f"Erro de conexão: {e}")

# --- TELA DE CONTAGEM ---
else:
    st.sidebar.write(f"Usuário: {st.session_state.user['email']}")
    if st.sidebar.button("Sair"):
        st.session_state.user = None
        st.rerun()

    st.title("📦 Painel de Contagem")
    posicao_lida = st.text_input("Bipe ou Digite a Posição:")
    
    if posicao_lida:
        # Busca produtos na posição
        res = supabase.table("posicoes").select("*").eq("id_posicao", posicao_lida).execute()
        
        if res.data:
            st.success(f"Posição {posicao_lida} encontrada!")
            
            # Cria a lista com SKU + Descrição
            opcoes = []
            for item in res.data:
                desc = item.get('descricao_sku') or "Sem descrição"
                opcoes.append(f"{item['sku']} - {desc}")
            
            sku_selecionado = st.selectbox("Selecione o produto:", opcoes)
            
            with st.form("form_contagem", clear_on_submit=True):
                lote = st.text_input("Lote")
                qtd = st.number_input("Quantidade Contada", min_value=0, step=1)
                
                if st.form_submit_button("Registrar Contagem"):
                    try:
                        # Identifica o ID único do item selecionado
                        # Encontra o dicionário correspondente ao item selecionado
                        item_selecionado_dados = next(
                            (i for i in res.data if f"{i['sku']} - {(i.get('descricao_sku') or 'Sem descrição')}" == sku_selecionado),
                            None
                        )
                        
                        if item_selecionado_dados:
                            supabase.table("inventario").insert({
                                "id_posicao_fk": item_selecionado_dados['id'],
                                "sku_contado": item_selecionado_dados['sku'],
                                "lote": lote,
                                "quantidade": qtd,
                                "usuario_email": st.session_state.user['email']
                            }).execute()
                            st.success(f"Sucesso! {sku_selecionado.split(' - ')[0]} registrado.")
                    except Exception as e:
                        st.error(f"Erro ao salvar no banco: {e}")
        else:
            st.warning("Posição não cadastrada.")
