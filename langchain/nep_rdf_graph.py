from __future__ import annotations

import json
import requests
import urllib.parse

from typing import (
    TYPE_CHECKING,
    List,
    Optional,
)

# Queries adapted from 
# https://github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain/graphs/rdf_graph.py

CLASS_QUERY = """
SELECT DISTINCT ?cls ?com
WHERE { 
 ?instance a ?cls .
 OPTIONAL { ?instance rdf:type/rdfs:subClassOf* ?cls } .
 #FILTER (isIRI(?cls)) .
 OPTIONAL { ?cls rdfs:comment ?com filter (lang(?com) = "en")}
}
"""

REL_QUERY = """
SELECT DISTINCT ?rel ?com
WHERE { 
 ?subj ?rel ?obj . 
 OPTIONAL { 
     ?rel rdf:type/rdfs:subPropertyOf* ?proptype .
     VALUES  ?proptype  { rdf:Property owl:DatatypeProperty owl:ObjectProperty } .
 } . 
 OPTIONAL { ?rel rdfs:comment ?com filter (lang(?com) = "en")} 
}
"""

DTPROP_QUERY = """
SELECT DISTINCT ?rel ?com
WHERE { 
 ?subj ?rel ?obj . 
 OPTIONAL { 
     ?rel rdf:type/rdfs:subPropertyOf* ?proptype .
     ?proptype  a owl:DatatypeProperty .
 } . 
 OPTIONAL { ?rel rdfs:comment ?com filter (lang(?com) = "en")} 
}
"""

OPROP_QUERY = """
SELECT DISTINCT ?rel ?com
WHERE { 
 ?subj ?rel ?obj . 
 OPTIONAL { 
     ?rel rdf:type/rdfs:subPropertyOf* ?proptype .
     ?proptype  a owl:ObjectProperty .
 } . 
 OPTIONAL { ?rel rdfs:comment ?com filter (lang(?com) = "en")} 
}
"""

class NepRdfGraph:
    """
    Modes:
    * online: Online file - can only be queried, changes can be stored locally
    """

    def __init__(
        self,
        query_endpoint: Optional[str] = None
    ) -> None:
        """
        Set up the RDFlib graph
        :param query_endpoint: SPARQL endpoint for queries, read access
        """
        self.query_endpoint = query_endpoint
        self.summary_endpoint = query_endpoint.split("/sparql")[0] + "/rdf/statistics/summary?mode=detailed" 

        print("SPARQL endpoint *"  + self.query_endpoint + "*")
        print("Summary endpoint *"  + self.summary_endpoint + "*")

        # Set schema
        self.schema = ""
        self.load_schema()
        
    @property
    def get_schema(self) -> str:
        """
        Returns the schema of the graph database.
        """
        return self.schema

    def query(
        self,
        query: str,
    ):

        # fix the query
        querytoks = query.strip().split("```")
        if len(querytoks) == 3:
            query = querytoks[1]
        
        if query.startswith("sparql"):
            query = query[6:]

        print("the query is actually")
        print(query)
            
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        params = {'query': query}
        data = urllib.parse.urlencode(params)

        queryres = requests.post(self.query_endpoint, headers=headers, data=data)

        print(queryres.reason)
        json_resp = json.loads(queryres.text)
        return json_resp

    @staticmethod
    def _get_local_name(iri: str) -> str:
        if "#" in iri:
            local_name = iri.split("#")[-1]
        elif "/" in iri:
            local_name = iri.split("/")[-1]
        else:
            raise ValueError(f"Unexpected IRI '{iri}', contains neither '#' nor '/'.")
        return local_name

 
    def load_schema(self) -> None:
        """
        Load the graph schema information.
        """
        
        """
        This approach uses summary API - not very helpful to the LLM
        
        queryres = requests.get(self.summary_endpoint)
        jsummary = json.loads(queryres.text)
        classes = jsummary['payload']['graphSummary']['classes']
        rels = []
        for kv in jsummary['payload']['graphSummary']['predicates']:
            for k in kv:
                rels.append(k)
        rels

        ssummary = "Summary of schema\nClasses: " + "\n".join(classes) + "\nRelationships: " + "\n".join(rels)

        print("Summary is")
        print(ssummary)

        self.schema = ssummary
        """

        def _sparqlres_to_str(self, sres, var: str) -> str:

            reslist = []
            for r in sres['results']['bindings']:
                uri = r[var]['value']
                comment = r['com']['value'] if 'com' in r else ""
                reslist.append("<" + str(uri) + "> (" + self._get_local_name(uri) + ", " + str(comment) + ")")
            return ", ".join(reslist)
        
        
        """
        This approach is based on 
        https://github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain/graphs/rdf_graph.py
        """
        clazz_res = self.query(CLASS_QUERY)
        clazzes = _sparqlres_to_str(self, clazz_res, 'cls')
        rel_res = self.query(REL_QUERY)
        rels = _sparqlres_to_str(self, rel_res, 'rel')
        dt_res = self.query(DTPROP_QUERY)
        dtprops = _sparqlres_to_str(self, dt_res, 'rel')
        o_res = self.query(OPROP_QUERY)
        oprops = _sparqlres_to_str(self, o_res, 'rel')
        
        self.schema = "".join([
            f"In the following, each IRI is followed by the local name and ", 
            f"optionally its description in parentheses. \n",
            f"The graph supports the following node types:\n",
            clazzes,
            f"The graph supports the following relationships:\n",
            rels,
            f"The graph supports the following OWL object properties, ",
            dtprops, 
            "The graph supports the following OWL data properties, ",
            oprops])
        
