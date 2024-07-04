import boto3
import json
from langchain.embeddings import BedrockEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader
from rdflib import Graph, Literal, RDF, RDFS, URIRef, XSD, OWL, BNode, DC, SKOS

#
# A library of helpers.
# In future, modularize this a bit.
#

#
# General
#

# get local name of an IRI/URI
def get_local_name(iri: str):
    if "#" in iri:
        toks = iri.split("#")
        return toks[-1]
    elif "/" in iri:
        toks = iri.split("/")
        return toks[-1]
    else:
        return iri

CELL_DELIM=";"

# Return a string that can will be a scalar. If it's actually a list, stringify it using semi-colon delimeter
def get_delim_string(dicto, key):
    if not (key in dicto):
        return ""
    if type(dicto[key])==list:
        return CELL_DELIM.join(dicto[key])
    return dicto[key]

def get_delim_tokens(dicto, key):
    if not (key in dicto):
        return ""
    return dicto[key].split(CELL_DELIM)

# Return an array of dicto at key. If it's scalar, return array of len 1
def get_delim_array(dicto, key):
    if not (key in dicto):
        return []
    if type(dicto[key])==list:
        return dicto[key]
    return [dicto[key]]


def get_paragraph(content):
    return list(filter(lambda x : x != '', content.split("\n")))

def get_summary_paragraph(content):
    toks=get_paragraph(content)
    if len(toks)==1:
        return toks[0]
    elif len(toks)==2:
        print(f"Ignore header line {toks[0]}")
        return toks[1]
    else:
        raise Exception(f"Invalid summary {content}")

#
# RDF Lib helpers
#

NS = "http://example.org/orgdemo" # default, but override as you see fit

def rdf_open():
    return Graph()
    
def rdf_write(ff, s, p, o):
    ff.add((s, p, o))

def rdf_close(ff, filename):
    ff.serialize(destination = filename, format='turtle')

    
def make_uri(name):
    return URIRef(f"{NS}/{name}")

#
# Gen AI stuff via Bedrock (and a teeny bit of Langchain)
#

# Setup LLMs and bedrock client
# Modify this if you need
# Langchain needs 
# pip install -qU langchain-text-splitters langchain-community unstructured

QA_MODEL="anthropic.claude-3-sonnet-20240229-v1:0"
EMBED_MODEL="amazon.titan-embed-text-v1"

models={'QA_MODEL': QA_MODEL, 'EMBED_MODEL': EMBED_MODEL}
bedrock_client = boto3.client(service_name="bedrock-runtime")
bedrock_embeddings=BedrockEmbeddings(model_id=models['EMBED_MODEL'], client=bedrock_client)
    

def init_genail(my_models=models):
    global models
    global bedrock_embeddings
    models=my_models
    bedrock_client = boto3.client(service_name="bedrock-runtime")
    bedrock_embeddings=BedrockEmbeddings(model_id=models['EMBED_MODEL'], client=bedrock_client)
    
def summarize(doc_content):
    prompt=f"""
The text of a press release is provided below. Summarize its contents in one paragraph. Respond ONLY with the summary.

Text: {doc_content}
Summary:

    """
    
    body = json.dumps(
        {
            "anthropic_version": '',
            "max_tokens": 8192,
            "messages":[
                {
                    "role":"user", 
                    "content": [{
                        "text": prompt, 
                        "type": "text"
                    }]
                }
            ],
            "temperature": 0.1
        }
    )    
    
    response = bedrock_client.invoke_model(body=body, modelId=models['QA_MODEL'])
    response_body = json.loads(response.get('body').read())
    response_text = response_body.get('content')[0].get('text')
    return get_summary_paragraph(response_text)

def resolve_entities(candidate):
    prompt=f"""
I will provide you with an entity or event that I found in a press release. Respond with alternate names, or well-known URIs like the DBPedia URI, for the entity or event. On each line specify a different name or URI. Do not include anything else in the response except these names and URIs. 

Examples:

Text: Amazon
Alternates:
Amazon.com
AMZN
Amazon Inc.
http://dbpedia.org/resource/Amazon_(company)

Text: {candidate}
Alternates:

    """
    
    body = json.dumps(
        {
            "anthropic_version": '',
            "max_tokens": 8192,
            "messages":[
                {
                    "role":"user", 
                    "content": [{
                        "text": prompt, 
                        "type": "text"
                    }]
                }
            ],
            "temperature": 0.1
        }
    )    
    
    response = bedrock_client.invoke_model(body=body, modelId=models['QA_MODEL'])
    response_body = json.loads(response.get('body').read())
    response_text = response_body.get('content')[0].get('text')
    return get_paragraph(response_text)

def make_embedding(chunk_content):
    embedding=bedrock_embeddings.embed_documents([chunk_content])
    return str(embedding).replace(", ", ";").replace("[", "").replace("]", "")

def embedding_string(embedding):
    return str(embedding).replace(", ", ";").replace("[", "").replace("]", "")

def make_doc_splits(folder, glob="**/*.txt"):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2048,
        chunk_overlap=20,
        length_function=len,
        is_separator_regex=False,
    )

    loader = DirectoryLoader(folder, glob)
    documents = loader.load()
    all_splits = text_splitter.split_documents(documents)
    return all_splits