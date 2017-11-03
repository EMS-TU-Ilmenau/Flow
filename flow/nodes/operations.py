from flow.node import Node, ptype
import math # for float operations

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

class Pow(Operation):
	def __init__(self):
		super(Pow, self).__init__('Power')
	
	def process(self, a, b):
		self.res.push(a**b)

class Exp(Node):
	'''Exponent of a value'''
	def __init__(self):
		super(Exp, self).__init__('Exponent')
		self.addInput('x', 0.)
		self.resOut = self.addOutput('exp', ptype.FLOAT)
	
	def process(self, x):
		self.resOut.push(math.exp(x))

class Log(Node):
	'''Logarithm of a value'''
	def __init__(self):
		super(Log, self).__init__('Logarithm')
		self.addInput('x', 1.)
		self.addInput('base', 10.)
		self.resOut = self.addOutput('log', ptype.FLOAT)
	
	def process(self, x, base):
		self.resOut.push(math.log(x, base))

class AngleFunc(Node):
	'''Base class for angle functions with radians/degree conversion'''
	def __init__(self, name):
		super(AngleFunc, self).__init__(name)
		self.addInput('deg', False)
		self.addInput('hyperb', False)

class AngleTo(AngleFunc):
	'''Base class for angle functions with angle to function conversion'''
	def __init__(self, name):
		super(AngleTo, self).__init__(name)
		self.addInput('angle', 0.)
		self.resOut = self.addOutput('value', ptype.FLOAT)
	
	def process(self, deg, hyperb, angle):
		if deg:
			angle = math.radians(angle)
		# hyperFunc and angleFunc have to be defined by inheritated class!
		self.resOut.push(self.hyperFunc(angle) if hyperb else self.angleFunc(angle))

class ToAngle(AngleFunc):
	'''Base class for angle functions with function to angle conversion'''
	def __init__(self, name):
		super(ToAngle, self).__init__(name)
		self.addInput('value', 0.)
		self.resOut = self.addOutput('angle', ptype.FLOAT)
	
	def process(self, deg, hyperb, value):
		# hyperFunc and angleFunc have to be defined by inheritated class!
		angle = self.hyperFunc(value) if hyperb else self.angleFunc(value)
		if deg:
			angle = math.degrees(angle)
		self.resOut.push(angle)

class Sinus(AngleTo):
	def __init__(self):
		super(Sinus, self).__init__('Angle to sinus')
		self.angleFunc = math.sin
		self.hyperFunc = math.sinh

class Cosinus(AngleTo):
	def __init__(self):
		super(Cosinus, self).__init__('Angle to cosinus')
		self.angleFunc = math.cos
		self.hyperFunc = math.cosh

class Tangens(AngleTo):
	def __init__(self):
		super(Tangens, self).__init__('Angle to tangens')
		self.angleFunc = math.tan
		self.hyperFunc = math.tanh

class ArcSinus(ToAngle):
	def __init__(self):
		super(ArcSinus, self).__init__('Sinus to angle')
		self.angleFunc = math.asin
		self.hyperFunc = math.asinh

class ArcCosinus(ToAngle):
	def __init__(self):
		super(ArcCosinus, self).__init__('Cosinus to angle')
		self.angleFunc = math.acos
		self.hyperFunc = math.acosh

class ArcTangens(ToAngle):
	def __init__(self):
		super(ArcTangens, self).__init__('Tangens to angle')
		self.angleFunc = math.atan
		self.hyperFunc = math.atanh

class MinMax(Operation)
	def __init__(self):
		super(MinMax, self).__init__('Min Max')
		self.res.name = 'lower'
		self.other = self.addOutput('higher')
	
	def process(self, a, b):
		self.res.push(min(a, b))
		self.other.push(max(a, b))