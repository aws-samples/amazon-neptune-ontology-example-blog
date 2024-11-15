import boto3
import json
from pathlib import Path

# Setup LLMs and bedrock client
# Modify this if you need

QA_MODEL="anthropic.claude-3-sonnet-20240229-v1:0"
EMBED_MODEL="amazon.titan-embed-text-v1"

MODELS={'QA_MODEL': QA_MODEL, 'EMBED_MODEL': EMBED_MODEL}
bedrock_client = boto3.client(service_name="bedrock-runtime")

ONTOLOGY_CONTENT=Path('source/rdf/org_ontology.ttl').read_text()
TAXONOMY_CONTENT=Path('source/rdf/industry_taxonomy.ttl').read_text()

BACKTICKS="""
```
"""

ANALYZE_START_PROMPT="""
You are an expert AI assistant that excels in understanding and analyzing natural language questions. For a given question, you can tell me what entities it refers to and what information about these entities are being asked for. 

DO NOT answer the question. I will do that. Your task is to respond with a JSON object that summarizes the entities and intent of the question. Respond ONLY with the JSON. Do not include any other text in the response.

Here is the structure of the JSON:

{
 "entities": 
  "entity name A": {
   "alternateEntityNames" : [ "alternate entity name A1", "alternate entity name A2" ],
   "wellKnownURIs": ["entity uri A1", "entity uri A2"]  
   "type": "entity type X", 
  },
  "entity name B": {
   "alternateEntityNames" : [ "alternate entity name B1", "alternate entity name B2" ],
   "wellKnownURIs": ["entity uri B1", "entity uri B2"]  
   "type": "entity type Y", 
  }
 },
 
 "types": {
  "entity type X": {
   "alternateNames" : [ "alternate entity type X1", ""alternate entity type X2" ],
   "wellKnownURIs": ["type uri X1", "type uri X2"]  
  },
  "entity type Y": {
   "alternateNames" : [ "alternate entity type Y1", ""alternate entity type Y2" ],
   "wellKnownURIs": ["type uri Y1", "type uri Y2"]  
  },

 "predicates": {
  "predicate P": {
   "alternateNames" : [ "alternate predicate P1", ""alternate predicate P2" ],
   "wellKnownURIs": ["predicate uri P1", "predicate uri P2"]  
  },
  "predicate Q": {
   "alternateNames" : [ "alternate predicate Q1", ""alternate predicate Q2" ],
   "wellKnownURIs": ["predicate uri Q1", "predicate uri Q2"]  
  }
 },
  
 "intent": [ list of actions ]
}

Here are some more notes:
- "entities" is a list of things mentioned in the question. Besides the primary name, alternate names, and well-known URIs. Also indicate the type of entity. Use classes from the ontology (included below) for types if possible. 
- "types" is a list of types referred to in the "entities" section. Provide alternate names and well-known URIs for types. Use classes from the ontology (included below) for types if possible. 
- "predicates" is a list of predicates and relationships. Include these only if the question asks about relationships between entities. If so, include the name, alternate names, and well-known URIs of each predicate. Use object properties from the ontology if possible. 
- "intent" is a list of actions where:

Where action is either:

[ "describe", "entity name A" ]

OR

[ "connect", "entity name A", "entity name B", "predicate P" ]

You may provide multiple actions under intent.

Examples of intent:

<question>
"Tell me about Ring or Jeff Bezos"
</question>

<intent>
"intent": [ ["describe", "Ring"], ["describe", "Jeff Bezos" ] ]
</intent>

<question>
"Did Amazon buy ACME or Ring"
</question>

<intent>
"intent": [ ["connect", "Amazon", "ACME", "buy"], ["connect", "Amazon", "Ring", "buy"] ]
</intent>


Respond ONLY with the JSON. Do not include any other text in the response.

"""

ANALYZE_ONTOLOGY_PROMPT="""
I have an ontology that describes classes and properties of things. Use the ontology when providing entity types, property types, and names. 

Here is the ontology in backticks:
""" + BACKTICKS + ONTOLOGY_CONTENT + BACKTICKS

ANALYZE_TAXONOMY_PROMPT="""
I have a taxonomy that provides a vocabulary for industries. Use the ontology when to provide alternate names. 

Here is the taxonomy in backticks:
""" + BACKTICKS + TAXONOMY_CONTENT + BACKTICKS

END_PROMPT="""

Question:
"""

SUMMARIZE_START_PROMPT="""
You are an expert AI assistant that excels in summarizing JSON data that contains information related to a user's question. Your task is to answer the question using only the JSON data provided. Do not rely on your own knowledge to answer the question.

Here is the JSON data in backticks:
    
"""



def get_psv_toks(content):
    toks=get_paragraph(content)
    if len(toks)==1:
        return toks[0].split("|")
    elif len(toks)==2:
        print(f"Ignore header line {toks[0]}")
        return toks[1].split("|")
    else:
        raise Exception(f"Invalid summary {content}")

def get_paragraph(content):
    return list(filter(lambda x : x != '', content.split("\n")))

def make_json(txt):
    while len(txt) > 0:
        try:
            return json.loads(txt)
        except Exception as error:
            #print("An exception occurred:", error) # An exception occurred: division by zero
            spl="\n".join(txt.split("\n")[1:])
            #print(spl)
            txt=spl

def call_qa_llm(bedrock_client, prompt):
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
    
    response = bedrock_client.invoke_model(body=body, modelId=MODELS['QA_MODEL'])
    response_body = json.loads(response.get('body').read())
    response_text = response_body.get('content')[0].get('text')
    return response_text
    
'''
Find alternate names and well-known URIs for a SINGLE candidate entity.
As a future enhancement, include my own ontology and taxonomy to give the LLM a vocab to work with.
In this demo, it can rely on public data from its corpus.
'''
def resolve_entity(bedrock_client, candidate):
    prompt=f"""
You are an expert AI assistant specializing in entity resolution. You will be presented with a piece of text designating an entity or event that I found in a press release. 

Your task is to respond with a list of up to 20 terms that are alternate names or well-known URIs (like a DBPedia URI) for the entity or event.

Format your response like this:

term|term|term

Do not provide any other explanatory text.

For example, if the input is Amazon, your response is similar to:

Amazon.com|AMZN|Amazon Inc.|http://dbpedia.org/resource/Amazon_(company)

<text>
{candidate}
</text>
    
    """
    
    return get_psv_toks(call_qa_llm(bedrock_client, prompt))

'''
The lone RAG function. Summarize based on context
'''
def summarize_graph_results(bedrock_client, question, results):
    prompt_parts = [SUMMARIZE_START_PROMPT]
    prompt_parts.append(BACKTICKS)
    prompt_parts.append(json.dumps(results, indent=4)) 
    prompt_parts.append(BACKTICKS)
    prompt_parts.append(END_PROMPT) 
    prompt_parts.append(question)
    
    prompt="\n".join(prompt_parts)
    
    # call the LLM
    ret_text=call_qa_llm(bedrock_client, prompt)
    return ret_text
    

'''
This is NOT a RAG use case. I will answer the question, NOT the LLM.
But I need help understanding the question. The LLM will tell me what the question is trying to say. It will "analyze" it (literally, "break it apart"). 
I can then use as a plan to answer it.
The idea is to extract entities (including types and alt names/URIs), as well as basic steps (describing an entity, connecting entities through a variable path, and running these through AND/OR/NOT logic.

I give the LLM help by providing my ontology and taxonomy.

Stuff that happens before I call this:
- I checked similar chunks.
- I did a Comprehend entity extraction. I'll compare that to what the LLM gave me.

My graph has Red, Yellow, Blue. This part hits only yellow and blue. The LLM needs to know classes, object properties. 
'''
def analyze_question(bedrock_client, question):
    prompt_parts = [ANALYZE_START_PROMPT]
    prompt_parts.append(ANALYZE_ONTOLOGY_PROMPT) 
    prompt_parts.append(ANALYZE_TAXONOMY_PROMPT) 
    prompt_parts.append(END_PROMPT) 
    prompt_parts.append(question)
    
    prompt="\n".join(prompt_parts)
    
    # call the LLM
    ret_text=call_qa_llm(bedrock_client, prompt)
    return make_json(ret_text)

def make_embedding(bedrock_client, content):
    native_request = {"inputText": content}
    request = json.dumps(native_request)
    response = bedrock_client.invoke_model(modelId=MODELS['EMBED_MODEL'], body=request)
    model_response = json.loads(response["body"].read())
    embedding = model_response["embedding"]
    return embedding

def extract_comprehend_entities_from_q(comprehend_client, q):
    response = comprehend_client.detect_entities(
        Text=q,
        LanguageCode='en'
    )
    return response
