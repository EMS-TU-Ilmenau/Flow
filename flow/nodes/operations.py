from flow.node import Node

class Operation(Node):
	'''Base class for all operations with two inputs and one output'''
	
	def __init__(self, name):
		super(Operation, self).__init__(name)
		# build inputs and outputs
		self.addInput('a')
		self.addInput('b')
		self.res = self.addOutput('c')

class Add(Operation):
	def __init__(self):
		super(Add, self).__init__('Addition')
	
	def process(self, a, b):
		self.res.push(a+b)

class Sub(Operation):
	def __init__(self):
		super(Sub, self).__init__('Subtraction')
	
	def process(self, a, b):
		self.res.push(a-b)

class Mul(Operation):
	def __init__(self):
		super(Mul, self).__init__('Multiplication')
	
	def process(self, a, b):
		self.res.push(a*b)

class Div(Operation):
	def __init__(self):
		super(Div, self).__init__('Division')
	
	def process(self, a, b):
		self.res.push(a/b)

class CustomOp(Operation):
	'''A custom operation with the inputs "a" and "b" can be entered in the string input.
	Also python math operations are allowed with leading "math."
	'''
	def __init__(self):
		super(CustomOp, self).__init__('Custom operation')
		# build additional input
		self.addInput('operation', '(a*b)/(a+b)') # default/example custom operation
		# import math module for more powerful operations
		import math
	
	def process(self, a, b, operation):
		exec('result = '+operation)
		self.res.push(result)