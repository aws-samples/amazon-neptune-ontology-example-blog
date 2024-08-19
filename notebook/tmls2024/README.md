# Toronto Machine Learning Summit 2024: Ask the Graph: How Knowledge Graphs Helps Generative AI Models Answer Questions

TODO
setup
- create S3 bucket
- neptune cluster
- add IAM role - s3 access for neptune cluster
- AOS domain
- enable streaming, restart neptune cluster
- install FTS
- change perms on notebook: bedrock, s3, comprehend, ...


Then in notebook open a terminal and go a git clone. Folders will be

xskg/README, 4 notebooks, 3 pythons
xskg/source/rdf





This folder contains the demo accompanying the presentation _Ask the Graph: How Knowledge Graphs Helps Generative AI Models Answer Questions_ presented at the Toronto Machine Learning Summit 2024 (<https://www.torontomachinelearning.com/speakers/#agenda>). 

This is actually two demos in one. We show how to ask natural language questions of a knowledge graph represented as either Labeled Property Graph (LPG) or Resource Description Framework (RDF). Both approaches use Amazon Neptune.

The following figure shows the LPG architecture. We use a Neptune Analytics graph. We use a SageMaker notebook as a client to populate the graph and run natural language queries of it. We use Comprehend for entity extraction, and Anthropic and Titan LLMs via Bedrock for Q&A and embeddings. 

TODO figure

The next figure shows the RDF architecture. We use a Neptune database cluster in conjunction with an Amazon OpenSearch Service domain. We use a SageMaker notebook as a client to populate the graph and run natural language queries of it. We use Comprehend for entity extraction, and Anthropic and Titan LLMs via Bedrock for Q&A and embeddings. The RDF demo is UNDER CONSTRUCTION. Watch this page for updates.

TODO figure

Here is the data model that the demos use.
TODO figure. 

Here are instructions to setup the demo.

## Pre-requisites

<details><summary>Click to view/hide this section</summary>
<p>


You require an AWS account with permissions to create Amazon Neptune (<https://aws.amazon.com/neptune>), Amazon Bedrock (<https://aws.amazon.com/bedrock>), Amazon SageMaker (<https://aws.amazon.com/sagemaker>), and Amazon OpenSearch Service (<https://aws.amazon.com/opensearch-service/>) resources.

Provision all resources in either us-east-1 or us-west-2 regions. For simplicity, provision all resources in the same AWS account.

</p>
</details>

## Setup

### Common setup

#### Allow Bedrock models

<details><summary>Click to view/hide this section</summary>
<p>

In your AWS console, open the Bedrock console and request model access for the _Titan Embeddings G1_ and _Claude_ models. For instructions how to request model access, follow <https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html>.

Check back until both models show as _Access granted_.

![Bedrock model access](../kg_ai_alg/images/bedrock_model_access.png "Bedrock model access").

</p>
</details>

### LPG Demo Setup

#### Create Neptune Analytics Graph

<details><summary>Click to view/hide this section</summary>
<p>

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

</p>
</details>

#### Create Neptune Notebook

<details><summary>Click to view/hide this section</summary>
<p>


Follow instructions in https://docs.aws.amazon.com/neptune-analytics/latest/userguide/create-notebook-cfn.html to create a Sagemaker notebook instance for Neptune Analytics through CloudFormation. On the stack details page provide the following:

- Stack name: *tmls-LPGDemo*
- GraphEndpoint: enter the endpoint from the *tmls* graph you created above.
- NotebookName: *tmls-LPG-notebook*

Leave the remaining parameters blank. Navigate through the remaining pages, accepting defaults.

![notebook params](images/na_notebook.png "notebook params").

Wait for the CloudFormation stack to complete. It may take several minutes.

#### Modify Notebook IAM Role

When complete, go the SageMaker console. In the left menu select _Notebook_. Locate your notebook in the main pane. 

![notebook_created](images/sm_notebook.png "notebook created").

Select the notebook to see its configuration. Locate its IAM role. Click on that role to bring it up in the IAM console.

Add two policies to the permissions: 

- *AmazonBedrockFullAccess*, giving the notebook access to invoke Bedrock models for embedding and entity extraction

TODO change
![change notebook role](images/iam_notebook.png "change notebook role").

If you prefer narrower permissions, create your own policy that restricts S3 writes to only your working bucket and Bedrock invokes to only the Claude and Titan models.


#### Get Demo Notebook Files and Begin

TODO ... 

Download the four notebooks from this repository:

- 0-PrepSources.ipynb
- 1-PopulateGraph.ipynb
- 2-CreateLlamaIndex.ipynb
- 3-GraphAlgorithms.ipynb

Back in the SageMaker console, open the Jupyter notebook folder view

![jupyter](images/jupyter.png "jupyter").

In Jupyter, upload the four notebooks should downloaded to your local machine above.

![jupyter notebooks upload](images/jupyter_upload.png "jupyter notebooks upload").

Now run through the notebooks! *0-PrepSources.ipynb* is optional, meant mostly to show how we prepared the data. You may skip this as the prepared data is already available publicly.

</p>
</details>




## Cleanup

<details><summary>Click to view/hide this section</summary>
<p>

This demo incurs cost. If you are done and wish to avoid further charges:

- Delete the Neptune Analytics graphs. The Neptune console provides an action to delete a graph. Or see <https://docs.aws.amazon.com/neptune-analytics/latest/apiref/API_DeleteGraph.html>. 
- Stop and remove the Sagemaker notebook instance. For this, delete the CloudFormation stack you created for the notebook. See <https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-console-delete-stack.html> for instructions how to delete a stack.
- Remove the S3 bucket. See <https://docs.aws.amazon.com/AmazonS3/latest/userguide/delete-bucket.html>.
- Terminate the EC2 instance. See <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/terminating-instances.html>.

</p>
</details>
