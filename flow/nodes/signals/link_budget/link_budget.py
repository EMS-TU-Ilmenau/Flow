from flow.node import Node, ptype
import random
import math

c = 299792458.0 # speed of light in m/s
wavelength = lambda f: c/f

class WattToDBm(Node):
	'''Linear power in Watt to Milliwatt-decibel'''
	def __init__(self):
		super(WattToDBm, self).__init__('Watt to dBm')
		self.addInput('watt', 0.001)
		self.dBmOut = self.addOutput('dBm', ptype.FLOAT)
	
	def process(self, watt):
		self.dBmOut.push(10*math.log10(1e3*watt))

class DBmToWatt(Node):
	'''Milliwatt-Decibel to linear power in Watt'''
	def __init__(self):
		super(DBmToWatt, self).__init__('dBm to Watt')
		self.addInput('dBm', 0.)
		self.wattOut = self.addOutput('watt', ptype.FLOAT)
	
	def process(self, dBm):
		self.wattOut.push(1e-3*math.pow(10, dBm/10))

class Amplifier(Node):
	'''Amplifies a signal in dB'''
	def __init__(self):
		super(Amplifier, self).__init__('Amplifier')
		self.addInput('signal')
		self.addInput('ampDB', 10.)
		self.signalOut = self.addOutput('signal')
	
	def process(self, signal, ampDB):
		self.signalOut.push(signal+ampDB)

class Attenuator(Node):
	'''Attenuates a signal in dB'''
	def __init__(self):
		super(Attenuator, self).__init__('Attenuator')
		self.addInput('signal')
		self.addInput('attnDB', 10.)
		self.signalOut = self.addOutput('signal')
	
	def process(self, signal, attnDB):
		self.signalOut.push(signal-attnDB)

class FreespaceLoss(Node):
	'''Attenuation of a signal with frequency over a distance in free space'''
	def __init__(self):
		super(FreespaceLoss, self).__init__('Freespace loss')
		self.addInput('freqMHz', 1000.)
		self.addInput('distanceM', 1.)
		self.fsplOut = self.addOutput('lossDB')
	
	def process(self, freqMHz, distanceM):
		fspl = (4*math.pi*distanceM/wavelength(freqMHz*1e6))**2
		self.fsplOut.push(10*math.log10(fspl))

class FarfieldBNetzA(Node):
	'''Far field distance for a given frequency 
	based on the definition of the Bundesnetzagentur.'''
	def __init__(self):
		super(FarfieldBNetzA, self).__init__('Farfield BNetzA')
		self.addInput('freqMHz', 1000.)
		self.ffOut = self.addOutput('farfieldM')
	
	def process(self, freqMHz):
		self.ffOut.push(4*wavelength(freqMHz*1e6))

class FarfieldAperture(Node):
	'''Far field distance for a given frequency and aperture.'''
	def __init__(self):
		super(FarfieldAperture, self).__init__('Farfield aperture')
		self.addInput('freqMHz', 1000.)
		self.addInput('apertureM', 0.2)
		self.ffOut = self.addOutput('farfieldM')
		self.antOut = self.addOutput('longAnt', ptype.BOOL)
	
	def process(self, freqMHz, apertureM):
		l = wavelength(freqMHz*1e6)
		if apertureM > l:
			# long antenna
			self.ffOut.push(2*apertureM**2/l)
			self.antOut.push(True)
		else:
			# short antenna
			self.ffOut.push(2*l)
			self.antOut.push(False)
