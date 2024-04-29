# main.py

import threading
import streamlit as st
from llama_index.core.settings import Settings
from llama_index.llms.bedrock import Bedrock
from llama_index.embeddings.bedrock import BedrockEmbedding
from load import create_or_load_indexes
from streamlit.runtime.scriptrunner.script_run_context import (
    add_script_run_ctx,
)
from llama_index.core.evaluation import FaithfulnessEvaluator
from llama_index.core.evaluation import RelevancyEvaluator
from llama_index.core.prompts import PromptTemplate

faithfulness_eval_prompt = PromptTemplate(
    "Please tell if a given piece of information "
    "is supported by the context.\n"
    "You need to answer with either YES or NO.\n"
    "Answer YES if any of the context supports the information, even "
    "if most of the context is unrelated. "
    "Some examples are provided below. \n\n"
    "Information: Neptune supports vector search.\n"
    "Context: With Neptune Analytics, you can run similarity searches on vectors stored along with your graph for generative AI applications"
    "Answer: YES\n"
    "Information: Amazon DocumentDB now supports vector search.\n"
    "Context: Amazon DocumentDB (with MongoDB compatibility) now supports vector search with Hierarchical Navigable Small World (HNSW) index.\n"
    "Answer: NO\n"
    "Information: {query_str}\n"
    "Context: {context_str}\n"
    "Answer: "
)


# ------------------------------------------------------------------------
# LlamaIndex - Amazon Bedrock

llm = Bedrock(
    model="anthropic.claude-3-sonnet-20240229-v1:0",
    model_kwargs={"temperature": 0},
    streaming=True,
)
embed_model = BedrockEmbedding(model="amazon.titan-embed-text-v1")
faithfulness_evaluator = FaithfulnessEvaluator(
    llm=llm, eval_template=faithfulness_eval_prompt
)
relevancy_evaluator = RelevancyEvaluator(llm=llm)
Settings.llm = llm
Settings.embed_model = embed_model
Settings.chunk_size = 1024

# ------------------------------------------------------------------------
# Streamlit

# Page title
st.set_page_config(
    page_title="Press Release Q&A Chatbot",
    layout="wide",
)


# Clear Chat History function
def clear_screen():
    st.session_state.messages = [
        {"role": "assistant", "content": "How may I assist you today?"}
    ]


def write_messages(context):
    for message in st.session_state.messages:
        if message["role"] == "assistant" or (
            "context" in message and message["context"] == context
        ):
            with st.chat_message(message["role"]):
                st.write(message["content"])


def run_query(indices, prompt, context, col):
    with col:
        with st.chat_message("user"):
            st.write(prompt)
        query_engine = indices[context].as_query_engine()
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = query_engine.query(prompt)
                st.write(response.response)
                st.session_state.messages.append(
                    {"role": context, "content": response.response}
                )
        st.divider()

        with st.spinner("Evaluating Responses ..."):
            resp = evaluate_response(prompt, response)
            st.write(f"**FAITHFULNESS EVALUATION**: {resp['faithfulness']}")
            st.write(f"**RELEVANCY EVALUATION**: {resp['relevancy']}")


def evaluate_response(query, response):
    faith_result = faithfulness_evaluator.evaluate_response(response=response)
    relevancy_result = relevancy_evaluator.evaluate_response(
        query=query, response=response
    )
    return {
        "faithfulness": str(faith_result.passing),
        "relevancy": str(relevancy_result.passing),
    }


st.title("Press Release Q&A Chatbot")
# st.image("llamaposeidon.png", use_column_width=True)
st.divider()


@st.cache_resource(show_spinner=False)
def load_indices():
    with st.spinner(text="Loading and indexing your data. This may take a while..."):
        return create_or_load_indexes()


# with Profiler() as pr:

# Create Index
indices = load_indices()

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "How may I assist you today?",
            "context": "assistant",
        }
    ]


col1, col2 = st.columns([0.5, 0.5])
with col1:
    st.subheader("RAG - similarity using vectors")
    write_messages("vssindex")

with col2:
    st.subheader("Graph RAG - similarity using vectors + Knowledge Graph")
    write_messages("kgindex")


if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})

    t1 = threading.Thread(target=run_query, args=[indices, prompt, "vss_index", col1])
    t2 = threading.Thread(target=run_query, args=[indices, prompt, "kg_index", col2])
    add_script_run_ctx(t1)
    add_script_run_ctx(t2)
    t1.start()
    t2.start()

    t1.join()
    t2.join()
