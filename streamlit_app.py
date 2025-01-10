import streamlit as st
import openai
from PyPDF2 import PdfReader

# Função para dividir texto em blocos menores
def dividir_em_blocos(texto, tamanho=1500):
    return [texto[i:i + tamanho] for i in range(0, len(texto), tamanho)]

# Função para carregar o texto do PDF
def carregar_pdf(arquivo):
    pdf_reader = PdfReader(arquivo)
    texto_extraido = ""
    for pagina in pdf_reader.pages:
        texto_extraido += pagina.extract_text() or ""
    return texto_extraido

# Função para limpar histórico de mensagens
def limpar_historico():
    st.session_state.history = []

# Função principal de geração de resposta
def gerar_resposta(user_input):
    if not st.session_state.documents_text:
        st.error("⚠️ Nenhum documento foi carregado.")
        return

    blocos = dividir_em_blocos(st.session_state.documents_text)
    contexto = f"Pergunta: {user_input}\n\nTexto do documento:\n{blocos[0]}"

    mensagens = [{"role": "system", "content": "Você é um assistente especializado em análise de documentos."}]
    mensagens.append({"role": "user", "content": contexto})

    try:
        with st.spinner('🧠 Processando sua pergunta...'):
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=mensagens,
                temperature=0.3
            )
            resposta = response["choices"][0]["message"]["content"]
            st.session_state.history.append({"role": "user", "content": user_input})
            st.session_state.history.append({"role": "assistant", "content": resposta})
    except Exception as e:
        st.error(f"❌ Erro ao gerar a resposta: {e}")
        st.write("🚨 Detalhes do erro:", e)

# Layout do aplicativo
st.set_page_config(page_title="PublixBot 1.5", page_icon="💛", layout="wide")

# Sidebar com configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="Insira sua chave API...")
    st.file_uploader("Faça upload de documentos (.pdf)", type=["pdf"], on_change=limpar_historico, key="upload_file")

if api_key:
    openai.api_key = api_key

    # Verifica se há arquivos carregados
    if st.session_state.upload_file is not None:
        st.session_state.documents_text = carregar_pdf(st.session_state.upload_file)
        st.success("✅ Documentos carregados com sucesso!")

        # Exibição do histórico de mensagens
        st.subheader("📄 Histórico de Mensagens:")
        if "history" not in st.session_state:
            st.session_state.history = []

        for msg in st.session_state.history:
            role_style = "background-color: #FFDD44; color: black; padding: 10px; border-radius: 5px;" if msg["role"] == "user" else "background-color: #2C2C2C; color: white; padding: 10px; border-radius: 5px;"
            st.markdown(f"<div style='{role_style}'>{msg['content']}</div>", unsafe_allow_html=True)

        # Campo de entrada de pergunta
        st.text_input("📝 Digite sua mensagem aqui:", key="user_input", on_change=gerar_resposta, args=(st.session_state.user_input,))

        # Botões de ação
        col1, col2 = st.columns([1, 1])
        with col1:
            st.button("🗑️ Limpar histórico", on_click=limpar_historico)
        with col2:
            st.download_button("📥 Baixar Resumo", data="\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state.history]), file_name="historico_resumo.txt", mime="text/plain")

else:
    st.warning("⚠️ Por favor, insira sua chave de API OpenAI para começar.")
