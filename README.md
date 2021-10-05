# Amazon Neptune Ontology Blog Example

## Setup
Use CloudFormation to setup Neptune DB, Neptune notebook, and S3 bulk loader bucket. Create a stack based on template in cfn/neptune_ontology_main.yml. It has two nested stacks using templates cfn/neptune_ontology_db.yml and cfn/neptune_ontology_workbench.yml. 

(Until this is in a public repo, there is something you will need to tweak!!! Note that the setup includes pulling in the source code from a Git repo. This is done using the custom resource repo2S3 in the main template. The source_repo repo property points to the URL of the repo. It is hardcoded. But until this repo is ready to be committed to a repo, you should pull the code from a private S3 bucket instead. To do this, create an S3 bucket, and change the value of source_repo to be the S3 URL of the bucket. I harded it to "s3://neptune-ontology-example-haveym". Adjust it for your bucket.

Here is a summary of what the template does:
- Creates a private S3 bucket for Neptune load.
- Copies from public Git repo (or source S3 bucket) to the target S3 loader bucket the files in cfn, data, and notebook. It also downloads into the target bucket the W3C ontology org.ttl from http://www.w3.org/ns/org.ttl. org.ttl is NOT included in the repo.
- Creates a private Neptune DB cluster and the VPC in which it is to reside. Also creates an S3 endpoint to access S3 from Neptune for loads. 
- Creates a Neptune notebook in the same VPC and copies to it notebook/Neptune_Ontology_example.ipynb.


## Running the Examples
Once the setup is complete, in the console open the Neptune notebook that is created. From the Jupyter menu then select Neptune_Ontology_Example.ipynb. Once open, follow the steps; it gives you a guided tour! You will be loading into Neptune three Turtle RDF files: example_org.ttl and tester_ontology.ttl (included in the data folder of the repo) and org.ttl (downloaded from http://www.w3.org/ns/org.ttl during CFN setup). You will then be querying and validating this data. 


## Cleanup
To cleanup, delete the main stack that you created above. In CloudFormation, choose the stack based on template cfn/neptune_ontology_main.yml. Delete it.

## License
This library is licensed under the MIT-0 License. See the LICENSE file.

