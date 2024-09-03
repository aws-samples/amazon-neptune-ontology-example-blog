import aos_helpers as aosh
import neptune_helpers as nh
import ai_helpers as aih
import json

CAT_DOC="document"
CAT_YELLOW_EVENT="yellow-event"
CAT_YELLOW_ENTITY="yellow-entity"
CAT_CLASS="class"
CAT_REL="rel"
CAT_CONCEPT="concept"
CAT_BLUE_ENTITY="blue"
CAT_OTHER="other"
CAT_PATHS="paths_s_p_o"
CAT_DEBUG="_debug"

'''
TODO:
- inference classes
- ask a question about an industry buying a startup. So I need to connect industry to company ...
'''

'''
This module uses the other helpers to help answer, and present the results of, a question.
We break this into steps for explanatory purposes. The notebook shows one way to bring them together.
'''

# will store results as we find them
def create_results():
    return {
        CAT_DOC:{},
        CAT_YELLOW_EVENT:{},
        CAT_YELLOW_ENTITY:{},
        CAT_BLUE_ENTITY:{},
        CAT_CLASS:{},
        CAT_REL: {},
        CAT_CONCEPT: {},
        CAT_OTHER: {},
        CAT_PATHS: [],
        CAT_DEBUG:{}
    }

# function create create a wallet for all the connections
def make_client(session, neptune_conn, aos_client, bedrock_client, comprehend_client):
    return {
        'session': session,
        'neptune_conn': neptune_conn,
        'aos_client': aos_client,
        'bedrock_client': bedrock_client,
        'comprehend_client': comprehend_client
    }

# render those results as a json file
def render_results_json_file(json_fname, results):
    with open(json_fname, 'w') as f: 
        f.write(json.dumps(results, indent=4))

# render those results as an HTML file
def render_results_html(html_fname, results):
    pass

# render those results as a PNG graph diagram
def render_results_graphviz(png_fname, results):
    pass

# render those results as a PNG graph diagram
# this is the lone RAG case
def render_results_llm_summary(client, summary_fname, question, results):
    with open(summary_fname, 'w') as f: 
        f.write(aih.summarize_graph_results(client['bedrock_client'], question, results))

# private function to run a describe and save objects to results
'''
in results I need a path:
path: s, p, o, p2, o2, ...
here I can directly link them
'''
DESCRIBE_LIMIT=1000
def _describe(client, results, uri, meta):
    # describe only once
    if not('desc_hit_list') in results[CAT_DEBUG]:
        results[CAT_DEBUG]['desc_hit_list']={}
        
    if uri in results[CAT_DEBUG]['desc_hit_list']:
        return results[CAT_DEBUG]['desc_hit_list'][uri]
    
    ret = nh.describe(client['session'], client['neptune_conn'], uri, DESCRIBE_LIMIT)
    tbl=nh.make_select_table(ret)
    
    if len(tbl) == 0:
        return None

    cat=None
    rec={
        'uri': None,
        'cat': None,
        'types': None,
        'typeLabels': None,
        'typeSuperClasses': None,
        'labels': None,
        'uriSuperClasses': None, 
        'uriSuperProperties': None
    }
    
    for row in tbl:
        # first row - add the rec if not already in results
        if cat is None:
            if not('cat' in row):
                cat = CAT_BLUE_ENTITY
            else:
                cat = row['cat']['value']
                
            results[CAT_DEBUG]['desc_hit_list'][uri]=cat   
            if not(uri in results[cat]):
                rec['uri'] = row['uri']['value']
                rec['cat'] = cat
                rec['types'] = row['types']['value'] if 'types' in row else ""
                rec['typeLabels'] = row['typeLabels']['value'] if 'typeLabels' in row else ""
                rec['typeSuperClasses'] = row['typeSuperClasses']['value'] if 'typeSuperClasses' in row else ""
                rec['labels'] = row['labels']['value'] if 'labels' in row else ""
                rec['uriSuperClasses'] = row['uriSuperClasses']['value'] if 'uriSuperClasses' in row else ""
                rec['uriSuperProperties'] = row['uriSuperProperties']['value'] if 'uriSuperProperties' in row else ""
                results[cat][uri] = {
                    'meta': meta,
                    'record': rec
                }
                
        # now consider the direct connections; add to doc record
        p=row['p']['value']
        pl=row['pLabels']['value'] if 'pLabels' in row else ""
        o=row['o']['value']
        is_uri=row['o']['type']=='uri'
        direction=row['direction']['value']
        if not(p in rec):
            rec[p] = []
        rec[p].append({'p': p, 'relLabels': pl, 'value': o, 'direction': direction}) 
        
        # also make paths of direct connections
        if is_uri:
            path=[uri, p, o] if dir=="out" else [o, p, uri]
            if not("distinct_paths") in results[CAT_DEBUG]:
                results[CAT_DEBUG]["distinct_paths"]={}
            if not(str(path) in results[CAT_DEBUG]["distinct_paths"]):
                results[CAT_DEBUG]["distinct_paths"][str(path)]='Y'
                results[CAT_PATHS].append(path)
                       
    return cat

'''
Find chunks in AOS that are similar to the question. 
Use AI helper to make embedding of question to match against AOS vector index.
Store in results
'''
CHUNK_CUTOFF=0.66
def find_chunks(client, results, question):
    # use ai helper to make embedding of question
    search_vector=aih.make_embedding(client['bedrock_client'], question)
    
    # use aos helper to find chunks like the embedding
    ret=aosh.find_chunks(client['aos_client'], search_vector)
    
    # organize AOS result and add to our query results    
    distinct_docs={}

    for h in ret['hits']['hits']:
        if h['_score'] >= CHUNK_CUTOFF:
            doc_uri = h['_source']['graph_doc_uri']

            if not (doc_uri in results[CAT_DOC]):
                doc_meta = {
                    'find_order': 1,
                    'doc_uri': doc_uri, 
                    'source': 'chunk match', 
                    'best_chunk_score':h['_score'],
                    'best_chunk_index': h['_source']['chunk_index'],
                    'best_chunk_content': h['_source']['chunk_content']
                }
                _describe(client, results, doc_uri, doc_meta)
                distinct_docs[doc_uri] = 'Y'

'''
Extract entities from question using comprehend and an LLM.
The results are saved to the results dictionary.
'''
def extract_from_question(client, results, question):
    comp_ents=aih.extract_comprehend_entities_from_q(client['comprehend_client'], question) 
    llm_ents=aih.analyze_question(client['bedrock_client'], question)
    results[CAT_DEBUG]['comp_ents']=comp_ents
    results[CAT_DEBUG]['llm_ents']=llm_ents
    
    # a bit of validation and repair of LLM response
    if not('entities' in llm_ents):
        raise Exception("LLM response is not well formed " + str(llm_ents))
    if not('types' in llm_ents):
        llm_ents['types']={}
    if not('predicates' in llm_ents):
        llm_ents['predicates']={}
    if not('intent' in llm_ents):
        llm_ents['intent']=[]
           

'''
Private utility to call AOS helper to get resources in Neptune index with similar labels.
An additional filter on type.
'''
FILTER_BY_EXTRACTED_ENTITY="entity_id:*ExtractedEntity*"
FILTER_BY_EXTRACTED_EVENT="entity_id:*ExtractedEvent*"
FILTER_BY_NON_EXTRACTED_ENTITY="NOT entity_id:*ExtractedEntity*"
FILTER_BY_NON_EXTRACTED="NOT entity_id:*Extracted*"
FILTER_BY_CLASS="entity_type:Class"
FILTER_BY_REL="entity_type:ObjectProperty"
FILTER_ALL=None
SCORE_PER_MAX_CUTOFF=0.9
def _find_entities_by_label(client, labels, additional_filter=None):   
    matches=[]
    ret=aosh.find_entities_by_label(client['aos_client'], labels, additional_filter)
    max_score=ret['hits']['max_score']
    for r in ret['hits']['hits']:
        score=r['_score']
        if score/max_score > SCORE_PER_MAX_CUTOFF:
            matches.append({
                'max_score': max_score,
                'score': score,
                'uri': r['_source']['entity_id'],
                'types': r['_source']['entity_type'] if 'entity_type' in r['_source'] else [],
                'rdfsLabel': r['_source']['predicates']['http://www.w3.org/2000/01/rdf-schema#label'] if 'http://www.w3.org/2000/01/rdf-schema#label' in r['_source']['predicates'] else [],
                'prefLabel': r['_source']['predicates']['http://www.w3.org/2004/02/skos/core#prefLabel'] if 'http://www.w3.org/2004/02/skos/core#prefLabel' in r['_source']['predicates'] else [],
                'altLabel': r['_source']['predicates']['http://www.w3.org/2004/02/skos/core#altLabel']  if 'http://www.w3.org/2004/02/skos/core#altLabel' in r['_source']['predicates'] else [],
                'suggestedLabel': r['_source']['predicates']['http://example.org/orgdemo/suggestedLabel'] if 'http://example.org/orgdemo/suggestedLabel' in r['_source']['predicates'] else []
            })
    return matches
                
'''
Function that takes entity extraction results from LLM and Comprehend. 
Then it asks AOS search index to find graph URIs that match these.

Note:
This function does not match labels in Neptune because it leverages AOS for this.
But for an example of how to do this in Neptune, look at neptune_helpers.find_resource_by_name()
'''
def resolve_entity_extraction_results(client, results):
    
    llm_ents=results[CAT_DEBUG]['llm_ents']
    comp_ents=results[CAT_DEBUG]['comp_ents']
    
    #
    # 1 - combine Comprehend and LLM results: entities, types, predicates
    # 
    xterms={
        'entities':{},
        'types':{},
        'predicates':{}
    }
    e_name2key={}
    t_name2key={}

    # LLM entities
    for e in llm_ents['entities']:
        enames = [e] + llm_ents['entities'][e]['alternateEntityNames']
        euris = llm_ents['entities'][e]['wellKnownURIs']
        etype = llm_ents['entities'][e]['type']
        xterms['entities'][e] = {'names': enames, 'uris': euris, 'connects_op': [] }
        if not(etype is None) and len(etype)>0:
            xterms['entities'][e]['types']=[etype]
        for en in enames:
            e_name2key[en]=e

    # LLM types
    for t in llm_ents['types']:
        tnames = [t] + llm_ents['types'][t]['alternateNames']
        turis = llm_ents['types'][t]['wellKnownURIs']
        xterms['types'][t] = {'names': tnames, 'uris': turis } 
        for tn in tnames:
            t_name2key[tn]=t

    # LLM predicates
    for p in llm_ents['predicates']:
        pnames = [p] + llm_ents['predicates'][p]['alternateNames']
        puris = llm_ents['predicates'][p]['wellKnownURIs']
        xterms['predicates'][p] = {'names': pnames, 'uris': puris } 
        
    # LLM connects
    for i in llm_ents['intent']:
        if len(i)==4 and i[0] == "connect":
            cs=i[1]
            co=i[2]
            cp=i[3]
            if cs in xterms['entities']:
                xterms['entities'][cs]['connects_op'].append([co, cp])

    # comprehend entities 
    COMPREHEND_SCORE_CUTOFF=0.0
    for c in comp_ents['Entities']:
        if c['Score'] >= COMPREHEND_SCORE_CUTOFF:
            ename=c['Text']
            etype=c['Type']
            # The URI for extacted entity is here. We won't guess at blue class.
            euri=f"http://example.org/orgdemo/xent/{etype}"

            if ename in e_name2key:
                ekey = e_name2key[ename]
                if not(etype in xterms['entities'][ekey]['types']):
                    xterms['entities'][ekey]['types'].append(etype)
            else:
                xterms['entities'][ename] = {'names': [etype], 'types': [etype] } 

            if etype in t_name2key:
                tkey = t_name2key[etype]
                if not(euri in xterms['types'][tkey]['uris']):
                    xterms['types'][tkey]['uris'].append(euri)
            else:
                xterms['types'][etype] = {'names': [etype], 'uris': [euri] } 
          
    #
    # 2 - Call AOS to search most likely graph resources being mentioned.
    #
    def add_resolved_uri(xtyp, x, u, subtyp=None):
        uris=xterms[xtyp][x]['uris']
        if not(subtyp is None):
            if not(subtyp in xterms[xtyp][x]):
                 xterms[xtyp][x][subtyp]=[]
            uris=xterms[xtyp][x][subtyp]
            
        if not(u in uris):
            uris.append(u)
            
    def resolve_each(xtyp, match_order, subtyp=None):
        for p in xterms[xtyp]:
            for mo in match_order:
                ret=_find_entities_by_label(client, xterms[xtyp][p]['names'], mo)
                for m in ret:
                    uri=m['uri']
                    add_resolved_uri(xtyp, p, uri, subtyp)
 
    resolve_each('predicates', [FILTER_BY_REL, FILTER_BY_CLASS, FILTER_ALL])
    resolve_each('types', [FILTER_BY_CLASS, FILTER_BY_REL, FILTER_ALL])
    resolve_each('entities', [FILTER_BY_NON_EXTRACTED], 'blue')
    resolve_each('entities', [FILTER_BY_EXTRACTED_ENTITY, FILTER_BY_EXTRACTED_EVENT, FILTER_ALL], 'yellow')
    results[CAT_DEBUG]['xterms']=xterms

'''
Function check resolved entities exist in Neptune. 

It finds them in the graph and describes each, and adds them to the results.

It does not attempt to connect anything. That comes later.
'''
def describe_resolved_graph_entities(client, results):
    
    xterms=results[CAT_DEBUG]['xterms']
    for e in xterms['entities']:
        uris=xterms['entities'][e]['uris']
        blue=xterms['entities'][e]['blue'] if 'blue' in xterms['entities'][e] else []
        yellow=xterms['entities'][e]['yellow'] if 'blue' in xterms['entities'][e] else []
        for u in list(set(uris+blue+yellow)):
            cat=_describe(client, results, u, {'source': 'extract', 'find_order': 1, 'entities': [], 'predicates': []})
            if not(cat is None):
                print(f"{u}*{cat}*")
                results[cat][u]['meta']['entities'].append(e)
                                      
    # predicates
    for e in xterms['predicates']:
        uris=xterms['predicates'][e]['uris']
        for u in list(set(uris)):
            cat=_describe(client, results, u, {'source': 'extract', 'find_order': 1, 'entities': [], 'predicates': []})
            if not(cat is None):
                print(f"{u}*{cat}*")
                results[cat][u]['meta']['predicates'].append(e)

'''
Take to/from each resource collected to far, unless we have already visited it.
One hop is sufficient.
We'll handle the yellow event->entity specially.

Then try to build the connect paths asked for.
'''
def connect(client, results):
    pass 

'''
One function that brings everything togther.
It requires you to make the client first: make_client
When it completes, you can use the render() functions to render the results
'''
def answer_question(client, question):
    results=create_results()
    print("Chunking")
    find_chunks(client, results, question)
    print("Extracting")
    extract_from_question(client, results, question)
    print("Resolving")
    resolve_entity_extraction_results(client, results)
    print("Describing")
    describe_resolved_graph_entities(client, results)
    print("Connecting")
    connect(client, results)
    print("Done. Use render() functions to render result")
    return results