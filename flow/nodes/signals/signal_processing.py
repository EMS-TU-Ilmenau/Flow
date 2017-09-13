from flow.node import Node, ptype
import random
import math

class UniformNoise(Node):
	'''Adds uniformly distributed noise separately to each of 
	the Re and Im part of an complex input signal'''
	def __init__(self):
		super(UniformNoise, self).__init__('Uniform noise')
		input = self.addInput('signal', 0+0j) # complex
		self.addInput('lower', -1.)
		self.addInput('upper', 1.)
		self.noiseOut = self.addOutput('noisy', input.type)
	
	def process(self, signal, lower, upper):
		re = signal.real+random.uniform(lower, upper)
		im = signal.imag+random.uniform(lower, upper)
		self.noiseOut.push(complex(re, im))

class GaussNoise(Node):
	'''Adds gauss distributed noise separately to each of 
	the Re and Im part of an complex input signal'''
	def __init__(self):
		super(GaussNoise, self).__init__('Gauss noise')
		input = self.addInput('signal', 0+0j)
		self.addInput('sigma', 1.)
		self.noiseOut = self.addOutput('noisy', input.type)
	
	def process(self, signal, sigma):
		re = signal.real+random.gauss(0., sigma)
		im = signal.imag+random.gauss(0., sigma)
		self.noiseOut.push(complex(re, im))
