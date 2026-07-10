import streamlit as st
from supabase import create_client
from streamlit_qrcode_scanner import qrcode_scanner
import pandas as pd

# --- CONFIGURAÇÃO ---
SUPABASE_URL = "https://ywkxkwmseaqfghnyghpz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl3a3hrd21zZWFxZmdobnlnaHB6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM1MDQ4ODIsImV4cCI6MjA5OTA4MDg4Mn0.JM4ZZ1SUqCXp2GU13p3xoHWxO1WJmZeQ4KL_jN_u1TE"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Inventário CCE", layout="centered")

if 'user' not in st.session_state:
    st.session_state.user = None

# --- LOGIN ---
if st.session_state.user is None:
    st.title("🔐 Login Inventário")
    email = st.text_input("E-mail:")
    if st.button("Entrar"):
        res = supabase.table("usuarios").select("*").eq("email", email.strip()).execute()
        if res.data:
            st.session_state.user = res.data[0]
            st.rerun()
        else:
            st.error("Usuário não encontrado.")
else:
    # --- DASHBOARD ADMIN (Verifica se perfil é 'ADM') ---
    if st.session_state.user.get('perfil') == 'ADM':
        if st.sidebar.checkbox("Modo Administrador"):
            st.title("📊 Dashboard de Gestão")
            dados = supabase.table("inventario").select("*").execute()
            if dados.data:
                df = pd.DataFrame(dados.data)
                col1, col2 = st.columns(2)
                col1.metric("Total de Contagens", len(df))
                col2.metric("SKUs Contados", df['sku_contado'].nunique())
                st.dataframe(df)
                st.download_button("Exportar CSV", df.to_csv(index=False), "relatorio.csv", "text/csv")
            else:
                st.info("Nenhuma contagem realizada.")
            st.divider()

    # --- PAINEL DE CONTAGEM ---
    st.title("📦 Inventário CCE")
    st.write(f"Usuário: {st.session_state.user['email']} | Perfil: {st.session_state.user.get('perfil')}")
    
    valor_lido = qrcode_scanner(key='scanner')
    posicao_digitada = st.text_input("Código da Posição:", value=valor_lido if valor_lido else "")

    if posicao_digitada:
        pos_data = supabase.table("posicoes").select("*").eq("id_posicao", posicao_digitada).execute()
        if pos_data.data:
            contagens = supabase.table("inventario").select("sku_contado").eq("id_posicao_fk", pos_data.data[0]['id']).execute()
            skus_contados = [c['sku_contado'] for c in contagens.data]
            
            opcoes = {}
            for item in pos_data.data:
                sku = item['sku']
                status = "✅" if sku in skus_contados else "⏳"
                desc = item.get('descricao_sku') or ""
                label = f"{status} {sku} - {desc}"
                opcoes[label] = item

            if len(skus_contados) >= len(pos_data.data):
                st.balloons()
                st.success(f"Posição {posicao_digitada} finalizada!")
            else:
                sku_selecionado = st.selectbox("Selecione o produto:", list(opcoes.keys()))
                with st.form("form_contagem", clear_on_submit=True):
                    fabricante = st.text_input("Fabricante")
                    lote = st.text_input("Lote")
                    qtd = st.number_input("Quantidade", min_value=0, step=1)
                    sem_gtin = st.checkbox("Produto sem GTIN")
                    gtin = st.text_input("GTIN / Código de Barras", disabled=sem_gtin)
                    
                    if st.form_submit_button("Registrar"):
                        item = opcoes[sku_selecionado]
                        supabase.table("inventario").insert({
                            "id_posicao_fk": item['id'],
                            "sku_contado": item['sku'],
                            "fabricante": fabricante,
                            "lote": lote,
                            "quantidade": qtd,
                            "gtin_lido": "SEM GTIN" if sem_gtin else gtin,
                            "usuario_email": st.session_state.user['email']
                        }).execute()
                        st.success("Registrado!")
                        st.rerun()
        else:
            st.warning("Posição não encontrada.")

    if st.button("Sair"):
        st.session_state.user = None
        st.rerun()
