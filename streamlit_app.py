import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import pdfplumber

# Configuração inicial da página
st.set_page_config(page_title="PublixBot 1.5", layout="wide")

# Função para carregar o modelo de embeddings
@st.cache_resource
def load_model():
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')  # Modelo leve e eficiente
        st.write("Modelo de embeddings carregado com sucesso!")
        return model
    except Exception as e:
        st.error(f"Erro ao carregar o modelo de embeddings: {e}")
        return None

model = load_model()

# Função para encontrar parágrafos relevantes
def find_relevant_paragraphs(user_input, paragraphs):
    if model is None:
        return "Erro: O modelo de análise semântica não está disponível."
    
    try:
        # Geração do embedding da consulta do usuário
        query_embedding = model.encode(user_input)
        paragraph_embeddings = [model.encode(p) for p in paragraphs if p.strip()]

        if not paragraph_embeddings:
            return "Erro: Não há parágrafos disponíveis para comparação."

        # Cálculo da similaridade
        similarities = cosine_similarity([query_embedding], paragraph_embeddings)
        best_match_idx = similarities.argmax()

        return paragraphs[best_match_idx]

    except Exception as e:
        st.warning(f"Erro na análise semântica: {e}")
        return "Não foi possível processar a análise semântica. Tente novamente."

# Função principal para gerar respostas
def gerar_resposta(texto_usuario):
    if 'paragraphs' not in st.session_state or not st.session_state.paragraphs:
        return "Erro: Nenhum documento carregado ou o texto não foi extraído corretamente."

    # Chama a função de busca de parágrafos relevantes
    paragrafo_relevante = find_relevant_paragraphs(texto_usuario, st.session_state.paragraphs)
    return paragrafo_relevante

# Interface principal do app
def main():
    # Título e instruções
    st.title("PublixBot 1.5")
    st.markdown("Essa é a inteligência artificial desenvolvida pelo Instituto Publix. Pergunte qualquer coisa com base no conteúdo dos documentos!")

    # Área de upload de PDF
    uploaded_file = st.file_uploader("Faça upload de documentos (.pdf)", type=["pdf"])
    if uploaded_file:
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                text = "\n".join(page.extract_text() or '' for page in pdf.pages)
                if text.strip():
                    paragraphs = text.split('\n\n')
                    st.session_state.paragraphs = paragraphs
                    st.success("Documento carregado com sucesso!")
                else:
                    st.error("Erro: O documento PDF não contém texto ou o texto não foi extraído corretamente.")
        except Exception as e:
            st.error(f"Erro ao processar o PDF: {e}")

    # Campo de entrada de perguntas do usuário
    user_input = st.text_input("Digite sua mensagem aqui:")
    if user_input:
        resposta_bot = gerar_resposta(user_input)
        st.markdown(f"**Bot:** {resposta_bot}")

    # Botões de controle
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Limpar histórico"):
            st.session_state.paragraphs = []
            st.success("Histórico limpo com sucesso!")

    with col2:
        if st.button("📄 Baixar Resumo"):
            if 'paragraphs' in st.session_state and st.session_state.paragraphs:
                resumo_texto = "\n\n".join(st.session_state.paragraphs)
                st.download_button(label="📥 Clique aqui para baixar", data=resumo_texto, file_name="resumo.txt")
            else:
                st.warning("Nenhum conteúdo disponível para download.")

# Executar o app
if __name__ == '__main__':
    main()
