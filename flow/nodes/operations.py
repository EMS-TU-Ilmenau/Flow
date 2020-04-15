from flow.node import Node, Ptype
import math # for float operations

class Operation(Node):
	'''
	Base class for basic operations with two inputs
	'''
	def __init__(self, name):
		Node.__init__(self, name)
		# build inputs and outputs
		self.addInput('a', 1.)
		self.addInput('b', 2.)
		self.resOut = self.addOutput('c')


class Add(Operation):
	def __init__(self):
		Operation.__init__(self, 'Addition')
	
	def process(self, a, b):
		self.resOut.push(a+b)


class Sub(Operation):
	def __init__(self):
		Operation.__init__(self, 'Subtraction')
	
	def process(self, a, b):
		self.resOut.push(a-b)


class Mul(Operation):
	def __init__(self):
		Operation.__init__(self, 'Multiplication')
	
	def process(self, a, b):
		self.resOut.push(a*b)


class Div(Operation):
	def __init__(self):
		Operation.__init__(self, 'Division')
	
	def process(self, a, b):
		self.resOut.push(a/b)


class Pow(Operation):
	def __init__(self):
		Operation.__init__(self, 'Power')
	
	def process(self, a, b):
		self.resOut.push(a**b)


class MinMax(Operation):
	def __init__(self):
		Operation.__init__(self, 'Min Max')
		self.resOut.name = 'lower'
		self.other = self.addOutput('higher')
	
	def process(self, a, b):
		self.resOut.push(min(a, b))
		self.other.push(max(a, b))


class Exp(Node):
	'''
	Exponent of a value
	'''
	def __init__(self):
		Node.__init__(self, 'Exponent')
		self.addInput('x', 0.)
		self.resOut = self.addOutput('exp', Ptype.FLOAT)
	
	def process(self, x):
		self.resOut.push(math.exp(x))


class Log(Node):
	'''
	Logarithm of a value
	'''
	def __init__(self):
		Node.__init__(self, 'Logarithm')
		self.addInput('x', 1.)
		self.addInput('base', 10.)
		self.resOut = self.addOutput('log', Ptype.FLOAT)
	
	def process(self, x, base):
		self.resOut.push(math.log(x, base))


class AngleFunc(Node):
	'''
	Base class for angle functions with radians/degree conversion
	'''
	def __init__(self, name):
		Node.__init__(self, name)
		self.addInput('deg', False)
		self.addInput('hyperb', False)
	
	def hyperFunc(self, *args):
		raise NotImplementedError('hyperFunc not implemented')
	
	def angleFunc(self, *args):
		raise NotImplementedError('angleFunc not implemented')


class AngleTo(AngleFunc):
	'''
	Base class for angle functions with angle to function conversion
	'''
	def __init__(self, name):
		AngleFunc.__init__(self, name)
		self.addInput('angle', 0.)
		self.resOut = self.addOutput('value', Ptype.FLOAT)
	
	def process(self, deg, hyperb, angle):
		if deg:
			angle = math.radians(angle)
		# hyperFunc and angleFunc have to be defined by inheritated class!
		self.resOut.push(self.hyperFunc(angle) if hyperb else self.angleFunc(angle))


class ToAngle(AngleFunc):
	'''
	Base class for angle functions with function to angle conversion
	'''
	def __init__(self, name):
		AngleFunc.__init__(self, name)
		self.addInput('value', 0.)
		self.resOut = self.addOutput('angle', Ptype.FLOAT)
	
	def process(self, deg, hyperb, value):
		# hyperFunc and angleFunc have to be defined by inheritated class!
		angle = self.hyperFunc(value) if hyperb else self.angleFunc(value)
		if deg:
			angle = math.degrees(angle)
		self.resOut.push(angle)


class Sinus(AngleTo):
	def __init__(self):
		AngleTo.__init__(self, 'Angle to sinus')
		self.angleFunc = math.sin
		self.hyperFunc = math.sinh


class Cosinus(AngleTo):
	def __init__(self):
		AngleTo.__init__(self, 'Angle to cosinus')
		self.angleFunc = math.cos
		self.hyperFunc = math.cosh


class Tangens(AngleTo):
	def __init__(self):
		AngleTo.__init__(self, 'Angle to tangens')
		self.angleFunc = math.tan
		self.hyperFunc = math.tanh


class ArcSinus(ToAngle):
	def __init__(self):
		ToAngle.__init__(self, 'Sinus to angle')
		self.angleFunc = math.asin
		self.hyperFunc = math.asinh


class ArcCosinus(ToAngle):
	def __init__(self):
		ToAngle.__init__(self, 'Cosinus to angle')
		self.angleFunc = math.acos
		self.hyperFunc = math.acosh


class ArcTangens(ToAngle):
	def __init__(self):
		ToAngle.__init__(self, 'Tangens to angle')
		self.angleFunc = math.atan
		self.hyperFunc = math.atanh


class ConditionalData(Node):
	'''
	Outputs from 1 of 2 inputs, depending on condition
	'''
	def __init__(self):
		Node.__init__(self, 'Conditional data')
		self.addInput('condition', True)
		self.addInput('forTrue', 1.)
		self.addInput('forFalse', 2.)
		self.resOut = self.addOutput('decision')
	
	def process(self, condition, forTrue, forFalse):
		self.resOut.push(forTrue if condition else forFalse)
