import json
from types import SimpleNamespace
from typing import Optional

import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

#  Keep track of Neptune environment for query
NEPTUNE_ENV = {'host': None, 'port': None, 'region': None, 'use_iam_auth': False, 'session': None}
def set_neptune_env(host, port=8182, use_iam_auth=False, region=''):
    NEPTUNE_ENV['endpoint']=f"https://{host}:{port}/sparql" 
    NEPTUNE_ENV['region']=region
    NEPTUNE_ENV['use_iam_auth']=use_iam_auth
    NEPTUNE_ENV['session']= boto3.Session() 

    client_params = {}
    client_params["region_name"] = region
    client_params["endpoint_url"] = f"https://{host}:{port}"
    NEPTUNE_ENV['client'] = NEPTUNE_ENV['session'].client('neptunedata', **client_params)

def execute_oc_query(query):
    return NEPTUNE_ENV['client'].execute_open_cypher_query(openCypherQuery=query)['results']

# discover the schema. It uses summary API result, so pass that as input.
# see notebook or how to obtain it
def discover(pgsummary):
    classes={}
    rel_classes={}
    SAMPLE_LIMIT=10000
    RESULT_LIMIT=200

    def _map_type(typ):
        if str(typ) == "<class 'int'>":
            return "int"
        if str(typ) == "<class 'float'>":
            return "float"
        if str(typ) == "<class 'bool'>":
            return "boolean"
        if str(typ) == "<class 'str'>":
            return "string"
        return "string"

    def _determine_type(prop, val):
        typ = type(val)
        if typ is list:
            prop['multival'] = True
            for v in list(val):
                mtyp = _map_type(type(v))
                if not(mtyp in prop['types']):
                    prop['types'].append(mtyp)
        else:
            mtyp = _map_type(typ)
            if not (mtyp in prop['types']):
                prop['types'].append(mtyp)

    for n in pgsummary['payload']['graphSummary']['nodeLabels']:
        print(n)
        classes[n] = {'labels': [], 'props': {}, 'rels': {}}

        # node props
        structure_query = f"MATCH(n:{n}) RETURN properties(n) as props LIMIT {SAMPLE_LIMIT}"  
        df = execute_oc_query(structure_query)
        for row in df:
            props = row['props']
            for p in props:
                if not(p in classes[n]['props']):
                    classes[n]['props'][p] = {'multival': False, 'types': []}
                _determine_type(classes[n]['props'][p], props[p])

        # edges
        structure_query = f"MATCH(n:{n})-[e]->(m) WITH type(e) AS edgetype, labels(m) AS target LIMIT {SAMPLE_LIMIT} RETURN distinct edgetype, target LIMIT {RESULT_LIMIT}"
        df = execute_oc_query(structure_query)
        for row in df:
            edge_type = row['edgetype']
            target = row['target']
            if not(edge_type in classes[n]['rels']):
                classes[n]['rels'][edge_type] = target

        # edge properties when that node is source
        structure_query = f"MATCH(n:{n})-[e]->(m) RETURN type(e) as edgetype, properties(e) as props LIMIT {SAMPLE_LIMIT}" 
        df = execute_oc_query(structure_query)
        for row in df:
            edge_type = row['edgetype']
            props = row['props']
            if len(props) > 0:
                rel_class = {'props': {}}
                if edge_type in rel_classes:
                    rel_class = rel_classes[edge_type]
                else:
                    rel_classes[edge_type] = rel_class
                for p in props:
                    if not(p in rel_classes[edge_type]['props']):
                        rel_classes[edge_type]['props'][p] = {'multival': False, 'types': []}
                    _determine_type(rel_classes[edge_type]['props'][p], props[p])

    return [classes, rel_classes]


def to_plant_uml(observation, class_filter=None, max_classes=-1, max_rels=-1):

    classes_str = ""
    rels_str = ""

    classes = observation[0]
    rel_classes = observation[1]

    def _print_type(t):
        s = t['types'][0]
        if t['multival']:
            s += "*"
        if len(t['types']) > 1:
            s += f(" also t['types'][1:]")
        return s

    num_classes = 0
    num_rels = 0
    
    for c in classes:
        if not(class_filter is None) and not (c in class_filter):
            continue

        # max classes?
        num_classes += 1
        if max_classes >=0 and num_classes > max_classes:
            print("Max classes. Stopping.")
            break
            
        classstr = f"\nclass {c} {{"
        for p in classes[c]['props']:
            classstr += f"\n   - {p}:{_print_type(classes[c]['props'][p])}"

        for r in classes[c]['rels']:
            num_rels += 1
            if max_rels >=0 and num_rels > max_rels:
                print(f"Max rels reached. Skipping {r} of {c}")
                break
            
            for target in classes[c]['rels'][r]:
                rels_str += f'\n{c} "1" -- "*" {target} : {r} > '

            if r in rel_classes:
                propstr = ""
                for rp in rel_classes[r]['props']:
                    propstr += f"{rp}:{_print_type(rel_classes[r]['props'][rp])} "
                rels_str += f"\nnote on link : {propstr}"


        classstr += "\n}"
        classes_str += classstr

    plantspec = f"""
@startuml

{classes_str}

{rels_str}

@enduml
    """

    return plantspec


