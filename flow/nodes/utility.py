from flow.node import Node, Ptype
import time # for the pause node
import json # for the dict/str converter nodes

class StrSplit(Node):
	'''Splits a string by delimiter and pushes out the separated string parts'''
	def __init__(self):
		super(StrSplit, self).__init__('String split')
		self.addInput('string', ptype=Ptype.STR)
		self.addInput('delimiter', ',')
		self.strOut = self.addOutput('parts', Ptype.STR)
	
	def process(self, string, delimiter):
		for part in string.split(delimiter):
			self.strOut.push(part)

class StrReplace(Node):
	'''Replaces a pattern in a string'''
	def __init__(self):
		super(StrReplace, self).__init__('String replace')
		self.addInput('string', ptype=Ptype.STR)
		self.addInput('find', ';')
		self.addInput('replace', ',')
		self.strOut = self.addOutput('modified', Ptype.STR)
	
	def process(self, string, find, replace):
		self.strOut.push(string.replace(find, replace))

class StrToDict(Node):
	'''Converts a JSON formatted string to to a dictionary'''
	def __init__(self):
		super(StrToDict, self).__init__('String to dictionary')
		self.addInput('string', ptype=Ptype.STR)
		self.dictOut = self.addOutput('dictionary', Ptype.DICT)
	
	def process(self, string):
		try:
			self.dictOut.push(json.loads(string))
		except:
			raise Error('{} cannot convert {:.50}... to a dictionary'.format(self.name, string))

class DictToStr(Node):
	'''Converts dictionary to a JSON formatted string'''
	def __init__(self):
		super(DictToStr, self).__init__('Dictionary to string')
		self.addInput('dictionary', ptype=Ptype.DICT)
		self.strOut = self.addOutput('string', Ptype.STR)
	
	def process(self, dictionary):
		try:
			self.strOut.push(json.dumps(dictionary, indent=4))
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
		self.arrOut = self.addOutput('array', Ptype.LIST)
	
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
		self.addInput('array', ptype=Ptype.LIST)
		self.elOut = self.addOutput('elements')
	
	def process(self, array):
		for element in array:
			self.elOut.push(element)

class IndexToValue(Node):
	'''Get a value based on index from an array'''
	def __init__(self):
		super(IndexToValue, self).__init__('Array value')
		self.addInput('array', ptype=Ptype.LIST)
		self.addInput('index', -1)
		self.valOut = self.addOutput('value')
	
	def process(self, array, index):
		try:
			self.valOut.push(array[index])
		except IndexError:
			pass

class ValueToIndex(Node):
	'''Get an index based on value from an array'''
	def __init__(self):
		super(ValueToIndex, self).__init__('Array index')
		self.addInput('array', ptype=Ptype.LIST)
		self.addInput('value')
		self.indOut = self.addOutput('index', Ptype.INT)
	
	def process(self, array, value):
		if value in array:
			self.indOut.push(array.index(value))

class ArrayMax(Node):
	'''Get the maximum value and corresponding index from an array'''
	def __init__(self):
		super(ArrayMax, self).__init__('Maximum in array')
		self.addInput('array', ptype=Ptype.LIST)
		self.valOut = self.addOutput('value')
		self.indOut = self.addOutput('index', Ptype.INT)
	
	def process(self, array):
		val = max(array)
		self.valOut.push(val)
		self.indOut.push(array.index(val))

class ArrayMin(Node):
	'''Get the minimum value and corresponding index from an array'''
	def __init__(self):
		super(ArrayMin, self).__init__('Minimum in array')
		self.addInput('array', ptype=Ptype.LIST)
		self.valOut = self.addOutput('value')
		self.indOut = self.addOutput('index', Ptype.INT)
	
	def process(self, array):
		val = min(array)
		self.valOut.push(val)
		self.indOut.push(array.index(val))

class ArrayLength(Node):
	'''Get the length an array'''
	def __init__(self):
		super(ArrayLength, self).__init__('Array length')
		self.addInput('array', ptype=Ptype.LIST)
		self.lenOut = self.addOutput('length', Ptype.INT)
	
	def process(self, array):
		self.lenOut.push(len(array))

class ArrayAppend(Node):
	'''Adds an element to an array'''
	def __init__(self):
		Node.__init__(self, 'Append to Array')
		self.arrIn = self.addInput('array', [])
		self.addInput('data')
		self.arrOut = self.addOutput('array', Ptype.LIST)
	
	def prepare(self):
		self.arrIn.default = [] # to clean reference
	
	def process(self, array, data):
		array.append(data)
		self.arrOut.push(array)

class ArrayRemove(Node):
	'''Removes an element of an array'''
	def __init__(self):
		Node.__init__(self, 'Remove from Array')
		self.addInput('array', ptype=Ptype.LIST)
		self.addInput('data')
		self.arrOut = self.addOutput('array', Ptype.LIST)
	
	def process(self, array, data):
		array.remove(data)
		self.arrOut.push(array)

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

class Trigger(Node):
	'''Gates data behind any data at trigger port'''
	def __init__(self):
		super(Trigger, self).__init__('Trigger')
		self.dataIn = self.addInput('data')
		self.addInput('trigger')
		self.addInput('reuseOldData', False)
		self.repOut = self.addOutput('data')
	
	def process(self, data, trigger, reuseOldData):
		self.repOut.push(data)
		if reuseOldData and not self.dataIn.buffer:
			# append old data to buffer again until fresh data is coming
			self.dataIn.buffer.append(data)

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