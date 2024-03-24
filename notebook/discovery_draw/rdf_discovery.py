import json
from types import SimpleNamespace
from typing import Optional

import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

#  Keep track of Neptune environment for query
NEPTUNE_ENV = {'endpoint': None, 'region': None, 'use_iam_auth': False, 'session': None}
def set_neptune_env(host, port=8182, use_iam_auth=False, region=''):
    NEPTUNE_ENV['endpoint']=f"https://{host}:{port}/sparql" 
    NEPTUNE_ENV['region']=region
    NEPTUNE_ENV['use_iam_auth']=use_iam_auth
    NEPTUNE_ENV['session']= boto3.Session() if use_iam_auth else None
 
# make SPARQL query of crud_type query or update on Neptune
def execute_sparql(query, crud_type='query'):
    request_data = {crud_type: query}
    data = request_data
    request_hdr = None

    if NEPTUNE_ENV['use_iam_auth']:
        credentials = NEPTUNE_ENV['session'].get_credentials()
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
            region=NEPTUNE_ENV['region']
        )
        request = AWSRequest(
            method="POST", url=NEPTUNE_ENV['endpoint'], data=data, params=params
        )
        SigV4Auth(creds, service, NEPTUNE_ENV['region']).add_auth(request)
        request.headers["Content-Type"] = "application/x-www-form-urlencoded"
        request_hdr = request.headers
    else:
        request_hdr = {}
        request_hdr["Content-Type"] = "application/x-www-form-urlencoded"

    queryres = requests.request(
        method="POST", url=NEPTUNE_ENV['endpoint'], headers=request_hdr, data=data
    )
    if str(queryres.status_code) != "200":
        print(f"Query error {queryres.status_code} {queryres.text}")
        print(f"Here is the query:\n{query}\n")
        print(f"CRUD type is *{crud_type}*")
        print(f"Here is the result:\n{queryres.text}\n")
        raise Exception({queryres.status_code, queryres.text})

    try:
        json_resp = json.loads(queryres.text)    
        if 'results' in json_resp:
            return json_resp['results']['bindings']
        else:
            return json_resp
    except Exception as e:
        print("Exception: {}".format(type(e).__name__))
        print("Exception message: {}".format(e))
        print(f"Here is the query:\n{query}\n")
        print(f"CRUD type is *{crud_type}*")
        print(f"Here is the result:\n{queryres.text}\n")
        raise e

# Run SPARQL select query on Neptune        
def execute_sparql_query(query):
    return execute_sparql(query, "query")  

'''
Observational query support.
This block contains queries to discover instances.
'''  

MAX_PROPS=1000
MAX_RESOURCE_SAMPLE=500
BAG_1TON = "{ rdfs:_1 rdfs:_2 rdfs:_3 rdfs:_4 rdfs:_5 } "

'''
Get properties of given *clazz*. 
This is a template for other queries. 
Pass in *check* and *project* to influence what is returned. 
'''
def _make_prop_query_template(clazz, check, project):
    return f'''
SELECT distinct {project} WHERE {{

    # select some resources of this type
    {{
        SELECT ?resource WHERE {{
            BIND  (<{clazz}> as ?type ) .
            ?resource a ?type .
        }}
        LIMIT {MAX_RESOURCE_SAMPLE}
    }}
    
    {check}
    
    #
    # object types
    #
    
    # literal
    BIND(DATATYPE(?obj) as ?litType) .   
    
    # object type
    OPTIONAL {{ 
        ?obj a ?objType .
    }}
    
    # List
    OPTIONAL {{       
        ?obj rdf:rest*/rdf:first ?val .
        BIND (DATATYPE(?val) as ?valLitType) .
        OPTIONAL {{
            ?val a ?valType .
        }}
    }}

    # Bag, Sq, Alt, Container
    OPTIONAL {{       
        VALUES ?objType {{ rdf:Bag rdf:Seq rdf:Alt rdf:Container }} .
        VALUES ?index {BAG_1TON} .
        ?obj ?index ?val .
        BIND (DATATYPE(?val) as ?valLitType) .
        OPTIONAL {{
            ?val a ?valType .
        }}
    }}
}}   
LIMIT {MAX_PROPS}
'''

'''
Get properties of given class, including property type. 
'''
def _make_prop_query(clazz):
    return _make_prop_query_template(clazz, """
?resource ?prop ?obj .
OPTIONAL {
    ?prop rdf:singletonPropertyOf ?sprop .
}
    """, "?prop ?sprop ?objType ?litType ?valType ?valLitType")

'''
For properties of *clazz* that have metadata, return those metadata properties and their types.
In this function we consider the Named Graph approach. 
In this approach, to define metadata of triple :S :P :O, we put :S :P :O in a named graph :G.
We then define metadata triples :G :MP :MO, where :MP is a metadata predicate and :MO the metadata object.
'''
def _make_metadata_ng_query(clazz):
    return _make_prop_query_template(clazz, """
GRAPH ?graph { ?resource ?prop ?_ . } .
?graph ?metaprop ?obj .
""", "?prop ?sprop ?metaprop ?objType ?litType ?valType ?valLitType")

'''
For properties of *clazz* that have metadata, return those metadata properties and their types.
In this function we consider the Singleton approach. 
In this approach, to define metadata of triple :S :P :O, we actually write :S :P{i} :O,
where :P{i} rdf:singletonPropertyOf :P. 
We then define metadata triples :P{i} :MP :MO, where :MP is a metadata predicate and :MO the metadata object.
'''
def _make_metadata_singleton_query(clazz):
    return _make_prop_query_template(clazz, """
?resource ?prop ?_ .
?prop rdf:singletonPropertyOf ?sprop .
?prop ?metaprop ?obj .
""",  "?prop ?sprop ?metaprop ?objType ?litType ?valType ?valLitType")

'''
Standard reification is a modeling approach that provides a third alternative to attach metadata 
to a statement. Instead of writing :S :P :O, we write:

:S{i} a rdf:Statement .
:S{i} rdf:subject :S .
:S{i} rdf:predicate :P .
:S{i} rdf:object :O .
:S{i} :MP :MO .
.. and more metadata if needed ..

:MP is a metadata predicate and :MO the metadata object.

For our objective, we want to arrange these statements in class/property structure.
This query helps us do that.
'''
def _make_stmt_query(clazz, prop):
    return f'''
SELECT distinct ?prop ?metaprop 
    ?litType ?objType ?valLitType ?valType  
    ?metaLitType ?metaObjType ?metaValLitType ?metaValType  
WHERE {{

    # select some statements of this type
    {{
        SELECT ?prop ?obj ?metaprop ?mobj WHERE {{
            ?stmt a rdf:Statement .
            ?stmt rdf:subject ?resource .
            ?resource a <{clazz}> .
            BIND  (<{prop}> as ?prop ) .
            ?stmt rdf:predicate ?prop .
            ?stmt rdf:object ?obj . 
            ?stmt ?metaprop ?mobj .
            FILTER (?metaprop != rdf:subject ) .
            FILTER (?metaprop != rdf:predicate ) .
            FILTER (?metaprop != rdf:object ) .
            FILTER (?metaprop != rdf:type ) .
        }}
        LIMIT {MAX_RESOURCE_SAMPLE}
    }}

    # object types    
    # literal
    BIND(DATATYPE(?obj) as ?litType) .   
    
    # object type
    OPTIONAL {{ 
        ?obj a ?objType .
    }}
    
    # List
    OPTIONAL {{      
        ?obj rdf:rest*/rdf:first ?val .
        BIND (DATATYPE(?val) as ?valLitType) .
        OPTIONAL {{
            ?val a ?valType .
        }}
    }}

    # Bag, Sq, Alt, Container
    OPTIONAL {{     
        VALUES ?objType {{ rdf:Bag rdf:Seq rdf:Alt rdf:Container }} .
        VALUES ?index {BAG_1TON} .
        ?obj ?index ?val .
        BIND (DATATYPE(?val) as ?valLitType) .
        OPTIONAL {{
            ?val a ?valType .
        }}
    }}
    # object types    
    # literal
    BIND(DATATYPE(?mobj) as ?metaLitType) .   
    
    # object type
    OPTIONAL {{ 
        ?mobj a ?metaObjType .
    }}
    
    # List
    OPTIONAL {{       
        ?mobj rdf:rest*/rdf:first ?metaVal .
        BIND (DATATYPE(?metaVal) as ?metaValLitType) .
        OPTIONAL {{
            ?metaVal a ?metaValType .
        }}
    }}

    # Bag, Sq, Alt, Container
    OPTIONAL {{      
        VALUES ?metaObjType {{ rdf:Bag rdf:Seq rdf:Alt rdf:Container }} .
        VALUES ?mindex {BAG_1TON} .
        ?mobj ?mindex ?metaVal .
        BIND (DATATYPE(?metaVal) as ?metaValLitType) .
        OPTIONAL {{
            ?metaVal a ?metaValType .
        }}
    }}
}}
LIMIT {MAX_PROPS}
'''

# the columns that come back from SPARQL queries
COLS = ["type", "prop", "sprop", "metaprop", "objType", "litType", "valType", "valLitType", \
    "metaLitType", "metaObjType", "metaValLitType", "metaValType"]  

def discover_observational(rdf_summary):
    
    # from result row, return values for given COLS names.
    def _get_cols(prop_res):
        col_vals = {}
        for c in COLS:
            if c in prop_res:
                col_vals[c] = prop_res[c]['value'] 
        return col_vals
     
    # create or update a property entry with the results of a query.
    # contents of a property entry include types and stereotypes
    # determine flag can be set to False if you are just finding that entry while handling meta prop
    def _get_entry(props, col_vals, determine=True):
        model_prop_name = col_vals['sprop'] if 'sprop' in col_vals else col_vals['prop']
        
        prop_entry = None
        if model_prop_name in props:
            prop_entry = props[model_prop_name]
        else:
            prop_entry = {'lits': [], 'rels': [], 
                'isSingleton': 'sprop' in col_vals, 
                'isList': False,
                'metaprops': {}
            }
            props[model_prop_name] = prop_entry
        if determine:
            _determine_type(col_vals, prop_entry, False)
        return prop_entry

    def _get_meta_entry(props, col_vals, meta_naming):
        prop_entry = _get_entry(props, col_vals, False)
        meta_prop_name = col_vals['metaprop']
        meta_entry = None
        if meta_prop_name in prop_entry['metaprops']:
            meta_entry = prop_entry['metaprops'][meta_prop_name]
        else:
            meta_entry = {'lits': [], 'rels': [], 
                'isList': False
            }
            prop_entry['metaprops'][meta_prop_name] = meta_entry
        _determine_type(col_vals, meta_entry, meta_naming)
        return meta_entry

    NAMING=['litType', 'valLitType', 'objType', 'valType']
    META_NAME=['metaLitType', 'metaValLitType', 'metaObjType', 'metaValType']
    def _determine_type(col_vals, entry, meta_naming):
        naming = META_NAME if meta_naming else NAMING
        def append_type(res_key, entry_key):
            added = False
            if res_key in col_vals and not(col_vals[res_key] in entry[entry_key]):
                added = True
                entry[entry_key].append(col_vals[res_key])
            return added
                
        append_type(naming[0], 'lits')
        if append_type(naming[1], 'lits'):
            entry['isList'] = True
        append_type(naming[2], 'rels')
        if append_type(naming[3], 'rels'):
            entry['isList'] = True    
            
    # classes and their props
    summary_classes = []
    for c in rdf_summary['payload']['graphSummary']['classes']:
        if not(c.startswith("http://www.w3.org/1999/02/22-rdf-syntax-ns#" ) or \
               c.startswith("http://www.w3.org/2000/01/rdf-schema#") or \
               c.startswith("http://www.w3.org/2002/07/owl#") or \
               c.startswith("http://www.w3.org/2001/XMLSchema#") or \
               c.startswith("http://www.w3.org/ns/json-ld#") or \
               c.startswith("http://purl.org/dc/elements/1.1/") or \
               c.startswith("http://xmlns.com/foaf/0.1/") or \
               c.startswith("http://www.w3.org/2004/02/skos/core#") or \
               c.startswith("http://www.w3.org/2008/05/skos-xl#")):
            summary_classes.append(c)

    # I won't use these for now. Could constrain prop queries by preds from summary, 
    # but seems ok without it.
    summary_predicates = []
    for p in rdf_summary['payload']['graphSummary']['predicates']:
        for pn in p:
            summary_predicates.append(pn)
    
    classes = {}
    for clazz in summary_classes:
        print(clazz)            
        classes[clazz]={'props':{}}
        
        prop_res = execute_sparql_query(_make_prop_query(clazz))
        for prop in prop_res:
            col_vals = _get_cols(prop)
            prop_entry = _get_entry(classes[clazz]['props'], col_vals)
            
        meta_res = execute_sparql_query(_make_metadata_ng_query(clazz))
        for prop in meta_res:
            col_vals = _get_cols(prop)
            prop_entry = _get_entry(classes[clazz]['props'], col_vals, False)
            meta_entry = _get_meta_entry(classes[clazz]['props'], col_vals, False)
            meta_entry['entryType']='namedgraph'

        meta_res = execute_sparql_query(_make_metadata_singleton_query(clazz))
        for prop in meta_res:
            col_vals = _get_cols(prop)
            prop_entry = _get_entry(classes[clazz]['props'], col_vals, False)
            meta_entry = _get_meta_entry(classes[clazz]['props'], col_vals, False)
            meta_entry['entryType']='singleton'
            
        # Special statement processing
        # Here, check one per prop
        for prop in classes[clazz]['props']:
            stmt_res = execute_sparql_query(_make_stmt_query(clazz, prop))
            for row in stmt_res:
                col_vals = _get_cols(row)
                if not(clazz in classes):
                    classes[clazz] = {'props':{}}
                classes[clazz]['isStatement']=True
                prop_entry = _get_entry(classes[clazz]['props'], col_vals)
                meta_entry = _get_meta_entry(classes[clazz]['props'], col_vals, True)
                meta_entry['entryType']='statement'

    return classes

'''
This part merges ontology with observational.

We use the approach from the blog post 
https://aws.amazon.com/blogs/database/model-driven-graphs-using-owl-in-amazon-neptune/

The notebook used in that post is 
https://github.com/aws-samples/amazon-neptune-ontology-example-blog/blob/main/notebook/Neptune_Ontology_Example.ipynb
'''

# check if uri is bnode or not
def _is_bnode(uri):
    return uri.startswith("b")

def _discover_ont():

    # check if list contains the val
    def _list_has_value(list, val):
        try:
            list.index(val)
            return True
        except ValueError:
            return False

    # Out of scope OWL stuff for this example: 
    # AllDisjointClases, disjointUnionOf
    # assertions - same/diff ind, obj/data prop assertion, neg obj/data prop assertion
    # annotations
    # top/bottom property
    # restriction onProperties;
    #   but restriction onProperty IS supported  
    # cardinality
    #   but will consider FunctionalProperty
    # Datatype and data ranges
    
    # Limitation: for datatype properties, consider only strings.
    
    ONT_CLASS_QUERY = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

select ?class 
    (GROUP_CONCAT(distinct ?subOf;SEPARATOR=",") AS ?subsOf)
    (GROUP_CONCAT(distinct ?equiv;SEPARATOR=",") AS ?equivs)
    (GROUP_CONCAT(distinct ?complement;SEPARATOR=",") AS ?complements) 
    (GROUP_CONCAT(distinct ?keyList;SEPARATOR=",") AS ?keys) 
    (GROUP_CONCAT(distinct ?kentry;SEPARATOR=",") AS ?keyEntries) 
    (GROUP_CONCAT(distinct ?uList;SEPARATOR=",") AS ?unions) 
    (GROUP_CONCAT(distinct ?iList;SEPARATOR=",") AS ?intersections) 
    (GROUP_CONCAT(distinct ?ientry;SEPARATOR=",") AS ?intersectionEntries) 
    (GROUP_CONCAT(distinct ?oneList;SEPARATOR=",") AS ?oneOfs) 
    (GROUP_CONCAT(distinct ?disj;SEPARATOR=",") AS ?disjoints) 
    where { 
    ?class rdf:type owl:Class .
    OPTIONAL { ?class rdfs:subClassOf+ ?subOf . } .
    OPTIONAL { ?class owl:equivalentClass+ ?equiv . } .
    OPTIONAL { ?class owl:complementOf ?complement . } .
    OPTIONAL { ?class owl:hasKey ?keyList . } .
    OPTIONAL { ?class owl:hasKey ?kl . ?kl rdf:rest*/rdf:first ?kentry . } .
    OPTIONAL { ?class owl:unionOf ?uList . } . 
    OPTIONAL { ?class owl:intersectionOf ?iList . } . 
    OPTIONAL { ?class owl:intersectionOf ?il . ?il rdf:rest*/rdf:first ?ientry . } .
    OPTIONAL { ?class owl:oneOf ?oneList . } .
    OPTIONAL { ?class owl:disjointWith ?disj . } . 
} group by ?class
LIMIT 200
    """

    ONT_PROP_QUERY = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

select ?prop 
    (GROUP_CONCAT(distinct ?subPropOf;SEPARATOR=",") AS ?subsOf)  
    (GROUP_CONCAT(distinct ?equiv;SEPARATOR=",") AS ?equivs)  
    (GROUP_CONCAT(distinct ?domain;SEPARATOR=",") AS ?domains)  
    (GROUP_CONCAT(distinct ?du;SEPARATOR=",") AS ?domainUs)  
    (GROUP_CONCAT(distinct ?range;SEPARATOR=",") AS ?ranges)  
    (GROUP_CONCAT(distinct ?ru;SEPARATOR=",") AS ?rangeUs)  
    (GROUP_CONCAT(distinct ?disj;SEPARATOR=",") AS ?disjoints)  
    (GROUP_CONCAT(distinct ?inv;SEPARATOR=",") AS ?inverses)  
    (GROUP_CONCAT(distinct ?type;SEPARATOR=",") AS ?types)  
    where {

    { ?prop rdf:type rdf:Property . }
    UNION
    { ?prop rdf:type owl:ObjectProperty . }
    UNION
    { ?prop rdf:type owl:DatatypeProperty . } .
    OPTIONAL { ?prop rdfs:subPropertyOf+ ?subPropOf . } .
    OPTIONAL { ?prop rdfs:equivalentProperty+ ?equiv . } .
    OPTIONAL { ?prop rdfs:domain ?domain } .
    OPTIONAL { ?prop rdfs:domain/owl:unionOf ?u . ?u rdf:rest*/rdf:first ?du . } .
    OPTIONAL { ?prop rdfs:range ?range } .
    OPTIONAL { ?prop rdfs:range/owl:unionOf ?u1 . ?u1 rdf:rest*/rdf:first ?ru . } .
    OPTIONAL { ?prop owl:propertyDisjointWith ?disj . } . 
    OPTIONAL { { ?prop owl:inverseOf ?inv }  UNION { ?inv owl:inverseOf ?prop } } . 
    ?prop rdf:type ?type . # allows us to check functional, transitive, etc
} 
group by ?prop
LIMIT 200

    """

    ONT_RESTRICTION_QUERY ="""
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

select ?restriction ?prop  
    (GROUP_CONCAT(distinct ?allClass;SEPARATOR=",") AS ?allFromClasses)
    (GROUP_CONCAT(distinct ?someClass;SEPARATOR=",") AS ?someFromClasses)
    (GROUP_CONCAT(distinct ?lval;SEPARATOR=",") AS ?lvals) 
    (GROUP_CONCAT(distinct ?ival;SEPARATOR=",") AS ?ivals) 
    where { 
    ?restriction rdf:type owl:Restriction .
    ?restriction owl:onProperty ?prop .
    OPTIONAL { ?restriction owl:allValuesFrom ?allClass . } .
    OPTIONAL { ?restriction owl:someValuesFrom ?someClass . } .
    OPTIONAL { ?restriction owl:hasValue ?lval . FILTER(isLiteral(?lval)) . } .
    OPTIONAL { ?restriction owl:hasValue ?ival . FILTER(!isLiteral(?ival)) . } .
} group by ?restriction ?prop
LIMIT 200

    """

    ONT_LIST_QUERY = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

select ?list (GROUP_CONCAT(distinct ?entity;SEPARATOR=",") AS ?entities) where { 
    ?subject owl:unionOf|owl:intersectionOf|owl:oneOf|owl:onProperties|owl:members|owl:disjoinUnionOf|owl:propertyChainAxioms|owl:hasKey ?list .
    OPTIONAL {?list rdf:rest*/rdf:first ?entity . } .
} group by ?list
LIMIT 200

    """

    # sub-function to run a sparql query and transform it
    # the transform works like this
    # sparql result: [ { "col1": { value "a"}, "col2": { value: "b,c"}, "col3 : { value: "d"}"}]
    # transformed: [ "a": { "col2": ["b", "c"], "col3", "d"}]
    # Here "col1" is the key, so the "a" becomes the key
    # "b,c" is comma-sep value and is transformed to list ["b", "c"]
    # "col3" is a single, so it its val is "d" rather than ["d"]
    def _run_model_query(q, key, singles):
        res = execute_sparql_query(q)
        result_dict = {}
        for rec in res:
            this_rec = {"visited": False, "visitedForProps": False, "discoveredProps": [], "restrictedProps": []}
            for rec_key in rec:
                val = str(rec[rec_key]["value"])
                if rec_key == key:
                    this_rec[rec_key] = val
                    result_dict[val] = this_rec
                elif _list_has_value(singles, rec_key) :
                    this_rec[rec_key] = val
                elif val == "":
                    this_rec[rec_key] = []
                else:
                    toks = val.split(",")
                    this_rec[rec_key] = toks

        return result_dict        

    # run the queries
    class_res = _run_model_query(ONT_CLASS_QUERY, "class", [])
    prop_res = _run_model_query(ONT_PROP_QUERY, "prop", [])
    restriction_res = _run_model_query(ONT_RESTRICTION_QUERY, "restriction", ["prop"])
    list_res = _run_model_query(ONT_LIST_QUERY, "list", [])
    classes = list(class_res.keys())
    props = list(prop_res.keys())
    restrictions = list(restriction_res.keys())
    lists = list(list_res.keys())

    # 
    # Walk functions. If a class/prop refers to a bnode, let's drill down and see what that bnode is.
    # Walk the bnode too, and capture its structure in the parent class/prop.
    # Example, suppose a class has a subClassOf b, where b is a bnode. 
    # What is that bnode? It might be a class that is a restriction on a property. 
    # That's useful to know, so we capture that expanded view in the parent class.
    #

    def _make_walked_node(b, v):
        return {"bnode": b, "obj": v}

    def _expand_list(rec, keys):
        for list_type in keys:
            new_list = []
            for entry in rec[list_type]:
                if _is_bnode(entry):
                    new_list.append(_make_walked_node(entry, _walk(entry)))
                else:
                    new_list.append(entry)
            rec[list_type+"_expand"] = new_list
    
    
    def _walk(entry):
        if _list_has_value(classes, entry):
            return _walk_class(entry)
        elif _list_has_value(restrictions, entry):
            return _walk_restriction(entry)
        elif _list_has_value(props, entry):
           return _walk_prop(entry)
        elif _list_has_value(lists, entry):
           return _walk_list(entry)
        else:
            return entry

    def _walk_list(l):
        #print("visit list " + l)
        if _list_has_value(lists, l):
            rec = list_res[l]
            if rec["visited"]:
                    return rec
            else:
                new_list = []
                _expand_list(rec, ["entities"])
                rec["visited"] = True
                return rec
        else:
            return l
        
    
    def _walk_class(clazz):
        #print("visit class " + clazz)
        if _list_has_value(classes, clazz):
            rec = class_res[clazz]
            if rec["visited"]:
                    return rec
            else:
                _expand_list(rec, ["keys", "subsOf", "equivs", "complements", "disjoints", "unions", "intersections"])
                rec["visited"] = True
                return rec
        else:
            return clazz

    def _walk_prop(prop):
        #print("visit prop " + prop)
        if _list_has_value(props, prop):
            rec = prop_res[prop]
            if rec["visited"]:
                    return rec
            else:
                _expand_list(rec, ["subsOf", "equivs", "inverses", "disjoints", "domains", "ranges"])
                rec["functional"] = _list_has_value(rec["types"], "http://www.w3.org/2002/07/owl#FunctionalProperty")
                if _list_has_value(rec["types"], "http://www.w3.org/2002/07/owl#ObjectProperty"):
                    rec["propType"] = "ObjectProperty"
                elif _list_has_value(rec["types"], "http://www.w3.org/2002/07/owl#DatatypeProperty"):
                    rec["propType"] = "DatatypeProperty"
                elif _list_has_value(rec["types"], "http://www.w3.org/1999/02/22-rdf-syntax-ns#Property"):
                    rec["propType"] = "Property"   
                rec["visited"] = True
                return rec        
        else:
            return clazz

    def _walk_restriction(restriction) :
        #print("visit restriction " + restriction)
        if _list_has_value(restrictions, restriction):
            rec = restriction_res[restriction]
            if rec["visited"]:
                    return rec
            else:
                if _is_bnode(rec["prop"]):
                    rec["prop"] = _make_walked_node(rec["prop"], _walk(rec["prop"]))
                _expand_list(rec, ["allFromClasses", "someFromClasses"])
                rec["visited"] = True
                return rec
        else:
            return restriction

    # walk the properties and classes, bringing in dependencies like lists, restrictions, and related classes
    for entry in prop_res:
        _walk_prop(entry)
    for entry in class_res:
        _walk_class(entry)

    # for the given prop, if it belongs to expected_clazz, return the prop plus super-props
    def _get_props(prop, expected_clazz):
        if _list_has_value(props, prop):
            candidate = False
            if expected_clazz == None:
                candidate = True
            else:
                # class is domain
                for dom in prop_res[prop]["domains"]:
                    if dom == expected_clazz:
                        candidate = True
                        break
                # domain is union and includes class
                for dom in prop_res[prop]["domainUs"]:
                    if dom == expected_clazz:
                        candidate = True
                        break
            if candidate:
                # return this prop and props of which the prop is subsOf
                return list(set([prop] + prop_res[prop]["subsOf"]))
            else:
                return []
        else:
            return []

    # recursively walk the class, looking for properties.
    def _walk_class_for_props(clazz):
        #print("visit " + clazz)
        # am i a class or a restriction?
        if _list_has_value(restrictions, clazz):
            if not(restriction_res[clazz]["visitedForProps"]):
                #print(" restriction visit " + clazz)
                restriction_res[clazz]["visitedForProps"] = True
                prop_uri = restriction_res[clazz]["prop"]
                restriction_res[clazz]["restrictedProps"] = [{
                        "prop": prop_uri,
                        "restriction": clazz,
                        "all" : restriction_res[clazz]["allFromClasses"], 
                        "some": restriction_res[clazz]["someFromClasses"],
                        "lvals": restriction_res[clazz]["lvals"],
                        "ivals": restriction_res[clazz]["ivals"] }]
            return restriction_res[clazz]
        elif _list_has_value(classes, clazz):
            if not(class_res[clazz]["visitedForProps"]):
                #print(" class visit " + clazz)
                
                # if i'm not a bnode, get all props that apply to me
                if not(_is_bnode(clazz)):
                    for prop in props:
                        class_res[clazz]["discoveredProps"] = list(set(class_res[clazz]["discoveredProps"] + _get_props(prop, clazz)))
                
                for list_type in ["subsOf", "intersectionEntries", "equivs"]:
                    for entry in class_res[clazz][list_type]:
                        can_use = _list_has_value(classes, entry) or _list_has_value(restrictions, entry)
                        if list_type == 'equivs' and _is_bnode(entry) == False:
                            can_use = False
                        if can_use:
                            # recurse for subsOf, intersectionEntries, equivs (restrictions only)
                            recurse_result = _walk_class_for_props(entry)
                            class_res[clazz]["discoveredProps"] = list(set( class_res[clazz]["discoveredProps"] + recurse_result["discoveredProps"]))
                            class_res[clazz]["restrictedProps"] += recurse_result["restrictedProps"]
                class_res[clazz]["visitedForProps"] = True
            return class_res[clazz]
                                
        else:
            print(" VERY BAD visit " + clazz)
            return None            
        
    # for each class determine the properties by walking
    for entry in class_res:
        if not(_is_bnode(entry)):
            _walk_class_for_props(entry)

    # return the model - the classes and properties discovered
    return {
        "classes": class_res,
        "props": prop_res
    }

def discover_and_merge_ontological(observed):
    ont_model = _discover_ont()

    for clazz in ont_model["classes"]:
        print(clazz)
        if _is_bnode(clazz):
            continue
    
        # Merge class level
        class_entry = {'props':{} }
        if clazz in observed:
            class_entry = observed[clazz]
        else:      
            observed[clazz] = class_entry
        class_entry['isOntology'] = True 

        # Merge prop-level: restrictions
        for r in ont_model["classes"][clazz]["restrictedProps"]:
            prop_entry = {"lits": [], "rels": [], "isSingleton": False,
                "isList": False,
                "metaprops": {}
            }
            if r['prop'] in class_entry['props']:
                prop_entry = class_entry['props'][r['prop']]
            else:
                class_entry['props'][r['prop']]=prop_entry

            prop_entry['isOntology'] = True
            prop_entry['isRestriction'] = True
            prop_entry['isRestrictionAll'] = len(r['all']) > 0
            prop_entry['isRestrictionSome'] = len(r['some']) > 0
            for l in r['lvals']:
                if not(l in prop_entry['lits']):
                    prop_entry['lits'].append(l)
            for i in r['ivals']:
                if not(i in prop_entry['rels']):
                    prop_entry['rels'].append(l)

        for prop in ont_model["classes"][clazz]["discoveredProps"]:
            if prop in ont_model["props"]:
                prop_def = ont_model["props"][prop]

                prop_entry = {"lits": [], "rels": [], "isSingleton": False,
                    "isList": False,
                    "metaprops": {}
                }
                if prop in class_entry['props']:
                    prop_entry = class_entry['props'][prop]
                else:
                    class_entry['props'][prop]=prop_entry

                prop_entry['isOntology'] = True
                prop_entry['isFunctional'] = prop_def["functional"]
                prop_entry['propType'] = prop_def["propType"]

                for r in prop_def['ranges'] + prop_def['rangeUs']:
                    if _is_bnode(r):
                        continue
                    if prop_entry['propType'] == 'ObjectProperty':
                        if not(r in prop_entry['rels']):
                            prop_entry['rels'].append(r)
                    else:
                        if not(r in prop_entry['lits']):
                            prop_entry['lits'].append(r)


    return observed
    

'''
This part manages CURIEs.
Full URIs are long and have special characters that clutter and confuse PlantUML notation.
It's much cleaner to show a CURIE: prefix:localName

We'll use common prefixes like rdf, rdfs, owl.

For app-specific URI's, we'll auto assign a prefix ns{i}. You can override this by
assigning your own prefix.
'''

next_idx = 0
CUSTOM_PREFIXES={}
def make_curie(uri):
    global next_idx
    def split_uri(uri):
        if "#" in uri:
            tokens = uri.split("#")
            return [f"{tokens[0]}#", tokens[-1]]
        elif "/" in uri:
            tokens = uri.split("/")
            return [f"{'/'.join(tokens[0:len(tokens)-1])}/", tokens[-1]]
        else:
            raise ValueError(f"Unexpected IRI '{uri}', contains neither '#' nor '/'.")
    toks = split_uri(uri)
    
    if not(toks[0] in CURIE_BY_URI):
        curie_prefix = f"ns{str(next_idx)}"
        next_idx += 1
        CURIE_BY_URI[toks[0]] = curie_prefix
        CURIE_BY_PREFIX[curie_prefix] = toks[0]
        CUSTOM_PREFIXES[curie_prefix] = toks[0]
    
    return [toks[0], CURIE_BY_URI[toks[0]], toks[1], f"{CURIE_BY_URI[toks[0]]}:{toks[1]}", f"{CURIE_BY_URI[toks[0]]}_{toks[1]}" ]

CURIE_BY_PREFIX={}
CURIE_BY_URI={}
def load_prefixes(prefixes_file = 'prefixes.txt'):
    # Common prefixes. source: http://prefix.cc/popular/all.sparql
    with open(prefixes_file) as f:
        sprefixes = f.read()

    for sp in sprefixes.split("\n"):
        if len(sp) > 0:
            toks = sp.split()
            prefixcolon = toks[1]
            prefix = prefixcolon[0:len(prefixcolon)-1]
            uriangle = toks[2]
            uri = uriangle[1:len(uriangle)-1]
            CURIE_BY_PREFIX[prefix]=uri
            CURIE_BY_URI[uri]=prefix

def get_prefixes_by_prefix():
    return CURIE_BY_PREFIX

def get_prefixes_by_URI():
    return CURIE_BY_URI

# Call this to add your own prefix/URI. Otherwise an ns{i} prefix will be assigned
# when you make a curie
def add_prefix(prefix, uri):
    CURIE_BY_URI[uri]=prefix
    CURIE_BY_PREFIX[prefix]=uri

next_idx = 0
def make_curie(uri, delim=":"):
    global next_idx
    def split_uri(uri):
        if "#" in uri:
            tokens = uri.split("#")
            return [f"{tokens[0]}#", tokens[-1]]
        elif "/" in uri:
            tokens = uri.split("/")
            return [f"{'/'.join(tokens[0:len(tokens)-1])}/", tokens[-1]]
        else:
            raise ValueError(f"Unexpected IRI '{uri}', contains neither '#' nor '/'.")
    toks = split_uri(uri)
    
    if not(toks[0] in CURIE_BY_URI):
        curie_prefix = f"ns{str(next_idx)}"
        next_idx += 1
        CURIE_BY_URI[toks[0]] = curie_prefix
        CURIE_BY_PREFIX[curie_prefix] = toks[0]
    
    return f"{CURIE_BY_URI[toks[0]]}{delim}{toks[1]}"

'''
This part writes PlantUML so you can render it in the viewer
'''

# Optionally remove classes beforehand
def to_plant_uml(classes, class_filter=None, max_classes=-1, max_rels=-1):

    plant_uml_sections=["", ""]
    all_refs = {}

    CURIE_DELIM_PLANTUML="_"
    def _make_curie(uri):
        return make_curie(uri, CURIE_DELIM_PLANTUML)

    def _notes_string(notes):
        return "\\n".join(notes)

    def _start_class(class_name, stereos):
        s_stereos = ""
        for s in stereos:
            s_stereos += f" << {s} >> "
        plant_uml_sections[0] += f"\nclass {class_name}{s_stereos} {{"
        
    def _end_class(class_name, ref_only_classes, all_meta_notes):
        plant_uml_sections[0] += "\n}"
        for r in ref_only_classes:
            if not(r in all_refs):
                all_refs[r] = r
                plant_uml_sections[0] += f"\nclass {r} << refonly >> {{"
                plant_uml_sections[0] += "\n}"
        if len(all_meta_notes) > 0:
            plant_uml_sections[0] += f'\nnote top of {class_name}: {_notes_string(all_meta_notes)}  '
            
    def _add_prop(prop_name, prop_stereos, is_list, lits):
        types = ",".join(lits)
        s_stereos = ""
        for s in prop_stereos:
            s_stereos += f" << {s} >> "
        if len(lits) == 0:
            plant_uml_sections[0] += f"\n   - {prop_name}{s_stereos}"
        else:
            plant_uml_sections[0] += f"\n   - {prop_name}{s_stereos}: {types}{'*' if is_list else ''}"
        
    def _add_rel(class_name, prop_name, prop_stereos, is_list, r, meta_notes):
        s_stereos = ""
        for s in prop_stereos:
            s_stereos += f" << {s} >> "
            
        plant_uml_sections[1] += f'\n{class_name} "1" -- "*" {r} : {prop_name} {s_stereos} > '
        if len(meta_notes) > 0:
            plant_uml_sections[1] += f'\nnote on link: {_notes_string(meta_notes)}  '

    num_classes = 0
    num_rels = 0
    for c in classes:
        # filter
        if not(class_filter is None) and not (c in class_filter):
            continue

        # max classes?
        num_classes += 1
        if max_classes >=0 and num_classes > max_classes:
            print("Max classes. Stopping.")
            break
            
        class_name = _make_curie(c)
        stereos = []
        ref_only_classes = []
        if 'isStatement' in classes[c]:
            stereos.append('stmt')
        if 'isOntology' in classes[c]:
            stereos.append('ontology')
        _start_class(class_name, stereos)

        all_meta_notes = []
        for p in classes[c]['props']:
            prop_name = _make_curie(p)
            if prop_name == "rdf_type":
                continue
                
            is_list = classes[c]['props'][p]['isList']
            prop_stereos = []

            # ontology stereotypes
            if classes[c]['props'][p]['isSingleton']:
                prop_stereos.append('singleton')
            if 'isOntology' in classes[c]['props'][p]:
                prop_stereos.append('ontology')
            if 'isRestriction' in classes[c]['props'][p]:
                prop_stereos.append('restriction')
            if 'isRestrictionAll' in classes[c]['props'][p]:
                prop_stereos.append('restrictionAll')
            if 'isRestrictionSome' in classes[c]['props'][p]:
                prop_stereos.append('restrictionSome')
            if 'isFunctional' in classes[c]['props'][p]:
                prop_stereos.append('functional')
            if 'propType' in classes[c]['props'][p]:
                prop_stereos.append(classes[c]['props'][p]['propType'])

            meta_notes = []
            has_meta = False
            meta_on_rel = False
            for m in classes[c]['props'][p]['metaprops']:
                if has_meta == False:
                    has_meta = True
                    meta_notes.append(f"Metadata of type {classes[c]['props'][p]['metaprops'][m]['entryType']} on prop {_make_curie(p)}")
                    meta_notes.append("Meta properties:")
                
                meta_prop_name = _make_curie(m)
                types = []
                for l in classes[c]['props'][p]['metaprops'][m]['lits']:
                    types.append(_make_curie(l))
                for r in classes[c]['props'][p]['metaprops'][m]['rels']:
                    types.append(_make_curie(r))
                typestr = ",".join(types)
                if len(types) > 0: 
                    meta_notes.append(f"  {meta_prop_name} : {typestr}")
                else:
                    meta_notes.append(f"  {meta_prop_name}")

            lits = []
            rels = []
            for l in classes[c]['props'][p]['lits']:
                lits.append(_make_curie(l))
            for r in classes[c]['props'][p]['rels']:
                rel_type = _make_curie(r)
                if rel_type in ['rdf.Bag', 'rdf.Alt', 'rdf.Seq', 'rdf.Container']:
                    continue
                rels.append(rel_type)
                if not(r in classes):
                    ref_only_classes.append(rel_type)

            if len(lits) > 0 or len(rels) == 0:
                all_meta_notes += meta_notes
                _add_prop(prop_name, prop_stereos, is_list, lits)
                
            for r in rels:
                num_rels += 1
                if max_rels >=0 and num_rels > max_rels:
                    print(f"Max rels reached. Skipping {prop_name} of {class_name}")
                else:
                    _add_rel(class_name, prop_name, prop_stereos, is_list, r, meta_notes)
                          
        _end_class(class_name, ref_only_classes, all_meta_notes)

    # Build PlantUML string from classes_str and rel_str above
    plantspec = f"""
@startuml

{plant_uml_sections[0]}

{plant_uml_sections[1]}

@enduml
"""
    return plantspec

