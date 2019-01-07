from flow.node import Node, Ptype

class IntegerSource(Node):
	'''
	Provides a integer number on its output
	'''
	def __init__(self):
		Node.__init__(self, 'Int out')
		# Automatically assign same datatype to output as the input
		# by parsing the default value during addInput.
		inp = self.addInput('value', 0)
		self.srcOut = self.addOutput('int', inp.ptype)
	
	def process(self, value):
		self.srcOut.push(int(value))


class FloatSource(Node):
	'''
	Provides a float number on its output
	'''
	def __init__(self):
		Node.__init__(self, 'Float out')
		inp = self.addInput('value', 0.0)
		self.srcOut = self.addOutput('float', inp.ptype)
	
	def process(self, value):
		self.srcOut.push(float(value))


class BooleanSource(Node):
	'''
	Provides a bool value on its output
	'''
	def __init__(self):
		Node.__init__(self, 'Bool out')
		inp = self.addInput('value', True)
		self.srcOut = self.addOutput('bool', inp.ptype)
	
	def process(self, value):
		self.srcOut.push(True if value else False)


class StringSource(Node):
	'''
	Provides a string on its output
	'''
	def __init__(self):
		Node.__init__(self, 'String out')
		inp = self.addInput('value', 'Hello')
		self.srcOut = self.addOutput('string', inp.ptype)
	
	def process(self, value):
		self.srcOut.push(str(value))


class ComplexSource(Node):
	'''
	Provides a complex number on its output
	'''
	def __init__(self):
		Node.__init__(self, 'Complex out')
		self.addInput('re', 0.0)
		self.addInput('im', 0.0)
		self.complexOut = self.addOutput('complex', Ptype.COMPLEX)
	
	def process(self, re, im):
		self.complexOut.push(complex(re, im))


class DictSource(Node):
	'''
	Gets a value specified by key from a dictionary
	'''
	def __init__(self):
		Node.__init__(self, 'Value from dictionary')
		self.addInput('dictionary', {})
		self.addInput('key', 'key')
		self.valOut = self.addOutput('value')
	
	def process(self, dictionary, key):
		if key in dictionary:
			self.valOut.push(dictionary[key])


class RangeSource(Node):
	'''
	Abstract class for range sources
	'''
	def __init__(self, name):
		Node.__init__(self, name)
		self.arrOut = self.addOutput('array', Ptype.LIST)
		self.lenOut = self.addOutput('length', Ptype.INT)
	
	def seq(self, start, stop, step=1):
		# sanity checks
		if stop < start and step > 0:
			return []
		if stop > start and step < 0:
			return []
		# make array
		n = abs(int(round((stop-start)/float(step))))
		if n > 0:
			return [start + step*i for i in range(n+1)]
		else:
			return []
	
	def process(self, start, step, stop):
		arr = self.seq(start, stop, step)
		self.arrOut.push(arr)
		self.lenOut.push(len(arr))


class IntegerRangeSource(RangeSource):
	'''
	Provides an int range array and its length on the outputs
	'''
	def __init__(self):
		RangeSource.__init__(self, 'Int range out')
		self.addInput('start', 1)
		self.addInput('step', 1)
		self.addInput('stop', 10)


class FloatRangeSource(RangeSource):
	'''
	Provides a float range array and its length on the outputs
	'''
	def __init__(self):
		RangeSource.__init__(self, 'Float range out')
		self.addInput('start', 0.)
		self.addInput('step', 0.1)
		self.addInput('stop', 1.)


class FileSource(Node):
	'''
	Reads lines from a file specified by a path string 
	and pushes out the line strings
	'''
	def __init__(self):
		Node.__init__(self, 'File source')
		self.addInput('filepath', '/Path/To/File.suffix', ptype=Ptype.FILE)
		self.lineOut = self.addOutput('line', Ptype.STR)
	
	def process(self, filepath):
		# push out all lines in one iteration
		with open(filepath) as file:
			for line in file:
				self.lineOut.push(line)