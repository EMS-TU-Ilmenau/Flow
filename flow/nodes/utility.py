from flow.node import Node, ptype
import time # for the pause node
import json # for the dict/str converter nodes

class StrToDict(Node):
	'''Converts a JSON formatted string to to a dictionary'''
	def __init__(self):
		super(StrToDict, self).__init__('String to dictionary')
		self.addInput('string', type=ptype.STR)
		self.dictOut = self.addOutput('dictionary', ptype.DICT)
	
	def process(self, string):
		try:
			self.dictOut.push(json.loads(string))
		except:
			raise Error('{} cannot convert {:.50}... to a dictionary'.format(self.name, string))

class DictToStr(Node):
	'''Converts dictionary to a JSON formatted string'''
	def __init__(self):
		super(DictToStr, self).__init__('Dictionary to string')
		self.addInput('dictionary', type=ptype.DICT)
		self.strOut = self.addOutput('string', ptype.STR)
	
	def process(self, dictionary):
		try:
			self.strOut.push(json.dumps(dictionary))
		except:
			raise Error('{} cannot convert {:.50}... to a string'.format(self.name, dictionary))

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

class IndexToValue(Node):
	'''Get a value based on index from a list'''
	def __init__(self):
		super(IndexToValue, self).__init__('List value')
		self.addInput('array', type=ptype.LIST)
		self.addInput('index', -1)
		self.valOut = self.addOutput('value')
	
	def process(self, array, index):
		self.valOut.push(array[index])

class ValueToIndex(Node):
	'''Get an index based on value from a list'''
	def __init__(self):
		super(ValueToIndex, self).__init__('List index')
		self.addInput('array', type=ptype.LIST)
		self.addInput('value')
		self.indOut = self.addOutput('index', ptype.INT)
	
	def process(self, array, value):
		self.indOut.push(array.index(value))

class ListMax(Node):
	'''Get the maximum value and corresponding index from a list'''
	def __init__(self):
		super(ListMax, self).__init__('Maximum in list')
		self.addInput('array', type=ptype.LIST)
		self.valOut = self.addOutput('value')
		self.indOut = self.addOutput('index', ptype.INT)
	
	def process(self, array):
		val = max(array)
		self.valOut.push(val)
		self.indOut.push(array.index(val))

class ListMin(Node):
	'''Get the minimum value and corresponding index from a list'''
	def __init__(self):
		super(ListMin, self).__init__('Minimum in list')
		self.addInput('array', type=ptype.LIST)
		self.valOut = self.addOutput('value')
		self.indOut = self.addOutput('index', ptype.INT)
	
	def process(self, array):
		val = min(array)
		self.valOut.push(val)
		self.indOut.push(array.index(val))

class ListLength(Node):
	'''Get the length a list'''
	def __init__(self):
		super(ListLength, self).__init__('List length')
		self.addInput('array', type=ptype.LIST)
		self.lenOut = self.addOutput('length', ptype.INT)
	
	def process(self, array):
		self.lenOut.push(len(array))

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