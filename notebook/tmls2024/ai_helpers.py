import boto3
import json
from langchain.embeddings import BedrockEmbeddings

# Setup LLMs and bedrock client
# Modify this if you need
# Langchain needs 
# pip install -qU langchain-text-splitters langchain-community unstructured

QA_MODEL="anthropic.claude-3-sonnet-20240229-v1:0"
EMBED_MODEL="amazon.titan-embed-text-v1"

models={'QA_MODEL': QA_MODEL, 'EMBED_MODEL': EMBED_MODEL}
bedrock_client = boto3.client(service_name="bedrock-runtime")
bedrock_embeddings=BedrockEmbeddings(model_id=models['EMBED_MODEL'], client=bedrock_client)

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

def get_summary_paragraph(content):
    toks=get_paragraph(content)
    if len(toks)==1:
        return toks[0]
    elif len(toks)==2:
        print(f"Ignore header line {toks[0]}")
        return toks[1]
    else:
        raise Exception(f"Invalid summary {content}")
    
def resolve_entities(candidate):
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
    return get_psv_toks(response_text)

def extract_keywords(question):
    prompt=f"""
You are an expert AI assistant specializing in entity extraction. You will be presented with a piece of text.

Your task is to extract a list of up to 20 entities and concepts from the text. You must not use any prior knowledge or any of your training data.

Format your response like this:

entity|entity|entity

Do not provide any other explanatory text.

<text>
{question}
</text>
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
    return get_psv_toks(response_text)

def extract_triples(question):
    prompt=f"""
You are an expert AI assistant specializing in entity extraction. You will be presented with a piece of text.

Your task is to extract a list of up to 10 facts mentioned in the text. Express each fact as a triple in the form of subject, predicate, object. 

If possible, use types from my ontology to indicate triples. Here are types of subjects and objects:

:Industry rdf:type owl:Class ;
    rdfs:subClassOf :OrgEntity ;
    rdfs:label "industry" ; 
    skos:prefLabel "industry" .    

:Location rdf:type owl:Class ;
    rdfs:subClassOf :OrgEntity ;
    rdfs:label "location" ; 
    skos:prefLabel "location" .    

:Organization rdf:type owl:Class ;
    rdfs:subClassOf :OrgEntity ;
    rdfs:label "organization" ; 
    skos:prefLabel "organization" ;
    skos:altLabel "organisation", "org", "company", "firm" .

:Person rdf:type owl:Class ;
    rdfs:subClassOf :OrgEntity ;
    rdfs:label "person" ; 
    skos:prefLabel "person" ;
    skos:altLabel "leader", "executive" .

:Product rdf:type owl:Class ;
    rdfs:subClassOf :OrgEntity ;
    rdfs:label "product" ; 
    skos:prefLabel "product" .

:Service rdf:type owl:Class ;
    rdfs:subClassOf :OrgEntity ;
    rdfs:label "service" ; 
    skos:prefLabel "service" .
    
xent:LOCATION rdf:type owl:Class ;
    rdfs:subClassOf :ExtractedEntity ;
    rdfs:label "location"@en ;
    skos:prefLabel "location"@en ;
    skos:altLabel "place" .

xent:MONETARY_VALUE rdf:type owl:Class ;
    rdfs:subClassOf :ExtractedEntity ;
    rdfs:label "monetary value"@en ;
    skos:prefLabel "monetary value"@en ;
    skos:altLabel "money", "dollar value", "dollar" .

xent:ORGANIZATION rdf:type owl:Class ;
    rdfs:subClassOf :ExtractedEntity ;
    rdfs:label "organization"@en ;
    skos:prefLabel "organization"@en ;
    skos:altLabel "org", "firm", "company" .

xent:PERSON rdf:type owl:Class ;
    rdfs:subClassOf :ExtractedEntity ;
    rdfs:label "person"@en ;
    skos:prefLabel "person"@en ;
    skos:altLabel "person", "executive", "leader" .

xent:PERSON_TITLE rdf:type owl:Class ;
    rdfs:subClassOf :ExtractedEntity ;
    rdfs:label "person title"@en ;
    skos:prefLabel "person title"@en ;
    skos:altLabel "title", "job", "role", "position" .

xent:QUANTITY rdf:type owl:Class ;
    rdfs:subClassOf :ExtractedEntity ;
    rdfs:label "quantity"@en ;
    skos:prefLabel "quantity"@en ;
    skos:altLabel "amount" .

xent:RIGHTS_ISSUE rdf:type owl:Class ;
    rdfs:subClassOf :ExtractedEntity ;
    rdfs:label "rights issue"@en ;
    skos:prefLabel "rights issue"@en ;
    skos:altLabel "issue", "right" .

xent:SECONDARY_OFFERING rdf:type owl:Class ;
    rdfs:subClassOf :ExtractedEntity ;
    rdfs:label "secondary offering"@en ;
    skos:prefLabel "secondary offering"@en ;
    skos:altLabel "offer", "offering" .

xent:SHELF_OFFERING rdf:type owl:Class ;
    rdfs:subClassOf :ExtractedEntity ;
    rdfs:label "shelf offering"@en ;
    skos:prefLabel "shelf offering"@en ;
    skos:altLabel "offer", "offering", "shelf" .

xent:STOCK_CODE rdf:type owl:Class ;
    rdfs:subClassOf :ExtractedEntity ;
    rdfs:label "stock code"@en ;
    skos:prefLabel "stock code"@en ;
    skos:altLabel "ticker" .

xent:STOCK_SPLIT rdf:type owl:Class ;
    rdfs:subClassOf :ExtractedEntity ;
    rdfs:label "stock split"@en ;
    skos:prefLabel "stock split"@en .
    
Here are types of predicates:

:hasIndustry rdf:type owl:ObjectProperty ;
    rdfs:subPropertyOf owl:topObjectProperty ;
    rdfs:range :Industry .

:hasKeyPerson rdf:type owl:ObjectProperty ;
    rdfs:subPropertyOf owl:topObjectProperty ;
    rdfs:domain :Organization ;
    rdfs:range :Product .

:hasLocation rdf:type owl:ObjectProperty ;
    rdfs:subPropertyOf owl:topObjectProperty ;
    rdfs:range :Location .

:hasParentOrg rdf:type owl:ObjectProperty ;
    rdfs:subPropertyOf owl:topObjectProperty ;
    rdfs:domain :Organization ;
    rdfs:range :Organization .

:subsidiaryOf rdf:type owl:ObjectProperty ;
    rdfs:subPropertyOf owl:topObjectProperty ;
    rdfs:domain :Organization ;
    rdfs:range :Organization ;
    rdfs:label "subsidiary" ;
    skos:prefLabel "subsidiary" .

:hasProduct rdf:type owl:ObjectProperty ;
    rdfs:subPropertyOf owl:topObjectProperty ;
    rdfs:range :Product .

:hasService rdf:type owl:ObjectProperty ;
    rdfs:subPropertyOf owl:topObjectProperty ;
    rdfs:range :Service .
    
xev:BANKRUPTCY rdf:type owl:Class ;
    rdfs:subClassOf :ExtractedEvent ;
    rdfs:label "bankruptcy"@en ;
    skos:prefLabel "bankruptcy"@en .

xev:CORPORATE_ACQUISTION rdf:type owl:Class ;
    rdfs:subClassOf :ExtractedEvent ;
    rdfs:label "corporate acquisition"@en ;
    skos:prefLabel "corporate acquisition"@en ;
    skos:altLabel "deal", "merger", "takeover" .

xev:CORPORATE_MERGER rdf:type owl:Class ;
    rdfs:subClassOf :ExtractedEvent ;
    rdfs:label "corporate merger"@en ;
    skos:prefLabel "corporate merger"@en ;
    skos:altLabel "deal", "merger", "takeover", "acqusition" .

xev:DATE rdf:type owl:Class ;
    rdfs:subClassOf :ExtractedEvent ;
    rdfs:label "date"@en ;
    skos:prefLabel "date"@en .

xev:EMPLOYMENT rdf:type owl:Class ;
    rdfs:subClassOf :ExtractedEvent ;
    rdfs:label "employment"@en ;
    skos:prefLabel "employment"@en .

xev:FACILITY rdf:type owl:Class ;
    rdfs:subClassOf :ExtractedEvent ;
    rdfs:label "facility"@en ;
    skos:prefLabel "facility"@en ;
    skos:altLabel "plant", "warehouse", "distribution center", "fulfillment center" .

xev:INVESTMENT_GENERAL rdf:type owl:Class ;
    rdfs:subClassOf :ExtractedEvent ;
    rdfs:label "investment"@en ;
    skos:prefLabel "investment"@en .

xev:IPO rdf:type owl:Class ;
    rdfs:subClassOf :ExtractedEvent ;
    rdfs:label "IPO"@en ;
    skos:prefLabel "IPO"@en ;
    skos:altLabel "initial public offering" .

xev:TENDER_OFFERING rdf:type owl:Class ;
    rdfs:subClassOf :ExtractedEvent ;
    rdfs:label "tender offering"@en ;
    skos:prefLabel "tender offering"@en ;
    skos:altLabel "tender", "offer" .

You must not use any prior knowledge or any of your training data.

Format your response with a triple on each line. A single line looks like this:

subject|subjectTypes (comma-separated)|predicate|subjectTypes (comma-separated)|object|objectTypes (comma-separated)

Do not provide any other explanatory text.

<text>
{question}
</text>
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
    return get_psv_toks(response_text)


def make_embedding(content):
    embedding=bedrock_embeddings.embed_documents([content])[0]
    return embedding
