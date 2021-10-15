# Amazon Neptune Ontology Blog Example

## Setup 
Use CloudFormation to setup Neptune DB, Neptune notebook, and S3 bulk loader bucket. Create a stack based on template in cfn/neptune_ontology_main.yml. It has two nested stacks using templates cfn/neptune_ontology_db.yml and cfn/neptune_ontology_workbench.yml. To setup:

1. *INTERIM - THE FOLLOWING STEP IS REQUIRED UNTIL THIS REPO IS MADE PUBLIC* Clone this repo. Create an S3 bucket. Add to the bucket the following files: example_org.ttl, tester_ontology.ttl, Neptune_Ontology_Example.ipynb, neptune_ontology_main.yml, neptune-ontology-db.yml, neptune-ontology-workbench.yml. The structure of the S3 bucket should be flat: no folders! TODO - show ls 
2. *INTERIM - THE FOLLOWING STEP IS REQUIRED UNTIL THIS REPO IS MADE PUBLIC* Edit your local copy of neptune_ontology_main.yml. Do a search and replace, replacing neptune-ontology-example-haveym with the name of your S3 bucket. Save.
3. In CloudFormation console, create a stack. For the template, upload your local copy of neptune_ontology_main.yml. Name your stack and override parameters if necessary.
4. Create! Check it succeeds!

Refer to the post (TODO - provide link) for detailed setup instructions.

** Note on interim approach: The CloudFormation template uses custom resource repo2S3 to download all the files it needs. It is meant to download these files from the git repo. But until the repo is public, it needs some other place to download them from. That place is S3, specifically the bucket you created in step 1 above. 

## Running the Examples
Once the setup is complete, in the console open the Neptune notebook that is created. From the Jupyter menu then select Neptune_Ontology_Example.ipynb. Once open, follow the steps; it gives you a guided tour! You will be loading into Neptune three Turtle RDF files: example_org.ttl and tester_ontology.ttl (included in the data folder of the repo) and org.ttl (downloaded from http://www.w3.org/ns/org.ttl during CFN setup). You will then be querying and validating this data. 

## Cleanup
To cleanup, delete the main stack that you created above. In CloudFormation, choose the stack based on template cfn/neptune_ontology_main.yml. Delete it.

## License
This library is licensed under the MIT-0 License. See the LICENSE file.

