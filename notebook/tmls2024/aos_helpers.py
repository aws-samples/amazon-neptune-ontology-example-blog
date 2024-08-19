import os
import json
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

CHUNK_INDEX="chunks"
CHUNK_EMBEDDINGS_INDEX="chunk_embeddings"

CHUNKS_INDEX_DEF = {
    "settings": {
        "number_of_replicas": 1,
        "number_of_shards": 5,
        "analysis": {
          "analyzer": {
            "default": {
              "type": "standard",
              "stopwords": "_english_"
            }
          }
        }
    },  
    "mappings": {
        "properties": {
            "embedding": {
                "type": "knn_vector",
                "dimension": 1536,  
            }
        }
    }
}

CHUNK_EMBEDDINGS_INDEX_DEF = {
    "settings": {
        "number_of_replicas": 1,
        "number_of_shards": 5,
        "index.knn": True,
        "index.knn.space_type": "cosinesimil",
        "analysis": {
          "analyzer": {
            "default": {
              "type": "standard",
              "stopwords": "_english_"
            }
          }
        }
    },   
    "mappings": {
        "properties": {
            "embedding": {
                "type": "knn_vector",
                "dimension": 1536,  
            }
        }
    }
}


# create file to bulk-load using client bulk. will be JSONl
def create_load_file(file_name):
    return open(file_name, "w")

# add record to bulk load file. 
def add_load_record(f, rec_id, rec_fields, index_name):
    j = {
        'index': {
            '_index': index_name, 
            '_id': rec_id
        }
    }
    f.write(json.dumps(j) + "\n")
    f.write(json.dumps(rec_fields) + "\n")

# close loader file
def close_load_file(f):
    f.close()
    
def connect_aos(url):
    aos_client = OpenSearch(
        hosts = [{'host': url, 'port': 443}],
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )
    return aos_client
    
def load_records_from_file(aos_client, file_name, index_name):
    with open(file_name, 'r') as file:
        file_content = file.read()
        ret = aos_client.bulk(file_content)
    return ret

def get_index(aos_client, index_name):
    return aos_client.indices.get(index=index_name)

def get_indices(aos_client):
    return aos_client.indices.get_alias(index="*")

def delete_index(aos_client, index_name):
    aos_client.indices.delete(index=index_name)

def create_index(aos_client, index_name, index_def):
    aos_client.indices.create(index=index_name,body=index_def)
     
   



    