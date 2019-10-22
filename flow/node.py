import logging # for debugging the dataflow
import copy # for deep copying data when output pushes to multiple inputs

log = logging.getLogger(__name__)

class PortType(object):
	'''
	Input or output port type
	'''
	def __init__(self, name, color, dtype):
		self.name = name
		self.color = color
		self.dtype = dtype
	
	def __repr__(self):
		return '{}({})'.format(self.__class__.__name__, 
			', '.join('{}={}'.format(k, v) for k, v in self.__dict__.items()))

	def __str__(self):
		return '{} {}'.format(self.name, self.color)


class PortTypeManager(object):
	'''
	Port type manager to store port datatypes and colors
	'''
	def __init__(self):
		self.__dict__['types'] = {}
		# add main types
		self._addType('OBJECT', '#D0D0D0')
		self._addType('BOOL', '#101010', bool)
		self._addType('INT', '#0080FF', int)
		self._addType('FLOAT', '#25D4EF', float)
		self._addType('COMPLEX', '#AC58FA')
		self._addType('DICT', '#E93333', dict)
		self._addType('LIST', '#FF8000', list)
		self._addType('TUPLE', '#FFD500', tuple)
		self._addType('STR', '#7AC137', str)
		self._addType('FILE', '#198B4A')
	
	def _addType(self, name, color, dtype=None):
		self.__dict__['types'][name] = PortType(name, color, dtype)
	
	def __setattr__(self, name, color):
		'''
		Defines a new port type

		:param name: port type name
		:param color: hex color string, e.g. "#ff0000" is red
		'''
		self._addType(name, color)
	
	def __getattr__(self, name):
		'''
		Looks up port type by name

		:param name: defined port type name
		:returns: port type instance
		'''
		return self.__dict__['types'].get(name)
	
	def fromObj(self, obj):
		'''
		Looks up port type by instance

		:param obj: class instance
		:returns: port type instance
		'''
		for pt in self.__dict__['types'].values():
			if pt.dtype is not None and isinstance(obj, pt.dtype):
				return pt
		
		raise TypeError('No port type for data {} of type {} defined'.format(
			obj, type(obj)))


Ptype = PortTypeManager() # there should be only 1 global instance for the whole package


class Node(object):
	'''
	Base node class.
	May be configured to have arbitrary number of inputs and outputs.
	'''
	
	def __init__(self, name='Node'):
		'''
		:param name: name of the node
		'''
		# make dicts for inputs and outputs
		self.input = {}
		self.output = {}
		self.name = name
		self.busy = False
	
	def __del__(self):
		self.disconnect() # disconnect from other nodes before deleting
	
	def addInput(self, name, *args, **kwargs):
		'''
		Creates a new input port. See InputPort for parameters.
		'''
		inp = InputPort(self, name, *args, **kwargs)
		self.input[name] = inp
		return inp
	
	def addOutput(self, name, *args, **kwargs):
		'''
		Creates a new output port. See OutputPort for parameters.
		'''
		out = OutputPort(self, name, *args, **kwargs)
		self.output[name] = out
		return out
	
	@property
	def inputs(self):
		return self.input.values()
	
	@property
	def outputs(self):
		return self.output.values()
	
	def disconnect(self):
		'''
		Detaches all connections from or to this node
		'''
		# iterate over own outputs
		for out in self.outputs:
			out.disconnect()
		
		# iterate over own inputs
		for inp in self.inputs:
			inp.disconnect()
	
	def reset(self):
		'''
		Is called during graph preparation
		'''
		# reset inputs
		for inp in self.inputs:
			inp.buffer = []
			inp.looped = False
			inp.defaultUsed = False
		
		# reset outputs
		for out in self.outputs:
			out.result = None
		
		self.prepare() # in case there something to prepare
	
	def collect(self):
		'''
		Is called every graph iteration.
		Synchronizes data and calls "process" when all inputs are ready.
		'''
		log.debug('{} is collecting data'.format(self.name))
		if all(inp.couldPull() for inp in self.inputs):
			self.busy = True
			log.debug('{} can process\n'.format(self.name))
			# get data from the inputs when all could pull
			data = {}
			for inp in self.inputs:
				data[inp.name] = inp.pull()
			# process data
			self.process(**data)
		else:
			self.busy = False
			log.debug('{} can NOT process\n'.format(self.name))
	
	def process(self, **inputData):
		'''
		Implementation of the nodes purpose here.
		:param inputData: input names as arguments for their data
		'''
		pass
	
	def prepare(self):
		'''
		Is called before the graph starts processing. 
		Should not be needed in most cases.
		'''
		pass
	
	def finish(self):
		'''
		Is called after the graph has finished processing. 
		Should not be needed in most cases.
		'''
		pass


class InputPort(object):
	'''
	Node input.
	Here, data is obtained either from the inputs of connected nodes, 
	or from default values.
	'''
	
	def __init__(self, node, name='Input', default=None, ptype=Ptype.OBJECT):
		'''
		:param node: the node this port belongs to
		:param name: string name for this input. 
			Only Python variable name style allowed!!!
		:param default: value used in case no data can be pulled
		:param ptype: data type identifier (see Ptype)
		'''
		self.default = default
		self.connOutput = None # the output of the connected node
		self.buffer = [] # queue for the data
		self.looped = False # set by the graph when part of a loop
		self.defaultUsed = False
		self.name = name
		self.node = node
		# auto assign data type
		if default is not None and ptype is Ptype.OBJECT:
			self.ptype = Ptype.fromObj(default)
		else:
			self.ptype = ptype
	
	def connect(self, output):
		'''
		:param output: output port of a node to connect to
		'''
		if output:
			output.connect(self)
	
	def disconnect(self):
		'''
		Disconnects from the currently connected output
		'''
		if self.isConnected():
			self.connOutput.disconnect(self)
	
	def isConnected(self):
		'''
		:returns: boolean indicating connection to an output
		'''
		return True if self.connOutput else False
	
	def couldPull(self):
		'''
		:returns: True when data available, False when not
		'''
		log.debug('Check if {} could pull:'.format(self.name))
		if self.buffer:
			log.debug('\tYes, from buffer')
			return True # take from buffer in normal cases
		elif self.looped or not self.isConnected():
			log.debug('\tNot from buffer, but might use default')
			# when not connected or in a loop, we might need the default.
			if self.default is None:
				log.debug('\tNo, have no default')
				return False
			# however, use only once as long as other inputs don't have data.
			if not self.defaultUsed:
				log.debug('\tYes, using default')
				return True
			if any(inp.buffer for inp in self.node.inputs if inp is not self):
				log.debug('\tYes, using default because other inputs have data')
				return True
			log.debug('\tNo, because default already used and other inputs have no data')
		else:
			log.debug('\tNo, because neither data in buffer nor unconnected or looped')
			return False
	
	def pull(self):
		'''
		:returns: data from the buffer/queue or default value
		'''
		if self.buffer:
			return self.buffer.pop(0) # take from buffer in normal cases
		else:
			self.defaultUsed = True
			return self.default # take default when no data available
			
		return None


class OutputPort(object):
	'''
	Node output.
	Holds connected node inputs and can connect and disconnect
	'''
	
	def __init__(self, node, name='Output', ptype=Ptype.OBJECT):
		'''
		:param node: the node this port belongs to
		:param name: string name for this output. NO SPACES ALLOWED!!!
		:param ptype: data type identifier
		'''
		self.connInputs = [] # list of inputs from connected nodes
		self.result = None # should be used to catch final results for sink ports
		self.name = name
		self.node = node
		self.ptype = ptype
	
	def connect(self, inp):
		'''
		:param inp: input port of a node to connect to
		'''
		# check for datatype (probably just causes trouble (e.g. tuple vs. list))
		if not (inp.ptype is self.ptype or inp.ptype is Ptype.OBJECT or self.ptype is Ptype.OBJECT):
			logging.warning('Type of {}.{} might be incompatible with {}.{}'.format(
				self.node.name, self.name, inp.node.name, inp.name))
		# detach old connection of target input
		inp.disconnect()
		# connect to input
		inp.connOutput = self
		self.connInputs.append(inp)
	
	def disconnect(self, inp=None):
		'''
		Disconnects from specific or all Inputs.
		:param inp: input port of a node to disconnect from or
			None to disconnect from all connected inputs.
		'''
		if inp in self.connInputs:
			# disconnect from input
			inp.connOutput = None
			self.connInputs.remove(inp)
		elif inp is None:
			# disconnect all inputs
			while self.connInputs:
				self.disconnect(self.connInputs[0])
	
	def isConnected(self):
		'''
		:returns: boolean indicating connection to at least 1 input
		'''
		return True if self.connInputs else False
	
	def push(self, data):
		'''
		Pushes data into the buffer of all connected inputs 
		or save as result if unconnected.
		'''
		if self.isConnected():
			share = 0
			for inp in self.connInputs:
				share += 1
				log.info('{}.{} pushing data out to {}.{}'.format(
					self.node.name, self.name, inp.node.name, inp.name))
				if share > 1:
					inp.buffer.append(copy.deepcopy(data))
				else:
					inp.buffer.append(data)
		else:
			self.result = data