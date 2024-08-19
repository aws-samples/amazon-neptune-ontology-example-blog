from rdflib import Graph, Literal, RDF, RDFS, URIRef, XSD, OWL, BNode, DC, SKOS

NS = "http://example.org/orgdemo" # default, but override as you see fit
NS_XROLE = f"{NS}/xrole" 
NS_XENT = f"{NS}/xent" 
NS_XEV = f"{NS}/xev" 

def rdf_open():
    return Graph()
    
def rdf_write(ff, s, p, o):
    ff.add((s, p, o))

def rdf_close(ff, filename):
    ff.serialize(destination = filename, format='turtle')
    
def make_uri(name, pfx=NS):
    return URIRef(f"{pfx}/{name}")
