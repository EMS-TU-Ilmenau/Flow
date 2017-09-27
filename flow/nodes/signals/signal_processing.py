from flow.node import Node, ptype
import random
import math

class UniformNoise(Node):
	'''Adds uniformly distributed noise separately to each of 
	the Re and Im part of a complex number'''
	def __init__(self):
		super(UniformNoise, self).__init__('Uniform noise')
		input = self.addInput('signal', type=ptype.COMPLEX)
		self.addInput('lower', -1.)
		self.addInput('upper', 1.)
		self.noiseOut = self.addOutput('noisy', input.type)
	
	def process(self, signal, lower, upper):
		re = signal.real+random.uniform(lower, upper)
		im = signal.imag+random.uniform(lower, upper)
		self.noiseOut.push(complex(re, im))

class GaussNoise(Node):
	'''Adds gauss distributed noise separately to each of 
	the Re and Im part of a complex number'''
	def __init__(self):
		super(GaussNoise, self).__init__('Gauss noise')
		input = self.addInput('signal', type=ptype.COMPLEX)
		self.addInput('sigma', 1.)
		self.noiseOut = self.addOutput('noisy', input.type)
	
	def process(self, signal, sigma):
		re = signal.real+random.gauss(0., sigma)
		im = signal.imag+random.gauss(0., sigma)
		self.noiseOut.push(complex(re, im))

class ComplexToMagnPhase(Node):
	'''Converts a complex number to magnitude and phase angle in rad'''
	def __init__(self):
		super(ComplexToMagnPhase, self).__init__('Complex to magnitude and phase')
		self.addInput('signal', type=ptype.COMPLEX)
		self.magnOut = self.addOutput('magnitude', ptype.FLOAT)
		self.phaseOut = self.addOutput('phaseRad', ptype.FLOAT)
	
	def process(self, signal):
		# magnitude
		magn = math.sqrt(signal.imag**2 + signal.real**2)
		self.magnOut.push(magn)
		# phase in radians
		phase = math.atan2(signal.imag, signal.real)
		self.phaseOut.push(phase)

class MagnPhaseToComplex(Node):
	'''Converts magnitude and phase angle in rad to a complex number'''
	def __init__(self):
		super(MagnPhaseToComplex, self).__init__('Magnitude and phase to complex')
		self.addInput('magnitude', 1.)
		self.addInput('phaseRad', 0.)
		self.complexOut = self.addOutput('signal', ptype.COMPLEX)
	
	def process(self, magnitude, phaseRad):
		re = magnitude*math.cos(phaseRad) # real part
		im = magnitude*math.sin(phaseRad) # imaginary part
		self.complexOut.push(complex(re, im))
