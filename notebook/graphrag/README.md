# Graph RAG Patterns in Amazon Neptune
This repository provides code samples that accompany presentations on Generative AI with Amazon Neptune. 

In those presentations, we describe why Knowledge Graph improves Generative AI. We argue that retrieval-augmented generation (RAG) improves responses to questions that a user asks in a generative AI application. RAG hits your enterprise database to provide the large language model (LLM) current, accurate, relevant context to answer the question. A graph database provides such context. Furthermore, because a graph navigates relationships, it can pull in additional context that explains and elaborates the result. 

We demonstrate three Graph RAG patterns. 

1. The LLM generates the graph query. RAG involves running that query against the graph database and having the LLM summarize the results. For more, see <https://python.langchain.com/v0.1/docs/integrations/graphs/amazon_neptune_open_cypher/> and <https://python.langchain.com/v0.1/docs/integrations/graphs/amazon_neptune_sparql/>.

2. The graph represents unstructured data as embeddings (in chunks if necessary). It links these embeddings to structured resources. When the user asks a question, we first match similar embeddings in the graph, then we pull in related structured resources. We pass this as context to the LLM to answer the question. To try this out, take a look at <https://github.com/aws-samples/amazon-neptune-ontology-example-blog/blob/main/notebook/kg_ai_alg>, particularly <https://github.com/aws-samples/amazon-neptune-ontology-example-blog/blob/main/notebook/kg_ai_alg/2x-TryVSSAndRAGOnChunks.ipynb>.

3. The LLM builds the graph as a network of relationships extracted from unstructured data. To answer the user's question, we query that LLM-driven graph! To try this out, take a look at <https://github.com/aws-samples/amazon-neptune-ontology-example-blog/blob/main/notebook/kg_ai_alg>, particularly <https://github.com/aws-samples/amazon-neptune-ontology-example-blog/blob/main/notebook/kg_ai_alg/2-CreateLlamaIndex.ipynb>.

Expand as follows:
- recommended architecture that works for both LPG and RDF
- NA shortcoming: topKByEmbedding cannot filter to a specific node label. Chunks will take the top spots in search results, making it hard to find other nodes.
- Extremely searchable graph capabilities:
  > findEntity (input: lots of ways - exact name, fuzzy name, semantically similar name, alternate name (same combos), related name (same combos)). Output: found entities, their provenance, their neibhborhood, all the ways we can name them taxonomically
  > findRelationship - e.g, find a hostile takeover (but maybe that's not the actual name; fuzzy, semantic, taxo
  > searchSupportingDocs - search the docs ad hoc, return back entities, relationships, as well as where we found it. ALso return what other facts are mentioned.
  >
How to:
- KG
- Search index
- LLM - Extract keywords from question
- LLM - Suggest entity linkage for ER
- LLM - Extract entities from documents
- LLM - Summarize documents
- LLM - Chunk and embed documents

Walk me through an NLQ:
- Extract keywords from question
- Find the things in graph with those keywords. That could be structured or unstructured data.
- Find unstructured documents via chunk vector search, and then link to extracted facts, and how do they link back to the structured graph

- All this is put into context
- What would a response look like?
- 

Case Study:
Deal research:
- structured graph already has banks, lawyers, customers, key people, etc.
- unstructured has deals in SEC filings. We can put some structure aroudn this aliging with ontology; tracing structured back to where it was found in unstructured is key
- but also have loose text. 
