import json # for parsing JSON formatted graph files
from timeit import default_timer # for measuring processing time
import logging # for debugging the dataflow
import importlib, inspect # for instantiating nodes from class path
import sys # for adding package to path
import os.path as putil # for path utility

log = logging.getLogger(__name__)

def shortString(data, maxLen=40):
	'''
	:param data: any data which can be converted to a string
	:param maxLen: maximum string length to output
	:returns: data as shortened string, showing only beginning and end
	'''
	dataStr = str(data)
	if dataStr == 'None':
		return ''
	if len(dataStr) > maxLen:
		return '{}...{}'.format(
			dataStr[:int(maxLen/2)], dataStr[-int(maxLen/2):])
	else:
		return dataStr

def uniqueName(names, name):
	'''
	:param names: list of string names
	:param name: name which needs to be different from the names in the list
	:returns: (modified) unique name
	'''
	# check if name is already unique
	if not any(n == name for n in names):
		return name
	else:
		if '.' in name:
			# we already tried to make unique
			pre, suf = name.split('.')
			# increase suffix and try again
			newName = '{}.{}'.format(pre, int(suf)+1)
		else:
			# append number as suffix
			newName = '{}.{}'.format(name, 1)
		return uniqueName(names, newName)


class Graph(object):
	'''
	Stores, manages and executes nodes.
	'''
	
	def __init__(self, path=None):
		'''
		:param path: when set to a json formatted graph-file path, 
			builds the graph from the file
		'''
		self.nodeDict = {} # create dictionary for the nodes
		self.nodesRunOrder = None
		self.loopInputs = None
		self.prepared = False
		# optionally build graph from file
		if path:
			self.fromFile(path)
	
	def __del__(self):
		self.clear() # delete all nodes before deleting the graph
	
	def __str__(self):
		'''
		Shows the current nodes and their connections as string
		'''
		graphStr = ''
		for node in self.nodes:
			# node name
			graphStr += '\n{}'.format(node.name)
			
			for inp in node.inputs:
				# format inputs name and default
				defaultStr = shortString(inp.default)
				graphStr += '\n> {}{}'.format(inp.name, 
					': {}'.format(defaultStr) if defaultStr else '')
				if inp.isConnected():
					# format input connection
					graphStr += ' o-o {}.{}'.format(
						inp.connOutput.node.name, inp.connOutput.name)
			
			for out in node.outputs:
				# format outputs name and result
				resultStr = shortString(out.result)
				graphStr += '\n< {}{}'.format(out.name, 
					': {}'.format(resultStr) if resultStr else '')
				if out.isConnected():
					# format output connections
					graphStr += ' o-o '
					graphStr += ', '.join('{}.{}'.format(
						inp.node.name, inp.name) for inp in out.connInputs)
			
			graphStr += '\n'
		
		return graphStr
	
	@property
	def nodes(self):
		return self.nodeDict.values()
	
	def addNode(self, node):
		'''
		Adds a node object to the graph

		:param node: node object
		'''
		# give unique name
		name = uniqueName(self.nodeDict.keys(), node.name)
		node.name = name
		self.nodeDict[name] = node
		return node
	
	def removeNode(self, name):
		'''
		Disconnects and removes a node object from the graph

		:param name: nodes graph name to remove
		'''
		self.nodeDict[name].disconnect()
		self.nodeDict.pop(name)
	
	def clear(self):
		'''
		Deletes all nodes in the graph
		'''
		self.nodeDict.clear()
		# clean up properties from prepare
		self.nodesRunOrder = None
		self.loopInputs = None
	
	def scopeNodePkg(self, extNodePkgs):
		'''
		Imports external node package(s). 
		Note: this does NOT add the nodes to the graph. In that case, use:
			graph.scopeNodePkg("path/to/myPackage")
			node = graph.nodeFromDatabase("myPackage.module.NodeClassName")
			graph.addNode(node)
		
		:param extNodePkgs: string or list/tuple of strings with directory path(s)
		'''
		def importPkg(pkgPath):
			# imports a package by directory path
			sys.path.append(putil.dirname(pkgPath))
			pkg = importlib.import_module(putil.basename(pkgPath))
			return pkg
		
		if isinstance(extNodePkgs, (tuple, list)):
			# import multiple node packages
			for path in extNodePkgs:
				importPkg(path)
		else:
			return importPkg(extNodePkgs) # import single package
	
	def nodeFromDatabase(self, classPath, name=''):
		'''
		Instantiates a node from the database

		:param classPath: string like "package.module.NodeClassName"
		:param name: optional name for re-naming the node
		:returns: node instance
		'''
		# get module/class seperator
		sep = classPath.rfind('.')
		modName = classPath[:sep] # module name
		clsName = classPath[sep+1:] # class name
		# instantiate node
		mod = importlib.import_module(modName)
		modMems = inspect.getmembers(mod)
		for mem in modMems:
			if mem[0] == clsName:
				node = mem[1]()
				if name: # optional rename node
					node.name = name
				return node
		
		raise ImportError('Node {} cannot be found in {}'.format(clsName, modName))
	
	def fromDict(self, graphDict):
		'''
		Builds nodes and connections from json formatted string
		
		:param graphDict: dictionary. Example:
			[optional]{"packages": ["path/to/package"]}, 
			{"nodes": {
				"nodeA": {
					"class": "package.module.NodeClassName", 
					"inputs": {
						"inputA": {
							"connection": [may be null]{"node": "nodeB", "output": "outputA"}, 
							"default": [may be null]42
						}, 
						"inputB": {...}
					}
				}, 
				"nodeB": {...}
			}}
		'''
		self.clear() # clean up old graph

		# load optional external node packages
		extPkgs = graphDict.get('packages')
		if extPkgs:
			self.scopeNodePkg(extPkgs)
		
		# instantiate nodes from class
		for nodeName, nodeEntry in graphDict['nodes'].items():
			classPath = nodeEntry['class']
			self.addNode(self.nodeFromDatabase(classPath, nodeName))
		
		# go through a second time to update default and connect
		for nodeName, nodeEntry in graphDict['nodes'].items():
			node = self.nodeDict[nodeName] # get the already created node
			for inp in node.inputs:
				inputEntry = nodeEntry['inputs'][inp.name]
				# set default
				inp.default = inputEntry.get('default')
				# set connection
				conn = inputEntry.get('connection')
				if conn:
					connNode = self.nodeDict[conn['node']]
					connOutput = connNode.output[conn['output']]
					inp.connect(connOutput)
	
	def fromFile(self, path):
		'''
		Builds nodes and connections from json formatted file

		:param path: json formatted graph-file path
		'''
		file = open(path)
		jsonStr = file.read() # read whole file
		graphDict = json.loads(jsonStr) # convert string to dict
		self.fromDict(graphDict)
		file.close()
		log.info('Built graph from file')
	
	def getSources(self):
		'''
		:returns: list with the source nodes
		'''
		return list(filter(lambda node: all(not inp.isConnected() 
			for inp in node.inputs), self.nodes))
		
	def getSinks(self):
		'''
		:returns: list with the sink nodes
		'''
		return list(filter(lambda node: all(not out.isConnected() 
			for out in node.outputs), self.nodes))
	
	def getRunOrder(self):
		'''
		:returns: list of nodes in a layer-wise execution order
		'''		
		# get source nodes first
		sourceNodes = self.getSources()
		if not sourceNodes:
			# user has build a weird loop, try to solve
			log.warning('No source node found for run order')
			sinkNodes = self.getSinks()
			iNode = 0
			while True:
				startNode = self.nodes[iNode]
				iNode += 1
				if startNode not in sinkNodes:
					sourceNodes = [startNode]
					break
				if iNode > len(self.nodes):
					log.error('Cannot solve run order. Using a suboptimal order.')
					return self.nodes
		
		orderedNodes = sourceNodes
		
		# now go down the hierachy layer-wise until all nodes are in the list once
		curLayer = sourceNodes
		while len(orderedNodes) < len(self.nodes):
			nextLayer = []
			for node in curLayer:
				# in each layer, get the next connected nodes
				for out in node.outputs:
					for connInput in out.connInputs:
						connNode = connInput.node
						# if the node was unknown yet, append it to the order list
						# also append it to the next layer
						if connNode not in orderedNodes:
							orderedNodes.append(connNode)
							nextLayer.append(connNode)
			# switch to next layer for next iteration
			curLayer = nextLayer
		
		return orderedNodes
	
	def getInputLoop(self, startInput, curInput=None, loopInputs=[]):
		'''
		Checks recursively if an input is connected in 
		a loop with itself somehow in the graph
		
		:param startInput: the input to be checked for being in a loop
		:returns: list of all inputs in the loop the startInput is in, 
			or empty list if not in loop
		'''
		if not curInput:
			# init
			curInput = startInput
			loopInputs = []
		loopInputs.append(curInput) # build the connection path
		if curInput.isConnected():
			for connInput in curInput.connOutput.node.inputs:
				if connInput.node == startInput.node:
					# found a loop
					return loopInputs
				else:
					return self.getInputLoop(startInput, connInput, loopInputs)
		else:
			return None
	
	def getLoops(self):
		'''
		Checks for all loops in the graph.
		Loops basically work, but there needs to be at least 
		1 input with a default value in the loop
		
		:returns: list of loops (a loop is a list of inputs)
		'''
		loops = []
		for nodeName, node in self.nodeDict.items():
			for inp in node.inputs:
				if inp not in loops: # don't search within found loop again
					loop = self.getInputLoop(inp)
					if loop:
						# input is part of a loop
						loops.extend(loop)
						hasDefault = False
						for loopIn in loop:
							if loopIn.default is not None:
								hasDefault = True
								loopIn.looped = True
								break
						if not hasDefault:
							# loops can only work when a default value was given
							raise ValueError('Loop detected, but no default value was assigned e.g. at {} of {}'.format(
								inp.name, nodeName))
		return loops
	
	def prepare(self):
		'''
		Prepares the graph before process.
		This will get the optimal run order of node execution, 
		check for loops in the graph and init the source buffers
		'''		
		# getting run order
		self.nodesRunOrder = self.getRunOrder()		
		log.info('Run order:')
		for node in self.nodesRunOrder:
			log.info('\t'+node.name)
			# reset and prepare node in case it wants to prepare something
			node.reset()
		
		# getting loops
		self.loopInputs = self.getLoops()
		if self.loopInputs:
			logging.warning('Loop detected. The graph may run forever')
		
		self.prepared = True
	
	def process(self, abort=None):
		'''
		Runs the "collect" method in each node in the run order 
		until an abort condition is met

		:param abort: object with an "is_set()" method, 
			which must return True or False
		:returns: result dictionary, number of iterations, iteration time
		'''
		log.debug(str(self))
		if not self.prepared:
			self.prepare() # prepare graph
		
		log.info('Graph processing...')
		startTime = default_timer()
		iterTime = 0.
		iterCount = 0
		while(True):
			log.info('======== Iteration {} ========\n'.format(iterCount))
			# collect and process data in each node
			for node in self.nodesRunOrder:
				node.collect()
			
			# abort conditions
			if self.nothingToDo:
				break
			
			if abort:
				if abort.is_set():
					break
			
			# some metrics for performance analysis
			iterTime = default_timer()-startTime
			iterCount += 1
		
		# processing finished
		log.info('Finished. Took {:.3f} ms and {} iterations'.format(iterTime*1e3, iterCount))
		log.debug(str(self))
		self.prepared = False
		# notify the node in case it wants to clean up stuff
		for node in self.nodes:
			node.finish()
		# deliver results and performance metrics
		results = self.getResults()
		return results, iterCount, iterTime
	
	@property
	def nothingToDo(self):
		'''
		:returns: True when there is nothing to process, or False when not
		'''
		# check if all nodes cannot process
		return all(not node.busy for node in self.nodes)
	
	def getResults(self):
		'''
		:returns: list of dictionaries with the sink nodes 
			result values and corresponding node/output names.
		'''
		results = []
		for sink in self.getSinks():
			for out in sink.outputs:
				results.append({'result': out.result, 'node': sink.name, 'output': out.name})
		return results