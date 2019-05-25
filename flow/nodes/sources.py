from flow.node import Node, Ptype
import os # for listing files in directories
import fnmatch # for filtering filenames
import random # for random numbers


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
		self.elOut = self.addOutput('elements')
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
			return [start + step*i for i in range(n)]
		else:
			return []
	
	def process(self, start, step, stop):
		arr = self.seq(start, stop, step)
		self.arrOut.push(arr)
		self.lenOut.push(len(arr))
		for el in arr:
			self.elOut.push(el)


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


class NoiseSource(Node):
	'''
	Provides random float numbers on its output
	'''
	def __init__(self):
		Node.__init__(self, 'Noise out')
		self.addInput('low', 0.)
		self.addInput('high', 1.)
		self.addInput('gauss', False)
		self.addInput('numElements', 1)
		self.noiseOut = self.addOutput('float', Ptype.FLOAT)
	
	def process(self, low, high, gauss, numElements):
		for _ in range(numElements):
			if gauss:
				mean = (low+high)/2.
				std = (high-mean)/3. # 99% coverage should be enough
				self.noiseOut.push(random.gauss(mean, std))
			else:
				self.noiseOut.push(random.uniform(low, high))


class FileSource(Node):
	'''
	Reads lines from a file specified by a path string 
	and pushes out the line strings
	'''
	def __init__(self):
		Node.__init__(self, 'File source')
		self.addInput('filepath', '/Path/To/File.suffix', ptype=Ptype.FILE)
		self.addInput('aslines', True)
		self.lineOut = self.addOutput('string', Ptype.STR)
	
	def process(self, filepath, aslines):
		with open(filepath) as file:
			if aslines:
				# push out lines
				for line in file:
					self.lineOut.push(line)
			else:
				# push out whole file content
				self.lineOut.push(file.read())


class FileSearchSource(Node):
	'''
	Searches for files with pattern in name in directory
	'''
	def __init__(self):
		Node.__init__(self, 'File search')
		self.addInput('dirpath', '/Path/To/Directory', ptype=Ptype.FILE)
		self.addInput('subdirs', False) # also search in subdirectories
		self.addInput('pattern', '*')
		self.filesOut = self.addOutput('files', Ptype.LIST)
	
	def process(self, dirpath, subdirs, pattern):
		if subdirs:
			# search in subdirectories
			filepaths = []
			for root, _, files in os.walk(dirpath):
				paths = [os.path.relpath(os.path.join(root, filename), dirpath) for filename in fnmatch.filter(files, pattern)]
				filepaths.extend(paths)
			self.filesOut.push(filepaths)
		else:
			# search only in specified directory
			files = fnmatch.filter(os.listdir(dirpath), pattern)
			self.filesOut.push(files)