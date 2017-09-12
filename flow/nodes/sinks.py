from flow.node import Node

class Print(Node):
	'''Formats input data as string'''
	
	def __init__(self):
		super(Print, self).__init__('Print')
		self.addInput('data')
		self.strOut = self.addOutput('formatted', str)
	
	def process(self, data):
		self.strOut.push('{}'.format(data))

class FileSink(Node):
	'''Writes input data as lines to a file 
	specified by a path string input'''
	
	def __init__(self):
		super(FileSink, self).__init__('File sink')
		self.addInput('data')
		self.addInput('filepath', 'C:/Users/Klaus/Documents/ToDoList.txt', dtype=file)
		self.addInput('lines', True) # adding linefeed or not
		# only technical needed to have a result value (the path when finished)
		self.pathOut = self.addOutput('filepath', str)
		
		self.file = None
	
	def process(self, data, filepath, lines):
		if not self.file:
			self.file = open(filepath, 'a')
		# append data to file
		self.file.write('{}{}'.format(data, '\n' if lines else ''))
		self.pathOut.push(filepath)
	
	def finish(self):
		self.file.close()
		self.file = None