class hostDetails:
	""" Host information, Packages (Name and Version), etc. """

	def __init__(self):
		""" Class scoped variables and data """

		self.hostName				= ""
		self.hostOS 				= "" # Host OS<"Dist Name Version Codename">
		self.hostPublicIP			= "" 
		self.hostIPs				= []

		self.packages 				= {} # Package <Name, Version>
		self.packagesDependencies 	= {} # Packages <Package, Package>

	def getHostInfo(self):
		""" Populate the hostName, hhostPublicIP and hostOS """

		import platform, urllib, subprocess
		from subprocess import check_output

		self.hostName		= platform.node()
		
		#self.hostOS 		= " ".join(platform.linux_distribution())
		self.hostOS 		= (check_output(["lsb_release", "-d"])).split("\t")[1].replace("\n", "")

		self.hostPublicIP 	= urllib.urlopen('http://icanhazip.com/').read().strip("\n")
		self.hostIPs 		= (check_output(['hostname', '--all-ip-addresses'])).replace(" \n", "").split(" ")
		
		return "Done."

	def find_files(self, file_name):
		""" Based on: https://stackoverflow.com/questions/1724693/find-a-file-in-python """

		import subprocess

		command = ['locate', file_name]
		output = subprocess.Popen(command, stdout=subprocess.PIPE).communicate()[0]
		search_results = output.split('\n')

		return search_results

	def stack_component_name_version(self, inputFile):
		"""
			Given a README file of a Bitnami Stack deployment (e.g., Wordpress), 
			return all its components pair as a dictionary object :<name, version>
		"""

		component_pair = {}
		lines = []
		with open(inputFile, "r") as fp:
			for line in fp:
				line = str(line).replace("\n", "")
				lines.append(line)
		try:
			stack_components = lines[lines.index('3. COMPONENTS')+4:lines.index('4. REQUIREMENTS')-1]
			for component in stack_components:
				if '-' in list(component):
					component = component.replace("- ", "")
					component = component.split(" ")

					component_formatted = []
					for item in component:
						if item != '':
							component_formatted.append(item)
					
					comp_len = len(component_formatted)
					if comp_len == 2:
						component_name = component_formatted[0].lower()
						if '(' in list(component_name):
							component_name = component_name.split('(')[0]
						component_pair[component_name] = component_formatted[1]
					if comp_len > 2:
						component_version = component_formatted[-1]
						component_name = '-'.join(component_formatted[0:-1])
						component_name = component_name.lower()
						component_pair[component_name] = component_version
		except:
			pass

		return component_pair

	def getPackagesInfo(self):
		""" 
		Targeting Ubuntu Xenial VM/Instance/Container
			:: Reading all installed packages, 
				-> For each package, 
					: Extract its relevant Package and Version, and write all the details to self.packages
			:: Set up the locale first: <export LC_ALL="en_US.UTF-8">
		"""
		import subprocess

		### Bitnami deployment rule
		try:
			target_filename = "../stack/README.txt" # This needs to be generalized later on.
			#target_filename = "README.txt" # stack/README.txt

			component_pair = {}

			# TODO - for debian (ubuntu os ready though.)
			# file_paths = self.find_files(target_filename)
			# for path in file_paths:
			# 	tmp = path.split("/")
			# 	if "stack" in tmp:
			# 		print path
			# 		# Use this path to extract Bitnami Deployment components into pairs.
			# 		component_pair = self.stack_component_name_version(path)
			# 		break
			component_pair = self.stack_component_name_version(target_filename)
			
			for key, value in component_pair.items():
				self.packages[key] = value
		except:
			pass

		### All other install packages via apt
		allPkges = subprocess.check_output(["apt", "list", "--installed"], stderr=subprocess.STDOUT)
		pkgesList = []

		for item in allPkges.split("\n"):
			pkgesList.append(item)

		for pkg in pkgesList[4:]:
			tmp = pkg.split(",")
			tmp = tmp[0].split("/")
			pkgName = tmp[0]
			
			try:
				infoCmd = ["apt", "show", pkgName]
				pkgInfo = subprocess.check_output(infoCmd, stderr=subprocess.STDOUT)

				pkgeName     = ""
				pkgeversion  = ""

				for item in pkgInfo.split("\n"):
					item = (item.replace("\n", "")).split(":")

					if item[0] == "Package":
						tmp = item[1:]
						if len(tmp) == 1:
							pkgeName = tmp[0]
						else:
							tmp = ":".join(tmp)
							pkgeName = tmp

					if item[0] == "Version":
						tmp = item[1:]
						if len(tmp) == 1:
							pkgeversion = tmp[0]
						else:
							tmp = ":".join(tmp)
							pkgeversion = tmp

						break

				### (http://www.sosst.sk/doc/debian-policy/policy.html/ch-controlfields.html#s-f-Version)
				# The format is: [epoch:]upstream_version[-debian_revision]
				version = pkgeversion.strip()
				
				# [epoch:] revomed
				if version[1] == ":":
					version = version.split(":")[1]
				# [-debian_revision] removed
				if '-' in version:
					version = version.split("-")[0]

				# Keeping the [upstream_version] part
				self.packages[pkgeName.strip()] = version 
			except:
				pass

		return "Done."

	def getPackagesDependenciesInfo(self):
		""" 
		Targeting Ubuntu Xenial VM/Instance/Container
			:: Reading all installed packages, 
				-> For each package, 
					: Extract its first order dependecy packages 
					: and write all the details to self.packagesDependencies
			:: Set up the locale first: <export LC_ALL="en_US.UTF-8">
			:: Needs to recall, the use of "|" in dependencies.
		"""

		import subprocess

		allPkges = subprocess.check_output(["apt", "list", "--installed"], stderr=subprocess.STDOUT)
		pkgesList = []

		for item in allPkges.split("\n"):
			pkgesList.append(item)

		for pkg in pkgesList[4:]:
			tmp = pkg.split(",")
			tmp = tmp[0].split("/")
			pkgName = tmp[0]

			try:
				infoCmd = ["apt", "show", pkgName]
				pkgInfo = subprocess.check_output(infoCmd, stderr=subprocess.STDOUT)

				pkgeName      = ""
				outDependencies  = []

				for item in pkgInfo.split("\n"):
					item = (item.replace("\n", "")).split(":")

					if item[0] == "Package":
						tmp = item[1:]
						if len(tmp) == 1:
							pkgeName = tmp[0]
						else:
							tmp = ":".join(tmp)
							pkgeName = tmp

					if item[0] == "Depends":
						tmp = item[1:]
						dependencies = ":".join(tmp)
						dependencies = dependencies.split(", ")
						
						for var in dependencies:
							var = var.replace(" ", "")
							tmp = var.split("(")
							
							if len(tmp) >= 1:
								outDependencies.append(tmp[0])

				finDependencies = ""
				if len(outDependencies) >= 1:
					finDependencies = outDependencies[0] + "->" + "->".join(outDependencies[1:]) 

				self.packagesDependencies[pkgeName.strip()] = finDependencies.strip()
			except:
				pass 

		return "Done."

if __name__ == '__main__':
	
	demo = hostDetails()

	# #1.
	print demo.getHostInfo()
	print "\nhostName: \t", demo.hostName
	print "\nhostOS: \t", demo.hostOS
	print "\nhostPublicIP: \t", demo.hostPublicIP
	print "\nhostIPs: \t", demo.hostIPs
	
	#2.
	print demo.getPackagesInfo()
	print "\nPackages: ", demo.packages
	
	#3.
	print demo.getPackagesDependenciesInfo()
	print "\n", demo.packagesDependencies