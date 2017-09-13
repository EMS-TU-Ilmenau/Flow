from flow.node import Node, ptype
import time

class PackArray(Node):
	'''Fetches data and releases them as an array.
	The array will be pushed out when reached length, or, 
	if length < 1, when no elements are incoming anymore.
	'''
	
	def __init__(self):
		super(PackArray, self).__init__('Pack array')
		# build inputs and outputs
		self.dataIn = self.addInput('elements')
		self.addInput('length', 0)
		self.arrOut = self.addOutput('array', ptype.LIST)
	
	def prepare(self):
		# for collecting the elements
		self.dataCollector = []
	
	def process(self, elements, length):
		self.dataCollector.append(elements) # collect elements
		if length > 0:
			# release buffered elements by length
			if len(self.dataCollector) >= length:
				self.arrOut.push(self.dataCollector)
				self.dataCollector = []
		else:
			# check if buffer is empty
			if not self.dataIn.buffer:
				self.arrOut.push(self.dataCollector)

class UnpackArray(Node):
	'''Reads all elements from an array and pushes them out. 
	It basically just unpacks the array'''
	
	def __init__(self):
		super(UnpackArray, self).__init__('Unpack array')
		self.addInput('array', type=ptype.LIST)
		self.elOut = self.addOutput('elements')
	
	def process(self, array):
		for element in array:
			self.elOut.push(element)

class Replicate(Node):
	'''Replicate incoming data n times'''
	
	def __init__(self):
		super(Replicate, self).__init__('Replicate')
		# build inputs and outputs
		self.addInput('data')
		self.addInput('n', 1) # 1 means, the data goes out 1:1
		self.repOut = self.addOutput('replicates')
	
	def process(self, data, n):
		for _ in range(n):
			self.repOut.push(data)

class Pause(Node):
	'''Sleeps blocking for specified seconds'''
	
	def __init__(self):
		super(Pause, self).__init__('Pause')
		self.addInput('data')
		self.addInput('sleep', 1.)
		self.dataOut = self.addOutput('data')
	
	def process(self, data, sleep):
		time.sleep(sleep)
		self.dataOut.push(data)