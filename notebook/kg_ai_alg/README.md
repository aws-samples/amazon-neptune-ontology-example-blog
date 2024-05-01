# KGC 2024 MasterClass: Generating and analyzing knowledge graphs using GenAI and Neptune Analytics

UNDER CONSTRUCTION

This folder contains the demo accompanying the masterclass _Generating and analyzing knowledge graphs using GenAI and Neptune Analytics_ presented at Knowledge Graph Conference 2024.

Here are instructions to setup the demo.

## Pre-requisites

You require an AWS account with permissions to create Neptune, SageMaker, and S3 resources.

Provision all resources in the same region. Use a region that supports both Neptune Analytics and Bedrock. We recommend using us-east-1 or us-west-2.

For simplicity provision all resources in the same account.

## Setup

### Allow Bedrock models

Navigate to the Bedrock console. Select _Model access_ from the left menu. Select _Manage Model Access_. If access is not already granted, check _Titan Embeddings G1_ and _Claude_ models. Save changes.

TODO - confirm you have access
TODO - screenshots

### Create Neptune Analytics Graphs

Navigate to the Neptune console. In the left menu, select _Graphs_.

#### Create main graph

Click _Create graph_.

Fill in values as follows:

- Graph name: KGC-demo
- Data source: Create empty graph
- Enable public connectivity - check
- Setup private endpoint - uncheck
- Vector search settings. Select _Use vector dimension_. When prompted for _Number of dimensions in each vector_, enter 1536.
- Select _Create Graph_.

Wait for the graph to become available. Obtain graph identifier.

#### Create graph for chatbot

Follow the same steps as above to create a second graph. Name it KGC-demo-chatbot.

### Create Neptune Notebook

Follow instructions in https://docs.aws.amazon.com/neptune-analytics/latest/userguide/create-notebook-cfn.html to create a notebook instance through CloudFormation.

TODO - IAM role allows bedrock, S3 working bucket

### Create S3 Working Bucket

Navigate to the S3 console. Create a bucket with a unique name similar to _kgc2024-masterclass-demo-yourname_.

### Create Chatbot

We also provide a chatbot to ask natural language questions of the knowledge graph.

#### Create EC2 Instance

TODO, VPC, IAM role, need public access, SG allows you to access from your machine

#### Obtain Code

git clone

#### Obtain text data

aws s3 sync _the raw data_

#### Configure

edit graph identifier

#### Get Dependencies

pip install requirements.txt

#### Start

streamlit run main.py

## Cleanup

This demo incurs cost. If you are done and wish to avoid further charges:

- Delete the Neptune Analytics graphs (TODO)
- Stop and remove the Sagemaker notebook instance (TODO)
- Remove the S3 bucket (TODO)
