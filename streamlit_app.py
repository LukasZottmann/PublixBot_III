import streamlit as st
import openai
import pdfplumber
import asyncio

st.title("💛 PublixBot Chatbot")
st.write("Carregue documentos e faça perguntas interativas com base neles!")

openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.warning("Por favor, insira sua chave da OpenAI API para continuar.")
else:
    openai.api_key = openai_api_key

    uploaded_files = st.file_uploader("Faça upload de documentos (.pdf)", type=["pdf"], accept_multiple_files=True)
    if uploaded_files:
        st.write("✅ Documentos carregados com sucesso!")

        # Função de extração com PDFplumber
        def extract_text_from_pdfs(files):
            all_text = ""
            for file in files:
                try:
                    with pdfplumber.open(file) as pdf:
                        for page in pdf.pages:
                            text = page.extract_text()
                            if text:
                                all_text += text + "\n"
                except Exception as e:
                    st.error(f"Erro ao ler o arquivo {file.name}: {e}")
            return all_text if all_text.strip() else "Não foi possível extrair texto do PDF."

        documents_text = extract_text_from_pdfs(uploaded_files)

        # Exibir prévia do texto
        if len(documents_text) > 0:
            st.write("📝 **Prévia do texto extraído:**")
            st.code(documents_text[:1000])  # Mostra os primeiros 1000 caracteres

        if "history" not in st.session_state:
            st.session_state.history = []

        # Função para enviar as primeiras partes do texto diretamente
        def gerar_resposta_com_texto(texto_documento, pergunta):
            st.write("🔍 Enviando trecho completo para análise...")
            async def gerar_resposta():
                response = await openai.ChatCompletion.acreate(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Você é um assistente especializado em análise de documentos PDF."},
                        {"role": "user", "content": f"Este é um trecho do documento: {texto_documento[:3000]}. Com base nisso, responda: {pergunta}"}
                    ],
                    temperature=0.3
                )
                return response["choices"][0]["message"]["content"]

            try:
                answer = asyncio.run(gerar_resposta())
                st.session_state.history.append({"role": "assistant", "content": answer})
                st.write("✅ **Resposta gerada com sucesso:**")
                st.code(answer)
            except Exception as e:
                st.error(f"Erro ao gerar a resposta: {e}")

        # Campo de mensagem do usuário
        user_input = st.text_input("Digite sua pergunta:")
        if user_input:
            gerar_resposta_com_texto(documents_text, user_input)
