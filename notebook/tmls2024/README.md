# Toronto Machine Learning Summit 2024: Ask the Graph: How Knowledge Graphs Helps Generative AI Models Answer Questions

## Introduction

This folder contains the demo accompanying the presentation _Ask the Graph: How Knowledge Graphs Helps Generative AI Models Answer Questions_ presented at the Toronto Machine Learning Summit 2024 (<https://www.torontomachinelearning.com/speakers/#agenda>). It also provides the code sample for a blog post on modeling a knowledge graph in Amazon Neptune (https://aws.amazon.com/neptune/) for generative AI-driven question-and-answer (Q&A). 

Neptune supports the two leading graph representations: [Resource Description Framework (RDF)](https://www.w3.org/RDF/) and [Labeled Property Graph](https://tinkerpop.apache.org/). This code sample focuses on RDF. We show how to build an RDF knowledge graph in Neptune that can answer natural language questions about organizations. Additionally, we demonstrate the *extreme searchability* of the graph. We design the graph so that we can find resources and discover their relationships with simple templated queries that allow fuzzy match and the use of alternative names. That extreme searchability is a necessary ingredient for answering natural language questions. Putting aside Q&A, extreme searchability is beneficial in its own right.

## The solution in three diagrams
In this section, we depict the solution you will build from this repo. The first shows how a user asks a question that is answered by the knowledge graph. 

![XSKG solution](images/xskg_overall.png "Overall solution"). 

The solution uses the following AWS services:

- Amazon Neptune to host the RDF knowledge graph
- Optionally, a Neptune Analytics graph, enabling you to run analytical queries and graph algorithms on the data to further research the question.
- An Amazon OpenSearch Service domain as a search index. It allows you to find press releases using semantic search based on vector embedding similarity. It also provides powerful lexical search of the graph data in Neptune. Both capabilities are critical to answering natural language questions.
- Amazon Bedrock to invoke LLMs to perform entity extraction and embedding creation.
- An Amazon SageMaker notebook instance, which acts as a test client to prepare and load the graph data, as well as to ask questions and make follow-up queries to further research the question.
- Neptune Graph Explorer, a low-code visualization UI to explore the graph. You can find resources related to the question and discover additional relationships.


<img width="301" alt="image" src="https://github.com/user-attachments/assets/e2a5fb75-126a-40e1-9c60-5a14b09c4c42">

This folder contains the demo accompanying the presentation _Ask the Graph: How Knowledge Graphs Helps Generative AI Models Answer 

We can find resources with generic queries ... in it easily, without having We can find resources in the graph through simple queries various ways to query the graph directly to find content in it. 


We support natural language questions of an RDF graph using the following solution: TODO image and wording.

Here is the data model: TODO image and wording

Here is how we ingest data into the model: TODO image and wording

## Setup
To setup this solution, you need an AWS account with permission to create resources such as a Neptune cluster, and OpenSearch Service cluster, S3 bucket, and SageMaker resources. Also select a single region in which to deploy your resources, ensure that Amazon Neptune, Amazon OpenSearch Service, Amazon Sagemaker, and S3 are all available for deployment in said region.

### Allow Bedrock models
In your AWS console, open the Bedrock console and request model access for the _Titan Embeddings G1_ and _Claude_ models. For instructions how to request model access, follow <https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html>.

Check back until both models show as _Access granted_.

![Bedrock model access](images/bedrock_model_access.png "Bedrock model access"). 

### Create Amazon Simple Storage Service (S3) Bucket
Create an Amazon Simple Storage Service (S3) bucket in the same account and region in which you deploy the other resources. This bucket is used to store embeddings produced by Neptune ML model training.

Follow instructions in [https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html](https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html). The bucket may be private and use default encryption. Take note of your bucket name and resource ARN for upcoming deployment steps.

### Setup Amazon Neptune Cluster
Create a Neptune cluster and a notebook instance. One way to setup these resources is using the CloudForamtion template via [https://docs.aws.amazon.com/neptune/latest/userguide/get-started-cfn-create.html](https://docs.aws.amazon.com/neptune/latest/userguide/get-started-cfn-create.html). We recommend using a `NotebookInstanceType` of `ml.t3.medium` or higher.

When the CloudFormation stack completes, locate the Neptune cluster and *make note of its VPC and subnets*. You will need these when creating the OpenSearch Service domain to ensure you create resources that can connect to eachother.

![Neptune Connection Items](images/neptune_strings.png) TODO borrow from movie search

### Setup Amazon OpenSearch Service Domain
In the Opensearch Service console, create a new domain as follows;
- Use standard create.
- Choose `Dev/test` template.
- Choose `Domain without standby` with `1-AZ` deployment option.
- Use version OpenSearch 2.7 or higher.
- Under `network`, choose the same VPC in which your Neptune cluster is deployed. For subnets, choose one of the subnets under the Neptune cluster.
- For security group, use a security group allowing inbound access to port 443.
- Disable fine-grained access control.

Once setup, *make note of the domain endpoint*. You will need it when running through the notebooks.

For more on creating domains, see [https://docs.aws.amazon.com/opensearch-service/latest/developerguide/createupdatedomains.html](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/createupdatedomains.html). 

### Enable Full-Text Search on Amazon Neptune Cluster

TODO

### Modify IAM Role in Notebook Instance 

In the SageMaker console, locate the notebook instance that was created by the Neptune cluster CloudFormation stack. Find its IAM role under `Permissions and encryption` on the details page for the notebook. Select that role and add IAM policies as follows:

![Neptune Notebook Role ARN](images/notebook_arn.png) TODO image from movie search

- The notebook should already have read access to all S3 buckets. Add write access to the S3 bucket you created above. One way to accomplish this is to add the `AmazonS3FullAccess` managed policy.
- The notebook should be able to read from and write to your Amazon OpenSearch Service Domain. One way to accomplish this is to add the `AmazonOpenSearchServiceFullAccess` managed policy.
- TODO: comprehend
- TODO: bedrock
- TODO: analytics

### (OPTIONAL) Create Neptune Analytics Graph

In your AWS console, open the Neptune console. In the left menu, select _Graphs_ to create a graph. 

Follow instructions <https://docs.aws.amazon.com/neptune-analytics/latest/userguide/gettingStarted-creating-a-graph.html> to create the graph. 

Use the following settings: 
- Graph name: *tmls*
- Data source: Create empty graph
- Enable public connectivity: check
- Setup private endpoint: uncheck
- Vector search settings: Enable these settings and set dimension to *1536*.

It will take a few minutes to create. Wait for the status of the graph to become *Available*. 

TODO - find the graph endpoint ...

### Use the notebooks

From this repository, download the four notebooks and supporting Python source files:

- 0-PrepStructured.ipynb
- 1-PrepUnstructured.ipynb
- 2-IngestData.ipynb
- 3-Query.ipynb
- ai_helpers.py
- aos_helpers.py
- neptune_helpers.py
- rdf_helpers.py
- query_helpers.py

Back in the SageMaker console, open the Jupyter notebook folder view

![jupyter](images/jupyter.png "jupyter"). TODO image

In Jupyter, upload the above files from your local copy:

![jupyter notebooks upload](images/jupyter_upload.png "jupyter notebooks upload"). TODO image

In the same folder on the notebook instance, create a file called ```.env``` with the following contents:

```
AOS_ENDPOINT_HOST=<your OpenSearch Service domain host>
S3_BUCKET_NOSLASH=<your S3 bucket and folder (if any). Do NOT end with a slash>
GRAPH_IDENTIFIER=<your Neptune Analytics graph identifier (OPTIONAL)>
```

Now run through the notebooks! *0-PrepStructured.ipynb* and *1-PrepUnsructured.ipynb* are optional, meant mostly to show how we prepared the data. You may skip these as the prepared data is already available publicly.

## Cleanup

This demo incurs cost. If you are done and wish to avoid further charges:

- Delete the CloudFormation stack you created for the Neptune cluster and notebook instance. See <https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-console-delete-stack.html> for instructions how to delete a stack.
- Delete the Neptune Analytics graphs. The Neptune console provides an action to delete a graph. Or see <https://docs.aws.amazon.com/neptune-analytics/latest/apiref/API_DeleteGraph.html>. 
- Remove the S3 bucket. See <https://docs.aws.amazon.com/AmazonS3/latest/userguide/delete-bucket.html>.
- Delete the OpenSearch Service domain you created. You may do this from the Opensearch Service console. Or see [https://awscli.amazonaws.com/v2/documentation/api/2.7.12/reference/opensearch/delete-domain.html](https://awscli.amazonaws.com/v2/documentation/api/2.7.12/reference/opensearch/delete-domain.html). 

## Cost
This solution incurs cost. Refer to pricing guides for [Neptune](https://aws.amazon.com/neptune/pricing/), [S3](https://aws.amazon.com/s3/pricing/), [OpenSearch Service](https://aws.amazon.com/opensearch-service/pricing/), and [SageMaker](https://aws.amazon.com/sagemaker/pricing/).
