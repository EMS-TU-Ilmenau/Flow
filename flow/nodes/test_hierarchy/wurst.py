from flow.node import Node, ptype

class Brot(Node):	
	def __init__(self):
		super(Brot, self).__init__('Bemme')
		self.addInput('wurst', 'Salami')
		self.belegt = self.addOutput('brot', ptype.STR)
	
	def process(self, wurst):
		self.belegt.push('Brot mit {}'.format(wurst))