# Amazon Neptune Ontology and Multimodel Blog Example

## Setup 
Use CloudFormation to setup Neptune DB, Neptune notebook, and S3 bulk loader bucket. Create a stack based on template in cfn/neptune_ontology_main.yml.To setup:

1. Clone this repo. 
2. In CloudFormation console, create a stack. For the template, upload your local copy of neptune_ontology_main.yml. Name your stack and override parameters if necessary.
3. Create! Check it succeeds!

## Running the Examples
Once the setup is complete, open the Sagemaker notebook instance. You can find the link in the Outputs section of the CloudFormation stack. The link opens the Jupyter file fiew. 

To run the ontology example discussed in the blog <https://aws.amazon.com/blogs/database/model-driven-graphs-using-owl-in-amazon-neptune>, open the Neptune_Ontology_Example.ipynb notebook; then follow the steps! 

To run the multimodel example discussed in the blog <TBD>, open the Neptune_Multimodel.ipynb notebook and follow the steps.

## Cleanup
To cleanup, delete the main stack that you created above. In CloudFormation, choose the stack based on template cfn/neptune_ontology_main.yml. Delete it.

## License
This library is licensed under the MIT-0 License. See the LICENSE file.

