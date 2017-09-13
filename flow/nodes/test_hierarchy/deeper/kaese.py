from flow.node import Node, ptype

class Stulle(Node):	
	def __init__(self):
		super(Stulle, self).__init__('Stulle')
		self.addInput('kaese', 'Gauda')
		self.belegt = self.addOutput('brot', ptype.STR)
	
	def process(self, kaese):
		self.belegt.push('Brot mit {}'.format(kaese))