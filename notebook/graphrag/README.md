# Graph RAG Patterns in Amazon Neptune
This repository provids code samples that accompany presentations on Generative AI with Amazon Neptune. 

In those presentations, we describe why Knowledge Graph improves Generative AI. We argue that retrieval-augmented generation (RAG) improves responses to questions that a user asks in a generative AI application. RAG hits your enterprise database to provide the large language model (LLM) current, accurate, relevant context to answer the question. A graph database provides such context. Furthermore, because a graph navigates relationships, it can pull in additional context that explains and elaborates the result. 

We demonstrate three Graph RAG patterns. 

1. The LLM generates the graph query. RAG involves running that query against the graph database and having the LLM summarize the results.

2. The graph represents unstructured data as embeddings (in chunks if necessary). It links these embeddings to structured resources. When the user asks a question, we first match similar embeddings in the graph, then we pull in related structured resources. We pass this as context to the LLM to answer the question.

3. The LLM builds the graph as a network of relationships extracted from unstructured data. To answer the user's question, we query that LLM-driven graph!
