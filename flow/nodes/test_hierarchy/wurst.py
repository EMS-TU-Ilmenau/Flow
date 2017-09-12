from flow.node import Node

class Brot(Node):	
	def __init__(self):
		super(Brot, self).__init__('Bemme')
		self.addInput('wurst', 'Salami')
		self.belegt = self.addOutput('brot', str)
	
	def process(self, wurst):
		self.belegt.push('Brot mit {}'.format(wurst))