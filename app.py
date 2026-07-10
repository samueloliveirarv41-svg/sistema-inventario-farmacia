import streamlit as st
from supabase import create_client
from streamlit_qrcode_scanner import qrcode_scanner

# Configuração (Use os seus dados)
SUPABASE_URL = "https://ywkxkwmseaqfghnyghpz.supabase.co"
SUPABASE_KEY = "SUA_CHAVE_AQUI" # Certifique-se de usar a chave correta
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
    st.title("📦 Inventário - Leitura Automática")
    
    # Leitor de QR Code / Código de Barras
    # Ele retorna o valor lido automaticamente
    valor_lido = qrcode_scanner(key='scanner')
    
    # Campo manual caso o bipe falhe
    posicao_lida = st.text_input("Código da Posição (ou bipe):", value=valor_lido if valor_lido else "")

    if posicao_lida:
        res = supabase.table("posicoes").select("*").eq("id_posicao", posicao_lida).execute()
        
        if res.data:
            st.success(f"Posição {posicao_lida} detectada!")
            
            opcoes = {f"{item['sku']} - {item.get('descricao_sku', 'Sem descrição')}": item for item in res.data}
            sku_selecionado = st.selectbox("Selecione o produto:", list(opcoes.keys()))
            
            with st.form("form_contagem", clear_on_submit=True):
                lote = st.text_input("Lote")
                qtd = st.number_input("Quantidade", min_value=0)
                gtin = st.text_input("GTIN do produto")
                
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
                    st.success("Contagem salva!")
        else:
            st.warning("Posição não encontrada.")
