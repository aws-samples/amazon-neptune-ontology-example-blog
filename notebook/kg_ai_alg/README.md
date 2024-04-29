# KGC 2024 MasterClass: Generating and analyzing knowledge graphs using GenAI and Neptune Analytics

UNDER CONSTRUCTION

This folder contains the demo accompanying the masterclass *Generating and analyzing knowledge graphs using GenAI and Neptune Analytics* presented at Knowledge Graph Conference 2024. 

Here are instructions to setup the demo.

## Pre-requisites
You require an AWS account with permissions to create Neptune, SageMaker, and S3 resources. 

Provision all resources in the same region. Use a region that supports both Neptune Analytics and Bedrock. We recommend using us-east-1 or us-west-2.

For simplicity provision all resources in the same account. 

## Setup

### Allow Bedrock models
Navigate to the Bedrock console. Select *Model access* from the left menu. Select *Manage Model Access*. If access is not already granted, check *Titan Embeddings G1* and *Claude* models. Save changes.

TODO - confirm you have access
TODO - screenshots

### Create Neptune Analytics Graphs
Navigate to the Neptune console. In the left menu, select *Graphs*.

#### Create main graph
Click *Create graph*.

Fill in values as follows:
- Graph name: KGC-demo
- Data source: Create empty graph
- Enable public connectivity - check
- Setup private endpoint - uncheck
- Vector search settings. Select *Use vector dimension*. When prompted for *Number of dimensions in each vector*, enter 1536.
- Select *Create Graph*.

Wait for the graph to become available. Obtain graph identifier.

#### Create graph for chatbot
Follow the same steps as above to create a second graph. Name it KGC-demo-chatbot.

### Create Neptune Notebook
Follow instructions in https://docs.aws.amazon.com/neptune-analytics/latest/userguide/create-notebook-cfn.html to create a notebook instance through CloudFormation.

### Create S3 Working Bucket
Navigate to the S3 console. Create a bucket with a unique name similar to *kgc2024-masterclass-demo-yourname*. 

### Create Chatbot
We also provide a chatbot to ask natural language questions of the knowledge graph

TODO


- command line
/home/ec2-user/neptune-genai-examples/llamaindex/knowledgegraphindex-chatbot-streamlit/venv/bin/python3.11 /home/ec2-user/neptune-genai-examples/llamaindex/knowledgegraphindex-chatbot-streamlit/venv/bin/streamlit run main.py


- which pip installs


- env for graph identifier

- does it need storage folders from instance?

pip install -r x/requirement.txt

Then streamlit ...

Two graphs

## Cleanup
This demo incurs cost. If you are done and wish to avoid further charges:
- Delete the Neptune Analytics graphs (TODO)
- Stop and remove the Sagemaker notebook instance (TODO)
- Remove the S3 bucket (TODO)

