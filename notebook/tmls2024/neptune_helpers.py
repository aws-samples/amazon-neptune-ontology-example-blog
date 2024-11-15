import os
import requests
import json
import boto3
from botocore.exceptions import ClientError
from botocore.awsrequest import AWSRequest
from botocore.auth import SigV4Auth

CONN_AWS_REGION="AWS_REGION"
CONN_USE_IAM_AUTH="USE_IAM_AUTH"
CONN_NEPTUNE_ENDPOINT="CONN_NEPTUNE_ENDPOINT"
CONN_GRAPH_IDENTIFIER="CONN_GRAPH_IDENTIFIER"

def execute_oc_na(na_client, conn, query, params):
    ret= na_client.execute_query(
        graphIdentifier=conn[CONN_GRAPH_IDENTIFIER],
        queryString=query,
        language='OPEN_CYPHER',
        parameters=params)
    return json.loads(ret["payload"].read().decode("UTF-8"))["results"]

def execute_sparql(session, conn, query):
    request_data = {"query": query}
    data = request_data
    request_hdr = None

    if conn[CONN_USE_IAM_AUTH]:
        credentials = session.get_credentials()
        credentials = credentials.get_frozen_credentials()
        access_key = credentials.access_key
        secret_key = credentials.secret_key
        service = "neptune-db"
        session_token = credentials.token
        params = None
        creds = SimpleNamespace(
            access_key=access_key,
            secret_key=secret_key,
            token=session_token,
            region=conn[CONN_AWS_REGION]
        )
        request = AWSRequest(
            method="POST", url=conn[CONN_NEPTUNE_ENDPOINT], data=data, params=params
        )
        SigV4Auth(creds, service, conn[CONN_AWS_REGION]).add_auth(request)
        request.headers["Content-Type"] = "application/x-www-form-urlencoded"
        request_hdr = request.headers
    else:
        request_hdr = {}
        request_hdr["Content-Type"] = "application/x-www-form-urlencoded"

    response = requests.request(
        method="POST", url= conn[CONN_NEPTUNE_ENDPOINT], headers=request_hdr, data=data
    )
    if str(response.status_code) != "200":
        print(f"Query error {response.status_code} {response.text}")
        print(f"Here is the query:\n{query}\n")
        print(f"Here is the result:\n{response.text}\n")
        raise Exception({response.status_code, response.text})

    try:
        json_resp = json.loads(response.text)
        return json_resp
    except Exception as e:
        print("Exception: {}".format(type(e).__name__))
        print("Exception message: {}".format(e))
        print(f"Here is the query:\n{query}\n")
        print(f"Here is the result:\n{response.text}\n")
        raise e
        
def make_select_table(ret):
    return ret['results']['bindings']

def describe(session, conn, uri, describe_limit=200):
    query = f"""
PREFIX : <http://example.org/orgdemo/> 
PREFIX skos:  <http://www.w3.org/2004/02/skos/core#>
PREFIX dc: <http://purl.org/dc/elements/1.1/> 

SELECT ?uri ?cat ?p ?o ?direction 
(GROUP_CONCAT(distinct ?pLabel;SEPARATOR="|") AS ?pLabels)
(GROUP_CONCAT(distinct ?type;SEPARATOR="|") AS ?types)
(GROUP_CONCAT(distinct ?typeLabel;SEPARATOR="|") AS ?typeLabels)
(GROUP_CONCAT(distinct ?typeSuperClass;SEPARATOR="|") AS ?typeSuperClasses)
(GROUP_CONCAT(distinct ?label;SEPARATOR="|") AS ?labels)
(GROUP_CONCAT(distinct ?uriSuperClass;SEPARATOR="|") AS ?uriSuperClasses)
(GROUP_CONCAT(distinct ?uriSuperProperty;SEPARATOR="|") AS ?uriSuperProperties)
WHERE {{
   BIND (<{uri}> as ?uri).
   
   {{
       {{ ?uri ?p ?o . BIND ("out" as ?direction) . }} 
       UNION
       {{ ?o ?p ?uri . BIND ("in" as ?direction) . }} 
   }} .
   OPTIONAL {{ ?p skos:prefLabel|skos:altLabel|:suggestedLabel|rdfs:label ?pLabel }} . 
   OPTIONAL {{ ?uri a ?type . 
             OPTIONAL {{ ?type rdfs:subClassOf+ ?typeSuperClass }} .
             OPTIONAL {{ ?type skos:prefLabel|skos:altLabel|:suggestedLabel|rdfs:label ?typeLabel }} .
   }} . 
   OPTIONAL {{ ?uri skos:prefLabel|skos:altLabel|:suggestedLabel|rdfs:label ?label }} . 
   OPTIONAL {{ ?uri rdfs:subClassOf+ ?uriSuperClass }} .
   OPTIONAL {{ ?uri rdfs:subPropertyOf+ ?uriSuperProperty }} .
    
   OPTIONAL {{ ?uri a skos:Concept . BIND ( "concept" as ?cat ) . }}
   OPTIONAL {{ ?uri a owl:Class . BIND ( "class" as ?cat ) . }}
   OPTIONAL {{ ?uri a owl:ObjectProperty . BIND ( "rel" as ?cat ) . }}
   OPTIONAL {{ ?uri a :Document . BIND ( "document" as ?cat ) . }}
   OPTIONAL {{ 
       ?uri rdf:type/rdfs:subClassOf+ :ExtractedEntity . 
       BIND ( "yellow-entity" as ?cat ) .
    }}
   OPTIONAL {{ 
       ?uri rdf:type/rdfs:subClassOf+ :ExtractedEvent . 
       BIND ( "yellow-event" as ?cat ) . 
    }}
}}
GROUP BY ?uri ?cat ?p ?o ?direction
LIMIT {describe_limit}
"""
    return execute_sparql(session, conn, query)

# Find resources with name as part of their labels
# See also aos_helpers.find_entities_by_label()
def find_resource_by_name(session, conn, name):
    
    names_string=f' "{name}" "{name}"@en ' 
        
    query = f"""
PREFIX : <http://example.org/orgdemo/> 
PREFIX skos:  <http://www.w3.org/2004/02/skos/core#>

select * where {{
    VALUES ?name {{ {names_string} }} .
    ?s skos:prefLabel|skos:altLabel|:suggestedLabel|rdfs:label ?name . 
    OPTIONAL {{ ?s rdf:type* ?type }} .
    OPTIONAL {{ ?s rdfs:subClassOf* ?sclass }} .
    OPTIONAL {{ ?type rdfs:subClassOf* ?typeclass }} .
    OPTIONAL {{ ?s rdfs:subPropertyOf* ?sproperty }} .
    OPTIONAL {{ ?resWithConcept :hasConcept ?s }} .
    OPTIONAL {{ ?resWithSeeAlso rdfs:seeAlso ?s }} .
}}
ORDER BY ?name ?s    """
    return execute_sparql(session, conn, query)
 
def connect_resources(na_client, conn, res1_list, res2_list, path_limit=20):
    
    params={'res1_list': list(map(lambda a: "<" + a + ">", res1_list)), 'res2_list': list(map(lambda a: "<" + a + ">", res2_list))}
    query = f"""
MATCH path=(a)-[*0..5]-(b)
WHERE id(a) in $res1_list
and id(b) in $res2_list
RETURN path
LIMIT {path_limit}
    """
    return execute_oc_na(na_client, conn, query, params)
