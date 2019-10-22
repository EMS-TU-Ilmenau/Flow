from flow import Node, Ptype, Graph # for building nodes and graphes
import random # for generating random values

# create some node classes
class NoiseSource(Node):
	'''
	Pushes out random float values between 0...amplitude
	'''
	def __init__(self):
		Node.__init__(self, 'Noise')
		# add inputs
		self.addInput('amplitude', 1.) # amplitude
		self.addInput('length', 100) # list length
		# add output
		self.rndOut = self.addOutput('rnd', Ptype.LIST) # list with random values
	
	def process(self, amplitude, length):
		# process input data values
		rndVals = [amplitude*random.random() for _ in range(length)] # generate random values
		self.rndOut.push(rndVals) # output list with random values


class Mean(Node):
	'''
	Averages values in a list
	'''
	def __init__(self):
		Node.__init__(self, 'Mean')
		self.addInput('array', ptype=Ptype.LIST) # list (with float or int values)
		self.avrOut = self.addOutput('avr') # average value
	
	def process(self, array):
		self.avrOut.push(sum(array)/float(len(array)))


if __name__ == '__main__':
	# create an example graph
	graph = Graph() # empty graph

	# create noise node
	noise = NoiseSource()
	noise.input['amplitude'].default = 5. # change default amplitude
	graph.addNode(noise) # add to graph

	# create average node
	mean = graph.addNode(Mean())
	'''
	# also possible:
	mean = Mean()
	graph.addNode(mean)
	'''
	mean.input['array'].connect(noise.output['rnd']) # connect to noise output
	'''
	# also possible:
	noise.output['rnd'].connect(mean.input['array'])
	'''
	
	# create max node from package nodes
	listMax = graph.addNode(graph.nodeFromDatabase('flow.nodes.utility.ArrayMax'))
	listMax.input['array'].connect(noise.output['rnd']) # connect to noise output

	'''
	# in case you want to load a node from an external package:
	graph.scopeNodePkg("path/to/myNodePkg")
	graph.addNode(graph.nodeFromDatabase('myNodePkg.somemodule.NodeClassName'))
	'''


	# show graph overview
	print('Graph:')
	print(graph)

	# process graph
	print('\nGraph results:')
	results, _, _ = graph.process()
	for res in results:
		print('{}.{}: {}'.format(res['node'], res['output'], res['result']))