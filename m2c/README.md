# Bringing Media2Cloud Video Analysis into Amazon Neptune Knowledge Graph

... THIS IS BEING MOVED SOON ....

This is an example accompanying my blog post on linking AI video analysis of the AWS Media2Cloud solution (https://aws.amazon.com/solutions/implementations/media2cloud/) with an Amazon Neptune knowledge graph. Refer to the blog post for a full step-to-step setup and exploration.

We refer to Media2Cloud as M2C throughout.

## Pre-requisite
- You need an Amazon Neptune cluster with a Neptune Workbench notebook instance.  To create using CloudFormation, see https://docs.aws.amazon.com/neptune/latest/userguide/neptune-setup.html. 
- You need to install Media2Cloud by launching its CloudFormation stack. This is discussed in https://docs.aws.amazon.com/solutions/latest/media2cloud-on-aws/automated-deployment.html#step-1.-launch-the-stack.
- Your notebook instance needs read/write access to that S3 bucket. If you created Neptune cluster using the CloudFormation template above, this step is not needed. Otherwise, find the IAM role for your notebook instance and add a policy to enable that S3 access.  See https://docs.aws.amazon.com/sagemaker/latest/dg/gs-setup-working-env.html.

## Steps to setup:
1. Create Neptune cluster if you do not have one to test on.
2. Create M2C application. Make note of the name of the analysis (or proxy) bucket.
3. Clone this repo.
4. In your notebook instance, select the Jupyter files tab. Upload your local cloned copy of M2CForKnowledgeGraph.ipynb (in the m2c folder).
5. Open the M2CForKnowledgeGraph.ipynb notebook in Jupyter.
6. Follow the steps described in the notebook. You need to make one edit. In the code cell under "Set the name of the M2C S3 Analysis bucket", change the value of ANALYSIS_BUCKET to the name of your M2C analysis/proxy bucket.

Setup steps are discussed in detail in the blog post.

## License
The ontology and notebook are licensed under the MIT-0 License. See the LICENSE file.
