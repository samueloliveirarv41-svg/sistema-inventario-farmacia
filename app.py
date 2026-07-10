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

# --- FLUXO DE LOGIN ---
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
    # Variável para controlar se estamos no modo ADM
    modo_adm = False

    # --- DASHBOARD ADMINISTRATIVO ---
    if st.session_state.user.get('perfil') == 'ADM':
        modo_adm = st.sidebar.checkbox("Modo Administrador")
        
        if modo_adm:
            st.title("📊 Painel de Controle: Posições")
            
            # Cálculo das métricas
            todas_posicoes = supabase.table("posicoes").select("id_posicao").execute().data
            set_total = set([p['id_posicao'] for p in todas_posicoes])
            
            contagens = supabase.table("inventario").select("id_posicao_fk").execute().data
            ids_contados = set([c['id_posicao_fk'] for c in contagens])
            
            total = len(set_total)
            contadas = len(ids_contados)
            pendentes = total - contadas
            
            # Exibição dos cards de controle
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Posições", total)
            col2.metric("Contadas", contadas)
            col3.metric("Pendentes", pendentes)
            
            st.divider()
            st.subheader("Relatório Detalhado")
            if contagens:
                df = pd.DataFrame(supabase.table("inventario").select("*").execute().data)
                st.dataframe(df)
                st.download_button("Exportar CSV", df.to_csv(index=False), "relatorio.csv", "text/csv")
            else:
                st.info("Nenhuma contagem realizada.")

    # --- PAINEL DE CONTAGEM (Aparece apenas se NÃO estiver em modo ADM) ---
    if not modo_adm:
        st.title("📦 Inventário CCE")
        st.write(f"Usuário: {st.session_state.user['email']}")
        
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
                            st.success("Contagem registrada!")
                            st.rerun()
            else:
                st.warning("Posição não encontrada.")

    # Botão de sair fixo para ambos os perfis
    if st.button("Sair"):
        st.session_state.user = None
        st.rerun()
