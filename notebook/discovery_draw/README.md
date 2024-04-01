# Discover and Draw Neptune Graph Schema

The notebooks in this folder show how to discovery and draw the graph schema in your Amazon Neptune database. We discover by introspecting the main types of nodes, edges, and resources using the Neptune Summary API plus graph queries. 

Neptune supports both Labeled Property Graph (LPG) and Resource Description Framework (RDF) graph representations. We provide separate notebooks for each.

We use PlantUML, a diagram-as-code tool, to draw the graph schemas. PlantUML renders the diagrams directly in the notebook, but also saves them as SVG files in your notebook folder.

To run these notebooks, you need an exiting SageMaker Notebook instance configured with the Neptune graph notebook.

## Discover and Draw LPG
To draw your property graph schema as a UML class diagram, copy the following files a folder in your notebook instance:

- VisualizeModel-LPG.ipynb
- lpg_discovery.py

Open VisualizeModel-LPG.ipynb. Run through the steps. 

## Discover and Draw RDF
To draw your RDF schema as a UML class diagram, copy the following files a folder in your notebook instance:

- VisualizeModel-RDF.ipynb
- rdf_discovery.py
- prefixes.txt

Open VisualizeModel-RDF.ipynb. Run through the steps. 

Note that the UML diagram created is not meant to depict an ontology. Rather it summarizes the contents of your graph into a simple set of classes and class relationships. Use a full-fledged ontology editor if you are interested to visually navigate and design an ontology.

