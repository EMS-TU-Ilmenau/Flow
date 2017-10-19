from flow.node import Node, ptype

def cableAttn(fMHz, lm, a, b):
	'''Cable attenuation per meter at frequency.
	:param fMHz: frequency in MHz
	:param lm: cable length in m
	:param a, b: coefficients'''
	fGHz = fMHz/1000.
	return lm*(a*(fGHz**0.5) + b*fGHz)

class CableAttn(Node):
	'''Abstract class for cable attenuation per meter at frequency'''
	def __init__(self, name):
		super(CableAttn, self).__init__(name)
		self.addInput('fMHz', 140.)
		self.addInput('cableLenM', 1.)
		self.attnOut = self.addOutput('attnDB', ptype.FLOAT)
		self.a = 1.
		self.b = 1.
	
	def process(self, fMHz, cableLenM):
		self.attnOut.push(cableAttn(fMHz, cableLenM, self.a, self.b))

class CustomCable(CableAttn):
	'''User can set a and b coefficients'''
	def __init__(self):
		super(CustomCable, self).__init__('Custom cable')
		self.addInput('a', 0.1)
		self.addInput('b', 0.01)
	
	def process(self, fMHz, cableLenM, a, b):
		self.attnOut.push(cableAttn(fMHz, cableLenM, a, b))

class SUCOFORM141(CableAttn):
	def __init__(self):
		super(SUCOFORM141, self).__init__('H+S Sucoform 141')
		self.a = 0.355
		self.b = 0.04

class SUCOFORM86(CableAttn):
	def __init__(self):
		super(SUCOFORM86, self).__init__('H+S Sucoform 86')
		self.a = 0.6283
		self.b = 0.04

class G03232D01(CableAttn):
	def __init__(self):
		super(G03232D01, self).__init__('H+S G 03232 D-01')
		self.a = 0.431
		self.b = 0.135

class EZ118TP(CableAttn):
	def __init__(self):
		super(EZ118TP, self).__init__('H+S EZ 118 TP')
		self.a = 0.3804
		self.b = 0.00791

class EZ141TPM17(CableAttn):
	def __init__(self):
		super(EZ141TPM17, self).__init__('H+S EZ 141 TP M17')
		self.a = 0.32544
		self.b = 0.03967

class SX04172B60(CableAttn):
	def __init__(self):
		super(SX04172B60, self).__init__('H+S SX 04172 B-60')
		self.a = 0.233
		self.b = 0.0575

class LCF1450J(CableAttn):
	def __init__(self):
		super(LCF1450J, self).__init__('LCF14-50J')
		self.a = 0.13
		self.b = 0.0092

class LCF1250J(CableAttn):
	def __init__(self):
		super(LCF1250J, self).__init__('LCF12-50J')
		self.a = 0.067
		self.b = 0.00549

class LCF7850JAA0(CableAttn):
	def __init__(self):
		super(LCF7850JAA0, self).__init__('LCF78-50JA-A0')
		self.a = 0.035
		self.b = 0.003

class Ecoflex10(CableAttn):
	def __init__(self):
		super(Ecoflex10, self).__init__('Ecoflex10')
		self.a = 0.123
		self.b = 0.019

class H155(CableAttn):
	def __init__(self):
		super(H155, self).__init__('H155')
		self.a = 0.285
		self.b = 0.024
