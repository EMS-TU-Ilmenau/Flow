from flow.node import Node
import random
import math

class UniformNoise(Node):
	'''Adds uniformly distributed noise to an input signal'''
	def __init__(self):
		super(UniformNoise, self).__init__('Uniform noise')
		self.addInput('signal')
		self.addInput('lower', -1.)
		self.addInput('upper', 1.)
		self.noiseOut = self.addOutput('noisy', float)
	
	def process(self, signal, lower, upper):
		self.noiseOut.push(signal+random.uniform(lower, upper))

class GaussNoise(Node):
	'''Adds gauss distributed noise to an input signal'''
	def __init__(self):
		super(GaussNoise, self).__init__('Gauss noise')
		self.addInput('signal')
		self.addInput('sigma', 1.)
		self.noiseOut = self.addOutput('noisy', float)
	
	def process(self, signal, sigma):
		self.noiseOut.push(signal+random.gauss(0., sigma))

class WattToDBm(Node):
	'''Linear power in Watt to Milliwatt-decibel'''
	def __init__(self):
		super(WattToDBm, self).__init__('Watt to dBm')
		self.addInput('watt', 0.001)
		self.dBmOut = self.addOutput('dBm', float)
	
	def process(self, watt):
		self.dBmOut.push(10*math.log10(1e3*watt))

class DBmToWatt(Node):
	'''Milliwatt-Decibel to linear power in Watt'''
	def __init__(self):
		super(DBmToWatt, self).__init__('dBm to Watt')
		self.addInput('dBm', 0.)
		self.wattOut = self.addOutput('watt', float)
	
	def process(self, dBm):
		self.wattOut.push(1e-3*math.pow(10, dBm/10))
