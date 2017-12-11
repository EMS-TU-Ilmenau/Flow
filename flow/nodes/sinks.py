from flow.node import Node, Ptype

class Print(Node):
	'''Formats input data as string'''
	def __init__(self):
		super(Print, self).__init__('Print')
		self.addInput('data')
		self.strOut = self.addOutput('formatted', Ptype.STR)
	
	def process(self, data):
		self.strOut.push('{}'.format(data))

class DictSink(Node):
	'''Adds / replaces a key:value pair to a dictionary'''
	def __init__(self):
		super(DictSink, self).__init__('Dictionary')
		self.dictIn = self.addInput('dictionary', {})
		self.addInput('key', 'key')
		self.addInput('value')
		self.dictOut = self.addOutput('dictionary', Ptype.DICT)
	
	def prepare(self):
		self.dictIn.default = {} # to clean reference
		
	def process(self, dictionary, key, value):
		dictionary[key] = value
		self.dictOut.push(dictionary)

class FileSink(Node):
	'''Writes input data as lines to a file 
	specified by a path string input'''
	def __init__(self):
		super(FileSink, self).__init__('File sink')
		self.addInput('string', ptype=Ptype.STR)
		self.addInput('filepath', '/Path/To/File.suffix', ptype=Ptype.FILE)
		self.addInput('lines', False) # adding linefeed or not
		# only technical needed to have a result value (the path when finished)
		self.pathOut = self.addOutput('filepath', Ptype.STR)
		# for faster processing, we let the file object open until the graph finished.
		# alternatively, open and close it in the process method, using "with"
		self.file = None
	
	def process(self, string, filepath, lines):
		if not self.file:
			self.file = open(filepath, 'a' if lines else 'w')
		# append data to file
		self.file.write(string+'\n' if lines else string)
		self.pathOut.push(filepath)
	
	def finish(self):
		if self.file:
			# close the file when graph finished
			self.file.close()
			self.file = None