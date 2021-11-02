""" 
Bootstrap the process of discovering this host:
	- Packages & their dependencies and 
	- Host information

	:: Then send this data encoded into a defined ontology model to 
	a shared remote AllegroGraph repository. 
"""

import sys, shlex
from subprocess import call

from legos.input_type import Inputs
from legos.agHostModel import HostMets

if __name__ == '__main__':

	demo = Inputs()
	if len(sys.argv) != 6:
	
		if len(sys.argv) == 2 and (sys.argv[1]).lower() == "help":
			call(shlex.split("less documentation/help_page"))
	
		else:
			# Plain text auth. not the best, but for now it is okay for dev purpose.
			print "\n::Usage \n\tpython manager.py --AGUsername --AGPassword --AGHostIP --AGPort --repositoryName \n"
			print "::Or \n\tpython manager.py help\n\t"
	
	else:
		demo.username = sys.argv[1]
		demo.password = sys.argv[2]
		demo.agHostIp = sys.argv[3]
		demo.agPort   = int(sys.argv[4])
		demo.repoName = sys.argv[5]

		ret = demo.createRepo()
		if ret == 0:
			print "\n**********************************"
			print "Starting a LEGOS building session."
			print "**********************************\n"

			try:
				raw_input("CTRL^C to abort, or ENTER to continue\n")
				
				# Our legos/agHostModel module instance
				# TO-DO: platform detection, if [linux|macos|windows], launch appropriate bootstrap scripts
				macchiato = HostMets(demo)
				
				# Generate our host model okb
				print macchiato.hostModelMethod()

				# Close the connection session.
				print demo.recycleConns()
				print "\n********************************"
				print "Ending a LEGOS building session."
				print "********************************\n"

			except:
				print demo.recycleConns()
				print "\n********************************"
				print "Ending a LEGOS building session."
				print "********************************\n"

		else:
			print("\nSession is terminated.\n")