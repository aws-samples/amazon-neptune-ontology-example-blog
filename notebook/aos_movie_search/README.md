# Demo: Make relevant movie recommendations using Amazon Neptune, Amazon Neptune Machine Learning, and Amazon OpenSearch Service

The following demo accompanies the blog post "Make relevant movie recommendations using Amazon Neptune, Amazon Neptune Machine Learning, and Amazon OpenSearch Service." 

## Solution
The blog post discusses a design for a highly searchable movie content graph database built on [Amazon Neptune](https://aws.amazon.com/neptune/), a managed graph database service. We demonstrate how to build a list of relevant movies matching a user's search criteria through the powerful combination of lexical, semantic, and graphical methods with Neptune, [Amazon OpenSearch Service](https://aws.amazon.com/opensearch-service/), and [Neptune Machine Learning](https://aws.amazon.com/neptune/machine-learning/).

We explore a solution for combined lexical, semantic, and graphical search through two lenses. First we will walk through the end-user search experience, then we will discuss populating our search data stores.

The first figure seen below, illustrates the solution from the end-user search perspective. The user first initiates a search on indices in OpenSearch Service, passing in  a search term as input. This input is first matched on lexical matches for direct keyword similarities. Next, the same input is parsed into a vector embedding representation and compared to embedding data in OpenSearch through vector similarity search. The input is then searched graphically by comparing it to graph embedding space data in OpenSearch. As a final step, the search may also explore neighbors in the Amazon Neptune graph database for locally related results. The results of steps 1, 2, and 3 will return specific node ID’s for movies within the content graph which can then be explored through graph traversals, connecting the results to connected movie titles.

![Movie Search Query](images/movie_search_query.png)
 
The next figure illustrates the second solution perspective, how the data is populated. In this solution, the primary store is a movie content data graph in Neptune. It is populated from sources such as IMDB, Rotten Tomatoes, Wikidata, and others. Our demo uses IMDB only. The OpenSearch cluster contains a copy of the movie content data in a searchable text index. OpenSearch also contains embeddings, or vector representations of movies which support nearest-neighbor search query patterns.

 ![Movie Search Ingest](images/movie_search_ingest.png)

There are two types of embeddings which we produce using [Amazon Sagemaker](https://aws.amazon.com/sagemaker/): 

1.	Embeddings which represent the text attributes of the movie, including its title, genres, and metadata. In order to turn these features into embeddings we use a Bidirectional Encoder Representations from Transformers (BERT) model. The BERT model consumes the text features as input, and outputs a vector representation of the inputs in the form of an embedding. These embeddings enable semantic matching of movie-related text.
2.	Embeddings which represent the full movie’s context and its graph neighborhood. We use [Neptune Machine Learning (Neptune ML)](https://docs.aws.amazon.com/neptune/latest/userguide/machine-learning.html) to produce embeddings based on Graph Neural Networks (GNN).  These embeddings enable graphical-similar matching of movies based on comparison of their embeddings alone. 

## Setup
To setup this solution, you need an AWS account with permission to create resources such as a Neptune cluster, and OpenSearch Service cluster, and SageMaker resources.

### Amazon Neptune Cluster Setup

Also need ML IAM role for GNN training. 
see https://s3.amazonaws.com/aws-neptune-customer-samples/v2/cloudformation-templates/neptune-ml-base-stack.json for role/policy
Do i need more?

for notebook, what instance type, what additional IAM policies

### Amazon Simple Storage Service (S3) Bucket Setup
Create an Amazon Simple Storage Service (S3) bucket in the same account and region in which you deploy the other resources. This bucket is used to store embeddings produced by Neptune ML model training.

Follow instructions in [https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html](https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html). 

### Amazon OpenSearch Service Domain Setup
Create an Amazon Neptune cluster


## Cleanup


## Cost
This solution incurs cost. Refer to pricing guides for [Neptune](https://aws.amazon.com/neptune/pricing/), [OpenSearch Service](https://aws.amazon.com/opensearch-service/pricing/), and [SageMaker](https://aws.amazon.com/sagemaker/pricing/).

