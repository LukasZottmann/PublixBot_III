import streamlit as st
import openai
import pdfplumber
import asyncio
import re

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
            st.code(documents_text[:500])  # Mostra os primeiros 500 caracteres

        if "history" not in st.session_state:
            st.session_state.history = []

        # Função para limpar histórico duplicado
        def limpar_historico(history):
            perguntas_respostas = set()
            historico_limpo = []
            for msg in history:
                conteudo = msg["content"]
                if conteudo not in perguntas_respostas:
                    historico_limpo.append(msg)
                    perguntas_respostas.add(conteudo)
            return historico_limpo

        # Função de geração de resposta
        async def gerar_resposta(user_input):
            trecho_documento = documents_text[:2000]  # Enviar apenas os primeiros 2000 caracteres para evitar repetições
            st.session_state.history.append({"role": "user", "content": user_input})

            # Limpar histórico para evitar duplicações
            st.session_state.history = limpar_historico(st.session_state.history)

            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Você é um assistente de análise de documentos PDF. Responda de forma clara e concisa, sem repetir partes do texto ou expandir demais as explicações."},
                    *st.session_state.history,
                    {"role": "user", "content": f"Trecho do documento: {trecho_documento}\nPergunta: {user_input}"}
                ],
                temperature=0.3
            )
            answer = response["choices"][0]["message"]["content"]
            st.session_state.history.append({"role": "assistant", "content": answer})

        # Campo de mensagem do usuário
        user_input = st.text_input("Digite sua pergunta:")
        if user_input:
            try:
                st.write("🧠 Gerando resposta...")
                asyncio.run(gerar_resposta(user_input))
            except Exception as e:
                st.error(f"Erro ao gerar a resposta: {e}")

        # Exibição do histórico de mensagens no formato de chat
        for message in st.session_state.history:
            if message["role"] == "user":
                st.markdown(f'<div class="chat-message user-message">{message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message bot-message">{message["content"]}</div>', unsafe_allow_html=True)
