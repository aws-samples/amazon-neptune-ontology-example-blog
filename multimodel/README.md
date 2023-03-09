# Using Amazon Neptune to Model a Multimodel Database Solution

This is an example accompanying my talk/blog post on multi modeling. It shows how an ontology to model data products in a multi-model solution. It also shows the use of Knowledge Graph as one model within the multimodel. 

## Pre-requisite
You need an AWS account.
You need an Amazon Neptune cluster with a Neptune Workbench notebook instance.
You need an S3 bucket in the same region as your Neptune cluster. Your Neptune cluster needs an IAM role with read access to the bucket.
Your notebook instance sneeds read/write access to that S3 bucket.

## Steps to setup:
1. Clone this repo.
2. In your notebook instance, select the Jupyter files tab. Upload your local cloned copy of MultiModel.ipynb (in the multimodel folder).
3. Open the MultiModel.ipynb notebook in Jupyter.
4. Follow the steps described in the notebook. You need to make one edit. In the code cell under "Set the name of an S3 bucket in the same region that Neptune has access to", edit your S3 bucket name as the value of S3_BUCKET.

## License
The ontology and notebook are licensed under the MIT-0 License. See the LICENSE file.
