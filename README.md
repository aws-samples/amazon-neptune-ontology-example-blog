# Amazon Neptune Ontology and Multimodel Blog Example

## Prerequisites
To run this example, you need an AWS account with permission to create resources such as a Neptune cluster. 

## Provision resources
Create Neptune resources using AWS CloudFormation. Download a copy of the CloudFormation template (cfn/neptune_ontology_main.yml) from this repository. Then complete the following steps:

1.	On the AWS CloudFormation console, choose **Create stack**.
2.	Choose **With new resources (standard)**.
3.	Select U**pload a template file**.  
4.	Choose **Choose file** to upload the local copy of the template that you downloaded. The name of the file is Neptune_ontology_main.yml. 
5.	Choose **Next**.
6.	Enter a stack name of your choosing. 
7.	In the **Parameters** section, use defaults for the remaining parameters.
8.	Choose **Next**.
9.	Continue through the remaining sections.
10.	Read and select the check boxes in the **Capabilities** section.
11.	Choose **Create stack**.
12.	When the stack is complete, navigate to the **Outputs** section and follow the link for the output NeptuneSagemakerNotebook. 

This opens in your browser the Jupyter files view. There are two notebooks available: 
- Neptune_Multimodel.ipynb, demonstrating the multimodel example
- Neptune_Ontology_Example.ipynb, demonstrating the ontology example in <https://aws.amazon.com/blogs/database/model-driven-graphs-using-owl-in-amazon-neptune>.

We encourage you to review the stack with your security team prior to using it in a production environment.

## Running the Examples
To run the ontology example discussed in the blog <https://aws.amazon.com/blogs/database/model-driven-graphs-using-owl-in-amazon-neptune>, open the Neptune_Ontology_Example.ipynb notebook; then follow the steps! 

To run the multimodel example discussed in the blog <TBD>, open the Neptune_Multimodel.ipynb notebook and follow the steps.

## Cost
The template creates Neptune cluster resources, a SageMaker notebook (Neptune Workbench), an S3 bucket, plus additional resources. The Neptune cluster and SageMaker notebook incur costs.  Refer to the Neptune pricing guide <https://aws.amazon.com/neptune/pricing/> for pricing. 

## Clean up
If you’re done with the solution and wish to avoid future charges, delete the CloudFormation stack. 

## License
This library is licensed under the MIT-0 License. See the LICENSE file.

