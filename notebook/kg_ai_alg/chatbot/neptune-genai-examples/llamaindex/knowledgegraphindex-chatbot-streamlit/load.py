import os
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


KG_PERSIST_DIR = "storage_kg"
VSS_PERSIST_DIR = "storage_vss"
graph_identifier = "g-fcowfewla8"
max_triplets_per_chunk = 15

documents = SimpleDirectoryReader("data").load_data()


def create_or_load_indexes():
    graph_store = NeptuneAnalyticsGraphStore(graph_identifier=graph_identifier)
    vector_store = NeptuneAnalyticsVectorStore(
        graph_identifier=graph_identifier, embedding_dimension=1536
    )
    print('getting the index')
    indexes = {
        "kg_index": load_kg_index(graph_store),
        "vss_index": load_vector_index(vector_store),
    }
    return indexes


def load_kg_index(graph_store):
    # check if kg storage already exists
    if not os.path.exists(KG_PERSIST_DIR):
        # load the documents and create the index
        kg_storage_context = StorageContext.from_defaults(graph_store=graph_store)
        print("Creating KG Index")

        text = (
            "Some text is provided below. Given the text, extract up to "
            "{max_knowledge_triplets} "
            "knowledge triplets in the form of (subject, predicate, object). Avoid stopwords.\n"
            "Triplets should be focused on entities such as people and companies, and events.\n"
            "---------------------\n"
            "Example:"
            "Text: Amazon is located in Seattle."
            "Triplets:\n(Amazon, is located in, Seattle)\n"
            "Text: Amazon will acquire Whole Foods Market for $42 per share.\n"
            "Triplets:\n"
            "(Amazon, acquires, Whole Foods Market)\n"
            "(Whole Foods Market, acquired for, $42 per share)\n"
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

    return kg_index


def load_vector_index(vector_store):
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

    return vss_index
