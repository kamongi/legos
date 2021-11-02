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

class Inputs(object):
	""" This class service our legos tool cmd line inputs. """

	def __init__(self):
		""" Set important default parameters to use throughout this project. """

		self.username = ""
		self.password = ""
		self.agHostIp = ""
		self.agPort   = 10035 # Default
		self.repoName = ""
		self.conn 	  = None

	def createRepo(self):
		""" 
			Repository.ACCESS opens an existing repository, or 
			creates a new one if the repository is not found.
		"""
		print "\n-------\nPrelude\n-------\n"

		try:
			print "Defining connnection to AllegroGraph server -- host:'%s' port:%s" % (self.agHostIp, self.agPort)

			server = AllegroGraphServer(self.agHostIp, self.agPort, self.username, self.password)
			catalog = server.openCatalog() 
			myRepository = catalog.getRepository(self.repoName, Repository.ACCESS)
			myRepository.initialize()
			connection = myRepository.getConnection()

			print "Repository <%s> is up!  It contains <%i> statements.\n" % (myRepository.getDatabaseName(), connection.size())
			self.conn = connection

			return 0 # All is well.

		except:
			print "\n***Oops ... :(\n"

			return -1 # Oops

	def recycleConns(self):
		""" Close any open AllegroGraph connection """

		self.conn.close()
		connRepository = self.conn.repository
		connRepository.shutDown()

		return "\nRecycling is done.\n"