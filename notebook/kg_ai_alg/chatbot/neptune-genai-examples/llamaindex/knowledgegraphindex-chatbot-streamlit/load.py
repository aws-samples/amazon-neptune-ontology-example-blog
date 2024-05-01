"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os
from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader
from llama_index.graph_stores.neptune import NeptuneAnalyticsGraphStore
from llama_index.vector_stores.neptune import NeptuneAnalyticsVectorStore
from llama_index.core import (
    KnowledgeGraphIndex,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
)
from llama_index.core import PromptTemplate


load_dotenv()
KG_PERSIST_DIR = os.getenv("BASE_PERSIST_DIR") + "_kg"
VSS_PERSIST_DIR = os.getenv("BASE_PERSIST_DIR") + "_vss"
graph_identifier = os.getenv("GRAPH_ID")
max_triplets_per_chunk = os.getenv("TRIPLETS_PER_CHUNK")


documents = SimpleDirectoryReader("./data").load_data()


def create_or_load_indexes():
    """Overall function to coordinate loading both the VSS and KG indexes

    Returns:
        A dict of indicies
    """
    graph_store = NeptuneAnalyticsGraphStore(graph_identifier=graph_identifier)
    vector_store = NeptuneAnalyticsVectorStore(
        graph_identifier=graph_identifier, embedding_dimension=1536
    )
    print("getting the index")
    indexes = {
        "kg_index": load_kg_index(graph_store),
        "vss_index": load_vector_index(vector_store),
    }
    return indexes


def load_kg_index(graph_store):
    """Creates or loads the KG Index

    Args:
        graph_store: The KG Index to use in the storage context

    Returns:
        The loaded KG Index
    """
    # check if kg storage already exists
    if not os.path.exists(KG_PERSIST_DIR):
        # load the documents and create the index
        kg_storage_context = StorageContext.from_defaults(graph_store=graph_store)
        print("Creating KG Index")

        text = (
            "Your task is to take the text provided and extract up to the "
            "{max_knowledge_triplets} most important concepts in "
            "knowledge triplets in the form of (subject, predicate, object).\n"
            "Triplets should be focused on entities such as people, companies, locations, and events.\n"
            "All triplets should not include stopwords such as a, an, and, are, as, at, be, but, by, for, if, in, into, is, it, no, not, of, on, or, such, that, the, their, then, there, these, they, this, to, was, will and with.\n"
            "For each predicate, simplify the action into a single verb or a 2 words.\n"
            "---------------------\n"
            "Example:"
            "Text: Amazon is located in Seattle."
            "Triplets:\n(amazon, is located in, seattle)\n"
            "Text: Amazon will acquire Whole Foods Market for $42 per share.\n"
            "Triplets:\n"
            "(Amazon, acquires, Whole Foods Market)\n"
            "(whole foods market, acquired for, $42 per share)\n"
            "---------------------\n"
            "Text: {text}\n"
            "Triplets:\n"
        )
        template: PromptTemplate = PromptTemplate(text)
        kg_index = KnowledgeGraphIndex.from_documents(
            documents,
            storage_context=kg_storage_context,
            max_triplets_per_chunk=max_triplets_per_chunk,
            include_embeddings=True,
            show_progress=True,
            kg_triple_extract_template=template,
        )

        # persistent storage
        kg_index.storage_context.persist(persist_dir=KG_PERSIST_DIR)
    else:
        # load the existing index
        print("Loading KG Index")
        storage_context = StorageContext.from_defaults(
            persist_dir=KG_PERSIST_DIR, graph_store=graph_store
        )
        kg_index = load_index_from_storage(storage_context)

    print("KG Index Loading Complete")
    return kg_index


def load_vector_index(vector_store):
    """Creates or loads the VSS Index

    Args:
        graph_store: The VSS Index to use in the storage context

    Returns:
        The loaded VSS Index
    """
    # check if vss storage already exists
    if not os.path.exists(VSS_PERSIST_DIR):
        # load the documents and create the index
        vss_storage_context = StorageContext.from_defaults(vector_store=vector_store)

        print("Creating VSS Index")
        vss_index = VectorStoreIndex.from_documents(
            documents,
            storage_context=vss_storage_context,
            max_triplets_per_chunk=max_triplets_per_chunk,
            include_embeddings=True,
            show_progress=True,
        )

        # persistent storage
        vss_index.storage_context.persist(persist_dir=VSS_PERSIST_DIR)
    else:
        # load the existing index
        print("Loading VSS Index")
        storage_context = StorageContext.from_defaults(
            persist_dir=VSS_PERSIST_DIR, vector_store=vector_store
        )
        vss_index = load_index_from_storage(storage_context)

    print("VSS Index Loading Complete")
    return vss_index
