"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

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

# Configure the faitfulness eval prompt template
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
# LlamaIndex - Amazon
# This section sets up global settings for LlamaIndex, such as the LLM
# and embedding models

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
# Functions
# This section contains the functions needed to be called by our streamlit app


def write_messages(context):
    """Writes the message to the chatbot window

    Args:
        context: The context of the message
    """
    for message in st.session_state.messages:
        if message["role"] == "assistant" or (
            "context" in message and message["context"] == context
        ):
            with st.chat_message(message["role"]):
                st.write(message["content"])


def run_query(prompt, context, col):
    """Runs the user prompt as a query and returns the result.
    This then runs evaluations on the answers provided.

    Args:
        prompt: The user's prompt
        context: The context of the message
        col: The streamlit column to update
    """
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
            with st.expander("See explanation"):
                resp = evaluate_response(prompt, response)
                st.write(f"**FAITHFULNESS EVALUATION**: {resp['faithfulness']}")
                st.write(f"**RELEVANCY EVALUATION**: {resp['relevancy']}")


def evaluate_response(query, response):
    """Runs evaluations of the responses

    Args:
        query: The user's question
        response: The LLM's response

    Returns:
        The evaluation results
    """
    faith_result = faithfulness_evaluator.evaluate_response(response=response)
    relevancy_result = relevancy_evaluator.evaluate_response(
        query=query, response=response
    )
    return {
        "faithfulness": str(faith_result.feedback),
        "relevancy": str(relevancy_result.feedback),
    }


@st.cache_resource(show_spinner=False)
def load_indices():
    """Loads the indicies while showing the spinner

    Returns:
        The indicies
    """
    with st.spinner(text="Loading and indexing your data. This may take a while..."):
        return create_or_load_indexes()


def run_parallel_retrievals(prompt):
    """Runs the parallel retrieval workflows in a multi-threaded manner

    Args:
        prompt: The user's question
    """
    st.session_state.messages.append({"role": "user", "content": prompt})
    t1 = threading.Thread(target=run_query, args=[prompt, "vss_index", col1])
    t2 = threading.Thread(target=run_query, args=[prompt, "kg_index", col2])
    add_script_run_ctx(t1)
    add_script_run_ctx(t2)
    t1.start()
    t2.start()

    t1.join()
    t2.join()


# ------------------------------------------------------------------------
# Streamlit
# This section represents our Streamlit App UI and Actions

# Page title
st.set_page_config(
    page_title="Press Release Q&A Chatbot",
    layout="wide",
)

st.title("Amazon Press Release Q&A Chatbot")
st.divider()

# Create or load the Vector and KnowledgeGraph indices
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

# Setup columns for the two chatbots
col1, col2 = st.columns([0.5, 0.5])
with col1:
    st.subheader("RAG - similarity using vectors")
    write_messages("vssindex")

with col2:
    st.subheader("Graph RAG - similarity using vectors + Knowledge Graph")
    write_messages("kgindex")


# Configure the sidebar with the example questions
with st.sidebar:
    st.header("Example Queries")
    st.subheader("Exploratory Queries")
    st.write(
        "Questions where all the data to answer it exists within a single document are questions where we expect both RAG and Graph RAG applications to do well."
    )
    if st.button("Try it", key="exploratory"):
        run_parallel_retrievals("How is AWS increasing energy efficiency?")

    st.subheader("Connect the Dots Queries")
    st.write(
        "Questions that require taking information from multiple documents and connecting them together is an example of where RAG struggles and Graph RAG does well."
    )
    if st.button("Try it", key="connect_the_dots"):
        run_parallel_retrievals(
            "What are the top press releases from AWS?"
        )

    st.subheader("Whole Dataset Reasoning")
    st.write(
        "Questions that require aggregation across the dataset is an example of where RAG struggles and Graph RAG does well."
    )
    if st.button("Try it", key="whole_dataset"):
        run_parallel_retrievals("What people are most mentioned by AWS")

# Setup the chat input
if user_prompt := st.chat_input():
    run_parallel_retrievals(user_prompt)
