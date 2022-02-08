# Amazon Neptune Ontology Blog Example

## Setup 
Use CloudFormation to setup Neptune DB, Neptune notebook, and S3 bulk loader bucket. Create a stack based on template in cfn/neptune_ontology_main.yml. It has two nested stacks using templates cfn/neptune_ontology_db.yml and cfn/neptune_ontology_workbench.yml. To setup:

1. Clone this repo. 
2. In CloudFormation console, create a stack. For the template, upload your local copy of neptune_ontology_main.yml. Name your stack and override parameters if necessary.
3. Create! Check it succeeds!

## Running the Examples
Once the setup is complete, in the console open the Neptune notebook that is created. From the Jupyter menu then select Neptune_Ontology_Example.ipynb. Once open, follow the steps; it gives you a guided tour! You will be loading into Neptune three Turtle RDF files: example_org.ttl and tester_ontology.ttl (included in the data folder of the repo) and org.ttl (downloaded from http://www.w3.org/ns/org.ttl during CFN setup). You will then be querying and validating this data. 

## Cleanup
To cleanup, delete the main stack that you created above. In CloudFormation, choose the stack based on template cfn/neptune_ontology_main.yml. Delete it.

## License
This library is licensed under the MIT-0 License. See the LICENSE file.

