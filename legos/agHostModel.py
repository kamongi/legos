import os, urllib, datetime, time, sys
import getpass

from franz.openrdf.sail.allegrographserver import AllegroGraphServer
from franz.openrdf.repository.repository import Repository
from franz.miniclient import repository
from franz.openrdf.query.query import QueryLanguage
from franz.openrdf.model import URI
from franz.openrdf.vocabulary.rdf import RDF
from franz.openrdf.vocabulary.rdfs import RDFS
from franz.openrdf.vocabulary.owl import OWL
from franz.openrdf.vocabulary.xmlschema import XMLSchema
from franz.openrdf.query.dataset import Dataset
from franz.openrdf.rio.rdfformat import RDFFormat
from franz.openrdf.rio.rdfwriter import  NTriplesWriter
from franz.openrdf.rio.rdfxmlwriter import RDFXMLWriter

from legos.hostInfo import hostDetails
from legos.input_type import Inputs

class HostMets:
	""" 
	It implements various methods to automatically model and instantiate a generic host 
		running an Ubuntu 16.04 or later OS.

	Depends on:
		:: AllegroGraph (AG) graph database (6.2.2 Server & Python Client versions)
		:: Generate an AG repository (Ontology Knowledge Base) for the Host Model domain.
	"""

	def __init__(self, inObj):
		""" Class scoped variables and data """

		self.conn 			= inObj.conn
		self.namespaces 	= self.initNamespaces()
		self.hostModelURIs 	= self.GenericHostDomain()
		self.hostingObj 	= hostDetails()
		self.repoName 		= inObj.repoName

	def initNamespaces(self):
		""" Define key namespaces """

		namespacesDict = {}
		
		## Global namespace
		namespacesDict["exns"] 		= "http://www.semanticweb.org/csrl/ontologies/2016/10/ontology/" # To keep track of our data model predicates & classes
		
		## Cloud/Host model specific
		namespacesDict["exnsH"]    	= "http://www.semanticweb.org/csrl/ontologies/2016/10/ontology/Hosts/" # To keep track of our hosts
		namespacesDict["exnsS"]    	= "http://www.semanticweb.org/csrl/ontologies/2016/10/ontology/Services/" # To keep track of our services
		namespacesDict["exnsProd"] 	= "http://www.semanticweb.org/csrl/ontologies/2016/10/ontology/ItProducts/" # To keep track of our IT Products (mainly Packages)

		return namespacesDict

	def AddHostInstances(self):
		""" Add our cloud system hosts' details """

		# Read in near-real time.
		hostName 	 	= self.hostingObj.hostName # i.e., "ubuntu"
		hostOS 		 	= self.hostingObj.hostOS # i.e., "Ubuntu 16.04.4 LTS"
		hostPublicIP 	= self.hostingObj.hostPublicIP # i.e., "192.168.2.41"
		hostIPs 		= self.hostingObj.hostIPs # i.e., "["192.168.2.41", "x.x.x.x"]"
 
		# Host details
		hostInstance = self.conn.createURI(namespace=self.namespaces['exnsH'], localname=str(hostName + "-" + hostIPs[0]))
		self.conn.add(hostInstance, RDF.TYPE, self.hostModelURIs["GenericHost"])

		hostNameInstance = self.conn.createLiteral(str(hostName), datatype=XMLSchema.STRING)
		self.conn.add(hostInstance, self.hostModelURIs["hasHostName"], hostNameInstance)
		
		hostOSInstance = self.conn.createLiteral(str(hostOS), datatype=XMLSchema.STRING)
		self.conn.add(hostInstance, self.hostModelURIs["hasHostOS"], hostOSInstance)

		hasHostPublicIPInstance = self.conn.createLiteral(str(hostPublicIP), datatype=XMLSchema.STRING)
		self.conn.add(hostInstance, self.hostModelURIs["hasHostPublicIP"], hasHostPublicIPInstance)

		for hostIP in hostIPs:
			hasHostIPInstance = self.conn.createLiteral(str(hostIP), datatype=XMLSchema.STRING)
			self.conn.add(hostInstance, self.hostModelURIs["hasHostIP"], hasHostIPInstance)

		return hostName, hostInstance

	def addHostPackages(self, hostName, hostInstance):
		""" For each Host add all installed Packages details into our OKB """

		for product, version in self.hostingObj.packages.iteritems():

			itProdInstance = self.conn.createURI(namespace=self.namespaces['exnsProd'], localname=str(product))

			self.conn.add(itProdInstance, RDF.TYPE, self.hostModelURIs["Package"])
			self.conn.add(itProdInstance, self.hostModelURIs["installedOn"], hostInstance)

			productTemp = self.conn.createLiteral(str(product), datatype=XMLSchema.STRING)
			self.conn.add(itProdInstance, self.hostModelURIs["hasProduct"], productTemp)
			versionTemp = self.conn.createLiteral(str(version), datatype=XMLSchema.STRING)
			self.conn.add(itProdInstance, self.hostModelURIs["hasVersion"], versionTemp)

		return "Done."

	def addHostPackagesDependencies(self, hostName, hostInstance):
		""" For each Host's installed Packages add their dependency packages details into our OKB """

		for product, dependencies in self.hostingObj.packagesDependencies.iteritems():

			dependencies = dependencies.split("->")

			itProdInstance = self.conn.createURI(namespace=self.namespaces['exnsProd'], localname=str(product))
			self.conn.add(itProdInstance, RDF.TYPE, self.hostModelURIs["Package"])

			for subDep in dependencies:

				subDep = subDep.replace(" ", "")
				subDep = subDep.split("|") # We consider both options. There could be cases where there are more than 2 options.

				if len(subDep) == 2:
					dependencyInstance1 = self.conn.createURI(namespace=self.namespaces['exnsProd'], localname=str(subDep[0]))
					self.conn.add(dependencyInstance1, RDF.TYPE, self.hostModelURIs["Package"])
					self.conn.add(itProdInstance, self.hostModelURIs["hasDependency"], dependencyInstance1)

					dependencyInstance2 = self.conn.createURI(namespace=self.namespaces['exnsProd'], localname=str(subDep[1]))
					self.conn.add(dependencyInstance2, RDF.TYPE, self.hostModelURIs["Package"])
					self.conn.add(itProdInstance, self.hostModelURIs["hasDependency"], dependencyInstance2)

				else:
					if subDep[0] == '':
						continue
					else:
						dependencyInstance = self.conn.createURI(namespace=self.namespaces['exnsProd'], localname=str(subDep[0]))
						self.conn.add(dependencyInstance, RDF.TYPE, self.hostModelURIs["Package"])
						self.conn.add(itProdInstance, self.hostModelURIs["hasDependency"], dependencyInstance)

		return "Done."

	def GenericHostDomain(self):
		""" 
			Defines a host (Physical/VM/Container running any OS) model ontology 
			using any given Host based on any VM/Containter running Ubuntu 16.04 Linux based OS . 
		"""

		hostModelURIs = {}

		# Classes resources
		GenericHost 	= self.conn.createURI(namespace=self.namespaces['exns'], localname="GenericHost")
		hostModelURIs["GenericHost"] = GenericHost

		Cpe 			= self.conn.createURI(namespace=self.namespaces['exns'], localname="Cpe")
		hostModelURIs["Cpe"] = Cpe

		CpeItem 		= self.conn.createURI(namespace=self.namespaces['exns'], localname="CpeItem")
		self.conn.add(CpeItem, RDFS.SUBCLASSOF, Cpe)
		hostModelURIs["CpeItem"] = CpeItem

		Package 		= self.conn.createURI(namespace=self.namespaces['exns'], localname="Package")
		self.conn.add(Package, RDFS.SUBCLASSOF, GenericHost)
		hostModelURIs["Package"] = Package

		# Object properties / attributes
		hasCpeItem         = self.conn.createURI(namespace=self.namespaces['exns'], localname="hasCpeItem")
		self.conn.add(hasCpeItem, RDFS.DOMAIN, Package)
		self.conn.add(hasCpeItem, RDFS.RANGE, CpeItem)
		hostModelURIs["hasCpeItem"] = hasCpeItem

		hasDependency         = self.conn.createURI(namespace=self.namespaces['exns'], localname="hasDependency")
		self.conn.add(hasDependency, RDFS.DOMAIN, Package)
		self.conn.add(hasDependency, RDFS.RANGE, Package)
		hostModelURIs["hasDependency"] = hasDependency

		isDependencyOf         = self.conn.createURI(namespace=self.namespaces['exns'], localname="isDependencyOf")
		self.conn.add(isDependencyOf, OWL.INVERSEOF, hasDependency) # Through inferences, its matching triples can be found
		hostModelURIs["isDependencyOf"] = isDependencyOf

		installedOn 		= self.conn.createURI(namespace=self.namespaces['exns'], localname="installedOn")
		self.conn.add(installedOn, RDFS.DOMAIN, Package)
		self.conn.add(installedOn, RDFS.RANGE, GenericHost)
		hostModelURIs["installedOn"] = installedOn

		# Data properties / attributes
		## All of these are of datatype=XMLSchema.STRING
		hasHostName               = self.conn.createURI(namespace=self.namespaces['exns'], localname="hasHostName")
		self.conn.add(hasHostName, RDFS.DOMAIN, GenericHost)
		hostModelURIs["hasHostName"] = hasHostName

		hasHostOS               = self.conn.createURI(namespace=self.namespaces['exns'], localname="hasHostOS")
		self.conn.add(hasHostOS, RDFS.DOMAIN, GenericHost)
		hostModelURIs["hasHostOS"] = hasHostOS

		hasHostPublicIP               = self.conn.createURI(namespace=self.namespaces['exns'], localname="hasHostPublicIP")
		self.conn.add(hasHostPublicIP, RDFS.DOMAIN, GenericHost)
		hostModelURIs["hasHostPublicIP"] = hasHostPublicIP

		hasHostIP               = self.conn.createURI(namespace=self.namespaces['exns'], localname="hasHostIP")
		self.conn.add(hasHostIP, RDFS.DOMAIN, GenericHost)
		hostModelURIs["hasHostIP"] = hasHostIP

		hasProduct               = self.conn.createURI(namespace=self.namespaces['exns'], localname="hasProduct")
		self.conn.add(hasProduct, RDFS.DOMAIN, Package)
		hostModelURIs["hasProduct"] = hasProduct

		hasVersion               = self.conn.createURI(namespace=self.namespaces['exns'], localname="hasVersion")
		self.conn.add(hasVersion, RDFS.DOMAIN, Package)
		hostModelURIs["hasVersion"] = hasVersion

		print "\nHost's - Packages ontology definition has been created.\n"

		return hostModelURIs

	def hostModelMethod(self):
		""" 
		Instantiate our host model using any host running an ubuntu 16.04 or later info:
			- Packages
			- Packages dependencies
			- Other host info (hostname, os, public_ip, etc.) 
		"""

		print "\nHost Info Status					: ", self.hostingObj.getHostInfo()
		print "\nPackages Info Status				: ", self.hostingObj.getPackagesInfo()
		print "\nPackages Dependencies Info Status	: ", self.hostingObj.getPackagesDependenciesInfo()

		print "\n\nAdding the resource relevant to the selected <%s> host ...\n" % (self.repoName)

		# Host's basic info details
		hostName, hostInstance = self.AddHostInstances()

		# Host's packages details
		self.addHostPackages(hostName, hostInstance)

		# Host's packages's dependencies details
		self.addHostPackagesDependencies(hostName, hostInstance)

		print "\n\tAdded Triple count: ", self.conn.size(), "\n"

		return "*** <%s> Host Model OKB generation is now complete." % (self.repoName)