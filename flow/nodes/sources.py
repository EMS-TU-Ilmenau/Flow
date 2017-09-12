from flow.node import Node

class IntegerSource(Node):
	'''Provides a integer number on its output'''
	
	def __init__(self):
		super(IntegerSource, self).__init__('Int out')
		# Automatically assign same datatype to output as the input 
		# by parsing the default value during addInput.
		input = self.addInput('value', 0)
		self.srcOut = self.addOutput('int', input.dtype)
	
	def process(self, value):
		self.srcOut.push(value)

class FloatSource(Node):
	'''Provides a float number on its output'''
	
	def __init__(self):
		super(FloatSource, self).__init__('Float out')
		input = self.addInput('value', 0.0)
		self.srcOut = self.addOutput('float', input.dtype)
	
	def process(self, value):
		self.srcOut.push(value)

class BooleanSource(Node):
	'''Provides a bool value on its output'''
	
	def __init__(self):
		super(BooleanSource, self).__init__('Bool out')
		input = self.addInput('value', True)
		self.srcOut = self.addOutput('bool', input.dtype)
	
	def process(self, value):
		self.srcOut.push(True if value else False)

class StringSource(Node):
	'''Provides a string on its output'''
	
	def __init__(self):
		super(StringSource, self).__init__('String out')
		input = self.addInput('value', 'Hello')
		self.srcOut = self.addOutput('bool', input.dtype)
	
	def process(self, value):
		self.srcOut.push(value)

class RangeSource(Node):
	'''Provides a range array and its length on the outputs'''
	
	def __init__(self):
		super(RangeSource, self).__init__('Range out')
		self.addInput('start', 1)
		self.addInput('step', 1)
		self.addInput('stop', 10)
		self.arrOut = self.addOutput('array', list)
		self.lenOut = self.addOutput('length', int)
	
	def process(self, start, step, stop):
		arr = list(range(start, stop+1, step))
		self.arrOut.push(arr)
		self.lenOut.push(len(arr))

class FileSource(Node):
	'''Reads lines from a file specified by a path string 
	and pushes out the line strings'''
	
	def __init__(self):
		super(FileSource, self).__init__('File source')
		self.addInput('filepath', 'C:/Users/Klaus/Documents/ToDoList.txt', dtype=file)
		self.lineOut = self.addOutput('line', str)
	
	def process(self, filepath):
		# push out all lines in one iteration
		with open(filepath) as file:
			for line in file:
				self.lineOut.push(line)