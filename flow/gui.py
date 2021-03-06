#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .graph import Graph, shortString # for building the flow graph
from .node import Ptype # for identifying port data types
from . import nodes # the node database
import os.path as putil # for path utility
import json # for parsing JSON formatted graph files
import logging # for debugging and warning user
import threading # for making graph processing non-blocking
import inspect # for walking the node modules
import importlib # for loading external node packages
import sys # for relative importing
try:
	# for python 2
	import Tkinter as tk # for building the gui
	import tkFont # for sizing node via fontsize
	import tkFileDialog # for opening a file with filedialog
	from ScrolledText import ScrolledText # for easy scrollable text
except:
	# for python 3
	import tkinter as tk
	import tkinter.font as tkFont
	import tkinter.filedialog as tkFileDialog
	from tkinter.scrolledtext import ScrolledText

log = logging.getLogger(__name__)

# global design colors
COL_BG = '#303030' # background
COL_PRIM = '#505050' # primer/base (node body)
COL_MAIN = '#808080' # main/ordinary (node header)
COL_HL = '#F0F0F0' # highlights (most text)
# special colors
COL_DATA = '#A0A0A0' # default and result value texts

def setupHoverColor(widget, hoverCol=COL_MAIN):
	'''
	Add bindings to a widget to change its background color upon hover
	'''
	widget.normalCol = widget.cget('bg')
	widget.bind('<Enter>', lambda _: widget.config(bg=hoverCol))
	widget.bind('<Leave>', lambda _: widget.config(bg=widget.normalCol))


class Point(object):
	'''
	For easier position handling
	'''
	def __init__(self, x, y):
		self.x = x
		self.y = y
	
	def __add__(self, p):
		return Point(self.x+p.x, self.y+p.y)
	
	def __sub__(self, p):
		return Point(self.x-p.x, self.y-p.y)
	
	def __mul__(self, fac):
		return Point(self.x*fac, self.y*fac)
	
	def __div__(self, fac):
		return Point(self.x/fac, self.y/fac)
	
	def __truediv__(self, fac): # used when __future__.division
		return Point(self.x/fac, self.y/fac)
	
	def __str__(self):
		return 'x={}, y={}'.format(self.x, self.y)


class NodeVisual(object):
	'''
	Visual representation of a node.
	'''
	def __init__(self, graphEditor, node, pos=Point(0, 0)):
		self.graphEditor = graphEditor
		self.node = node
		node.visual = self
		self.pos = pos
		self.fontSize = 12
		self.font = tkFont.Font(family='Arial', size=self.fontSize)
		self.dragOffset = Point(0, 0)
		
		# setup layout
		self.body = tk.Frame(self.graphEditor.bg, bg=COL_PRIM)
		self.body.pack()
		
		# header
		head = tk.Frame(self.body, bg=COL_MAIN, cursor='fleur')
		head.bind('<Button-1>', self.onDragStart)
		head.bind('<B1-Motion>', self.onDragMotion)
		# add title
		title = tk.Label(head, text=self.node.name, font=self.font, bg=COL_MAIN, fg=COL_HL)
		title.pack(side=tk.LEFT) # use expand=True to center title
		title.bind('<Button-1>', self.onDragStart)
		title.bind('<B1-Motion>', self.onDragMotion)
		# add delete button
		delBtn = tk.Label(head, text=u' × ', font=self.font, 
			bg=COL_MAIN, fg=COL_HL, cursor='X_cursor')
		delBtn.pack(side=tk.RIGHT)
		delBtn.bind('<Button-1>', lambda _: self.graphEditor.deleteNode(self.node.name))
		# pack header
		head.pack(fill=tk.X)
		
		# add inputs
		for inp in self.node.inputs:
			InputVisual(inp)
		
		# add outputs
		for out in self.node.outputs:
			OutputVisual(out)
		
		self.setPos(self.pos)
	
	def onDragStart(self, *args):
		editorMousePos = self.graphEditor.mousePos()
		editorNodePos = Point(self.body.winfo_x(), self.body.winfo_y())
		self.dragOffset = editorNodePos-editorMousePos
	
	def onDragMotion(self, *args):
		editorMousePos = self.graphEditor.mousePos()
		self.setPos(editorMousePos+self.dragOffset)
	
	def setPos(self, pos):
		'''
		Moves the node to a position in pixel
		:param pos: new position as Point
		'''
		self.pos = pos
		self.body.place(x=pos.x, y=pos.y)
	
	def setScale(self, scale):
		'''
		Sets the node to a given size
		:param scale: relative scale (normal is 1.0)
		'''
		self.font.configure(size=int(self.fontSize*scale))


class InputVisual(object):
	'''
	Visual representation of an input
	'''
	def __init__(self, inp):
		self.input = inp
		self.nodeVisual = self.input.node.visual
		inp.visual = self
		
		# setup layout
		font = self.nodeVisual.font
		self.body = tk.Frame(self.nodeVisual.body, bg=COL_PRIM, 
			highlightbackground=COL_HL, highlightthickness=0) # for step process
		self.body.pack(fill=tk.X)
		
		# add port with color for data type
		self.port = tk.Label(self.body, text=u'⚬', font=font, bg=COL_PRIM, 
			fg=self.input.ptype.color, 
			cursor='crosshair')
		self.port.pack(side=tk.LEFT)
		self.port.input = self # retrieve with: getattr(widget, 'input', None)
		self.port.bind('<Button-1>', self.onConnDrag)
		self.port.bind('<ButtonRelease-1>', self.nodeVisual.graphEditor.onConnDrop)
		
		# add port name
		self.title = tk.Label(self.body, text=self.input.name, font=font, 
			bg=COL_PRIM, fg=COL_HL)
		self.title.pack(side=tk.LEFT, padx=3)
		
		# check if we need a default value
		self.value = None
		self.default = None
		if self.input.default is None:
			return
		# add default value based on data type
		if self.input.ptype in (Ptype.STR, Ptype.FILE):
			# string
			self.value = tk.StringVar()
			self.default = tk.Entry(self.body, textvariable=self.value)
			# file
			if self.input.ptype is Ptype.FILE:
				self.title.bind('<Button-1>', self.openFile)
				self.title.bind('<Button-2>', self.saveFile)
				self.title.bind('<Button-3>', self.saveFile)
				self.title.config(cursor='bottom_side')
		elif self.input.ptype in (Ptype.INT, Ptype.FLOAT):
			# int and float
			if self.input.ptype is Ptype.INT:
				self.value = tk.IntVar()
			else:
				self.value = tk.DoubleVar()
			# setup numeric adjustment by dragging in the title
			self.default = tk.Entry(self.body, textvariable=self.value)
			self.title.bind('<Button-1>', self.startAdjustNum)
			self.title.bind('<B1-Motion>', self.adjustNum)
			self.title.config(cursor='sb_h_double_arrow')
		elif self.input.ptype is Ptype.BOOL:
			# bool
			self.value = tk.BooleanVar()
			self.default = tk.Checkbutton(self.body, variable=self.value)
		
		if self.value:
			# setup value exchange
			self.value.set(self.input.default)
			self.value.trace('w', self.setDefault)
			# apply layout
			self.default.config(font=font, bg=COL_PRIM, fg=COL_DATA, 
				width=0, bd=0, highlightthickness=0)
			self.default.pack(side=tk.LEFT)		
	
	def startAdjustNum(self, e):
		self.lastNum = self.value.get()
		self.lastAdj = e.x
	
	def adjustNum(self, e):
		'''
		Adjust a numeric default value by dragging
		'''
		diff = e.x-self.lastAdj
		# fine-tune sensitivity
		d = abs(diff)
		d = 0.2*d+1e-6*d**4
		d = d if diff > 0 else -d
		self.value.set(self.lastNum+int(d))
	
	def openFile(self, *args):
		'''
		Sets the value to the filepath from the open-dialog
		'''
		self.value.set(tkFileDialog.askopenfilename())
	
	def saveFile(self, *args):
		'''
		Sets the value to the filepath from the save-dialog
		'''
		self.value.set(tkFileDialog.asksaveasfilename())
	
	def setDefault(self, *args):
		'''
		Updates the input default value when user interacts
		'''
		try:
			self.input.default = self.value.get()
		except:
			pass
	
	def defaultVisible(self, visible):
		'''
		:param visible: True or False to show/hide default
		'''
		if self.default:
			if visible:
				self.default.pack()
			else:
				self.default.pack_forget()
	
	def onConnDrag(self, *args):
		self.nodeVisual.graphEditor.dragInput = self


class OutputVisual(object):
	'''
	Visual representation of an output
	'''
	def __init__(self, out):
		self.output = out
		self.nodeVisual = self.output.node.visual
		out.visual = self
		
		# setup layout
		font = self.nodeVisual.font
		self.body = tk.Frame(self.nodeVisual.body, bg=COL_PRIM)
		self.body.pack(fill=tk.X)
		
		# add port with color for data type
		self.port = tk.Label(self.body, text='⚬', font=font, bg=COL_PRIM, 
			fg=self.output.ptype.color, cursor='crosshair')
		self.port.pack(side=tk.RIGHT)
		self.port.output = self
		self.port.bind('<Button-1>', self.onConnDrag)
		self.port.bind('<ButtonRelease-1>', self.nodeVisual.graphEditor.onConnDrop)
		
		# add port name
		title = tk.Label(self.body, text=self.output.name, font=font, 
			bg=COL_PRIM, fg=COL_HL)
		title.pack(side=tk.RIGHT, padx=3)
		
		# add result value
		self.value = tk.StringVar()
		self.result = tk.Label(self.body, textvariable=self.value, 
			font=font, bg=COL_PRIM, fg=COL_DATA)
		self.result.pack(side=tk.RIGHT)
		self.setResult()
	
	def setResult(self):
		'''
		Updates the view to display the ports result
		'''
		resultString = shortString(self.output.result)
		self.value.set(resultString)
		self.resultVisible(True if resultString else False)
	
	def resultVisible(self, visible):
		'''
		:param visible: True or False to show/hide result
		'''
		if self.result:
			if visible:
				self.result.pack()
			else:
				self.result.pack_forget()
	
	def onConnDrag(self, e):
		self.nodeVisual.graphEditor.dragOutput = self


class GraphEditor(object):
	'''
	Visual representation of the graph
	'''
	def __init__(self, app):
		self.app = app
		# canvas for the connection visualization in the background
		self.bg = tk.Canvas(self.app.root, bg=COL_BG, bd=0, highlightthickness=0)
		self.bg.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
		
		# on right click, user can select a node from the database and spawn it
		self.graph = Graph() # logical graph
		self.nodeDB = NodeDatabase(self)
		self.bg.bind('<Button-2>', self.onRightDown) # macOS right-click
		self.bg.bind('<Button-3>', self.onRightDown) # Windows and Linux right-click
		self.spawnPos = Point(10, 10)
		
		# setup zooming
		self.minZoom = 0.5
		self.maxZoom = 3.0
		self.curZoom = 1.0
		self.lastZoom = self.curZoom
		# Windows and macOS
		self.app.root.bind('<MouseWheel>', self.onScroll)
		# Linux
		self.app.root.bind('<Button-4>', self.onScroll)
		self.app.root.bind('<Button-5>', self.onScroll)
		
		# setup connections
		self.dropTarget = None
		self.dragInput = None
		self.dragOutput = None
		self.bg.bind_all('<B1-Motion>', self.onConnDragging)
		
		# setup for panning graph
		self.bg.bind('<Button-1>', self.onLeftClick)
		self.bg.bind('<B1-Motion>', self.onPanning)
	
	def mousePos(self):
		'''
		:returns: mouse position relative to the background
		'''
		return Point(
			self.bg.winfo_pointerx()-self.bg.winfo_rootx(), 
			self.bg.winfo_pointery()-self.bg.winfo_rooty())
	
	def widgetCenterPos(self, widget):
		'''
		:returns: widgets center position relative to the background
		'''
		return Point(
			widget.winfo_rootx()-self.bg.winfo_rootx()+widget.winfo_width()/2, 
			widget.winfo_rooty()-self.bg.winfo_rooty()+widget.winfo_height()/2)
		
	def onScroll(self, e):
		'''
		Hackfix for multiplatform
		'''
		amount = 0.1
		if e.num == 5 or e.delta < 0:
			self.onZoom(-amount)
		if e.num == 4 or e.delta > 0:
			self.onZoom(amount)
	
	def onZoom(self, deltaZoom):
		'''
		Zoomes in or out the graph using the scroll wheel
		'''
		self.lastZoom = self.curZoom
		self.curZoom += deltaZoom
		self.curZoom = min(max(self.curZoom, self.minZoom), self.maxZoom)
		# update node transform
		move = self.lastZoom-self.curZoom
		for node in self.graph.nodes:
			nodeVisual = node.visual
			# scale
			nodeVisual.setScale(self.curZoom)
			# position
			oldPos = nodeVisual.pos
			tarPos = self.mousePos()
			newPos = oldPos*(1.0-move) + tarPos*move
			nodeVisual.setPos(newPos)
		
		# update visual connections for massive changes
		#self.bg.update() # accurate but extreme update lag
		self.bg.after_idle(self.drawConns)
		self.bg.after(100, self.drawConns)
	
	def onLeftClick(self, e):
		'''
		User clicked left on the background
		'''
		self.panStart = Point(e.x, e.y)
		self.bg.focus_set() # to redirect key inputs here (space for searching)
	
	def onPanning(self, e):
		'''
		User is holding and dragging on the background
		'''
		# get relative position since last left click
		panPos = Point(e.x, e.y)
		deltaPos = panPos-self.panStart
		for node in self.graph.nodes:
			nodeVisual = node.visual
			oldPos = nodeVisual.pos
			nodeVisual.setPos(oldPos+deltaPos)
		self.panStart = panPos
	
	def onRightDown(self, e):
		'''
		Shows a popup menu for spawing the nodes
		'''
		# shows the popup menu for spawing the nodes
		self.spawnPos = self.mousePos()
		self.nodeDB.menu.post(e.x_root, e.y_root)
	
	def spawnNode(self, classPath, spawnPos=None, name=''):
		'''
		Instantiates a node in the graph
		:param classPath: class import path. E.g. "flow.nodes.sinks.Print"
		:param spawnPos: Point position where the node is placed
		'''
		# instantiate node
		node = self.graph.nodeFromDatabase(classPath, name)
		# GUI related node modifications
		node.classPath = classPath # remember origin for saving graph
		pos = spawnPos or self.spawnPos
		# place node in graph logically and visually
		self.graph.addNode(node)
		nodeVisual = NodeVisual(self, node, pos)
		nodeVisual.setScale(self.curZoom)
	
	def deleteNode(self, nodeName):
		'''
		Removes a node and its visual from the graph
		:param nodeName: the nodes unique graph-name
		'''
		node = self.graph.nodeDict[nodeName]
		# show connected input defaults
		for out in node.outputs:
			for connInput in out.connInputs:
				connInput.visual.defaultVisible(True)
		# remove from visual panel
		node.visual.body.pack_forget()
		node.visual.body.destroy()
		# remove from logical graph
		self.graph.removeNode(nodeName)
		# update visual connections
		self.drawConns()
	
	def updateResults(self):
		'''
		Updates all output visuals to show current results
		'''
		for node in self.graph.nodes:
			for out in node.outputs:
				out.visual.setResult()
	
	def fromDict(self, graphDict):
		'''
		Creates a graph from a graph dictionary
		'''
		if not 'nodes' in graphDict:
			log.error('No nodes in graph')
			return
		
		# set zoom level
		self.curZoom = graphDict.get('zoom', self.curZoom)

		# load optional external node packages
		extPkgs = graphDict.get('packages')
		if extPkgs:
			try:
				self.graph.scopeNodePkg(extPkgs)
			except ImportError:
				log.error('Could not import node package(s): {}'.format(extPkgs))
		
		# instantiate nodes from class
		for nodeName, nodeEntry in graphDict['nodes'].items():
			pos = nodeEntry.get('pos', [10, 10])
			try:
				self.spawnNode(nodeEntry['class'], Point(*pos), nodeName)
			except:
				log.error('Class {} for node "{}" not in database'.format(
					nodeEntry['class'], nodeName))
		
		# go through a second time to update default and connect
		for nodeName, nodeEntry in graphDict['nodes'].items():
			try:
				node = self.graph.nodeDict[nodeName] # get the already created node
			except:
				continue # related to error above
			for inp in node.inputs:
				try:
					inputEntry = nodeEntry['inputs'][inp.name]
				except:
					log.error('No setup for input "{}" of node "{}" in graph file'.format(
						inp.name, nodeName))
					continue
				# set default
				inp.default = inputEntry.get('default')
				if inp.visual.value:
					inp.visual.value.set(inp.default)
				# set connection
				conn = inputEntry.get('connection')
				if conn:
					try:
						connNode = self.graph.nodeDict[conn['node']]
					except:
						continue # related to error above
					connOutput = connNode.output[conn['output']]
					if connOutput:
						inp.connect(connOutput)
						inp.visual.defaultVisible(False)
					else:
						log.error('Node "{}" has no output "{}" which should be connected '
							'to input "{}" of node "{}"'.format(
							conn['node'], conn['output'], inp.name, nodeName))
		
		# update visual connections slow but accurate
		self.bg.update()
		self.bg.after_idle(self.drawConns)
	
	def toDict(self):
		'''
		:returns: dictionary describing the graph
		'''
		graphDict = {}
		graphDict['zoom'] = self.curZoom
		if self.app.extNodePkgs:
			graphDict['packages'] = self.app.extNodePkgs
		nodeEntries = {}
		graphDict['nodes'] = nodeEntries
		for node in self.graph.nodes:
			# create node entry dict for each node
			nodeEntry = {}
			nodeEntries[node.name] = nodeEntry
			nodeEntry['pos'] = [int(node.visual.pos.x), int(node.visual.pos.y)]
			nodeEntry['class'] = node.classPath
			# create input entry dict for each input
			inputEntries = {}
			nodeEntry['inputs'] = inputEntries
			for inp in node.inputs:
				inputEntry = {}
				inputEntries[inp.name] = inputEntry
				inputEntry['default'] = inp.default
				inputEntry['connection'] = None if not inp.isConnected() else {
					'node': inp.connOutput.node.name, 
					'output': inp.connOutput.name}
		
		return graphDict
	
	def onConnDragging(self, e):
		'''
		Fires when mouse is pressed and moved globally
		'''
		try:
			widget = self.bg.winfo_containing(e.x_root, e.y_root)
			# get latest possible drop target
			self.dropPort = getattr(widget, 'input', None)
			self.dropPort = getattr(widget, 'output', self.dropPort)
			# update visual connections
			self.drawConns()
		except:
			pass # because errors on Linux when clicking on the toolbar
	
	def onConnDrop(self, e):
		'''
		Must handle connection here instead on the ports directly 
		because tkinter (and other GUI frameworks) block other widgets 
		mouse events until the mouse is released.
		'''
		# there are 3 cases of what the last entered port could be:
		# 1. same port as dragged or nothing -> disconnect
		# 2. other port of same gender -> do nothing
		# 3. other port of other gender -> connect
		
		# check if we have picked an input port
		if self.dragInput:
			if self.dropPort is self.dragInput or self.dropPort is None:
				# disconnect
				self.dragInput.input.disconnect()
				self.dragInput.defaultVisible(True)
			elif type(self.dropPort) is OutputVisual:
				# connect
				self.dragInput.input.connect(self.dropPort.output)
				self.dragInput.defaultVisible(False)
				self.dropPort.resultVisible(False)
		
		# check if we have picked an output port
		if self.dragOutput:
			# (no disconnection handling because it may has multiple connections)
			if type(self.dropPort) is InputVisual:
				# connect
				self.dragOutput.output.connect(self.dropPort.input)
				self.dragOutput.resultVisible(False)
				self.dropPort.defaultVisible(False)
		
		# clean up
		self.dragInput = None
		self.dragOutput = None
		self.dropPort = None
		# update visual connections slow but accurate
		self.bg.update()
		self.bg.after_idle(self.drawConns)
	
	def drawSpline(self, inPos, outPos):
		'''
		Draws a spline on the background between inPos and outPos
		:param inPos/outPos: 2D position
		'''
		xDiff = inPos.x-outPos.x
		protude = min(100, abs(xDiff)*0.4)
		self.bg.create_line(
			inPos.x, inPos.y, inPos.x-protude, inPos.y, 
			outPos.x+protude, outPos.y, outPos.x, outPos.y, 
			smooth=1, fill=COL_MAIN, width=int(self.curZoom*2))
	
	def drawConns(self):
		'''
		Draws the current connections in the background
		'''
		self.bg.delete(tk.ALL) # clear old content
		# draw existing connections
		for node in self.graph.nodes:
			for inp in node.inputs:
				if inp.isConnected():
					out = inp.connOutput # connected counterpart
					# get port positions
					inPos = self.widgetCenterPos(inp.visual.port)
					outPos = self.widgetCenterPos(out.visual.port)
					# draw spline
					self.drawSpline(inPos, outPos)
		
		# draw temporary/dragged connection
		if self.dragInput:
			portPos = self.widgetCenterPos(self.dragInput.port)
			self.drawSpline(portPos, self.mousePos())
		if self.dragOutput:
			portPos = self.widgetCenterPos(self.dragOutput.port)
			self.drawSpline(self.mousePos(), portPos)


class NodeDatabase(object):
	'''
	For instantiating nodes from the package modules
	'''
	def __init__(self, graphEditor):
		self.graphEditor = graphEditor
		self.menu = tk.Menu(self.graphEditor.bg) # when user right-clicks on background
		
		# node search related
		self.nodesDict = {}
		self.searchTerm = tk.StringVar()
		self.searchTerm.trace('w', self.onSearching)
		self.graphEditor.bg.bind('<space>', lambda _: self.openSearch())
		# make panel containing search field and result list
		self.searchPanel = tk.Frame(self.graphEditor.bg, bg=COL_PRIM)
		self.searchPanel.pack(side=tk.TOP)
		self.searchPanel.pack_forget() # initially not visible
		# search field
		self.searchField = tk.Entry(self.searchPanel, textvariable=self.searchTerm, 
			highlightthickness=0, bg=COL_BG, fg=COL_HL, bd=0, relief=tk.FLAT)
		self.searchField.pack(fill=tk.X, padx=4, pady=(0, 4))
		self.searchField.bind('<Escape>', lambda _: self.closeSearch())
		self.searchField.bind('<Return>', lambda _: self.selectFirstResult())
		# search result list
		self.searchResults = tk.Frame(self.searchPanel, bg=COL_BG)
		self.searchResults.pack(fill=tk.BOTH, expand=True)
		
		# catch internal nodes
		self.makeNodeMenu(nodes, nodes.__name__, self.menu, self.nodesDict)
		# catch external nodes when available
		for extPkg in self.graphEditor.app.extNodePkgs:
			try:
				extNodes = self.graphEditor.graph.scopeNodePkg(extPkg) # import package
				self.makeNodeMenu(extNodes, extNodes.__name__, self.menu, self.nodesDict)
			except ImportError:
				log.error('Could not load external node lib "{}"'.format(extPkg))
		
		# for faster access, skip the first menu when only 1 database was loaded
		dbs = self.menu.winfo_children()
		if len(dbs) == 1:
			self.menu = dbs[0]
		
		# add search item
		self.menu.add_command(label='Search...', underline=0, command=self.openSearch)
	
	def makeNodeMenu(self, member, pkgName, parentMenu, nodeDict={}):
		'''
		Recursively calls to catch all nodes in the import hierarchy
		'''
		# get import path (module) or class name (class)
		memName = member.__name__ if hasattr(member, '__name__') else ''
		
		# member is a class
		if inspect.isclass(member) and pkgName in member.__module__:
			# get node name because it looks nicer than the class name (it should!)
			itemName = ''
			for srcLine in inspect.getsourcelines(member)[0]:
				if '.__init__(\'' in srcLine or '.__init__(self,\'' in srcLine.replace(' ', ''):
					itemName = srcLine.split('\'')[1]
					break
				elif '.__init__(\"' in srcLine or '.__init__(self,\"' in srcLine.replace(' ', ''):
					itemName = srcLine.split('\"')[1]
					break
			if not itemName:
				return
			# insert in dictionary
			nodePath = '{}.{}'.format(parentMenu.path, memName)
			nodeDict[itemName] = nodePath
			# make menu item
			parentMenu.add_command(label=itemName, underline=0, 
				command=lambda p=nodePath: self.graphEditor.spawnNode(p))
		
		# member is another module
		if inspect.ismodule(member) and pkgName in memName:
			# make menu item
			memMenu = tk.Menu(parentMenu)
			memMenu.path = memName
			itemName = memName.replace('_', ' ').split('.')[-1]
			parentMenu.add_cascade(label=itemName, menu=memMenu, underline=0)
			# call for each sub-member
			subMems = inspect.getmembers(member)
			for mem in subMems:
				self.makeNodeMenu(mem[1], pkgName, memMenu, nodeDict)
	
	def showSearchResults(self, term):
		'''
		Makes a list containing node names matching the searchterm
		'''
		# clear old results
		for child in self.searchResults.winfo_children():
			child.destroy()
		if not term:
			return
		# populate list with results
		for nodeName, nodePath in self.nodesDict.items():
			if term.lower() in nodeName.lower():
				found = tk.Label(self.searchResults, text=nodeName, anchor='w', 
					bg=COL_PRIM, fg=COL_HL, font=('Arial', 12))
				setupHoverColor(found)
				found.bind('<Button-1>', lambda e, p=nodePath: self.selectResult(p))
				found.pack(fill=tk.X)
	
	def openSearch(self):
		'''
		Shows the search panel
		'''
		self.searchPanel.pack()
		self.searchField.focus_set()
	
	def closeSearch(self):
		'''
		Resets search term hides the search panel
		'''
		self.searchTerm.set('')
		self.searchPanel.pack_forget()
		self.graphEditor.bg.focus_set()
	
	def onSearching(self, *args):
		'''
		Shows the search panel
		'''
		self.showSearchResults(self.searchTerm.get())
	
	def selectFirstResult(self):
		'''
		Spawns first node in search result list
		'''
		results = self.searchResults.winfo_children()
		if results:
			first = results[0]
			self.selectResult(self.nodesDict[first.cget('text')])
	
	def selectResult(self, nodePath):
		'''
		Spawns the node and closes the search
		'''
		self.graphEditor.spawnNode(nodePath)
		self.closeSearch()


class LogHandler(object):
	'''
	Logging and warnings
	'''
	def __init__(self, app):
		self.app = app
		self.enabled = True # enabling or disabling logging
		
		# get package loggers
		self.loggers = []
		self.pkgName = __name__.split('.')[0]
		for name in logging.Logger.manager.loggerDict.keys():
			if self.pkgName in name:
				self.loggers.append(logging.getLogger(name))
		
		self.font = tkFont.Font(family='Courier New', size=12)
		# make text for normal logs
		self.logFrame = tk.Frame(self.app.root)
		self.logScroll = ScrolledText(self.app.root, bd=0, highlightthickness=0, 
			font=self.font, bg=COL_PRIM, fg=COL_HL, width=80)
		self.logScroll.pack(side=tk.RIGHT, fill=tk.Y)
		
		# make warning panel
		self.alert = tk.Label(self.app.graphEditor.bg, cursor='X_cursor', 
			font=self.font, bg=COL_HL, fg=COL_BG)
		self.alert.bind('<Button-1>', lambda _: self.resetWarning())
		self.alert.pack(side=tk.TOP)
		self.alert.pack_forget() # initially not visible
		
		self.enableLog(False) # initially, disable normal logs
	
	def enableLog(self, enable):
		'''
		Enables/Disables logging and shows/hides the log scroll
		'''
		self.enabled = enable
		if enable:
			# slow, but comprehensive logging
			self.logScroll.pack(side=tk.RIGHT, fill=tk.Y)
			self.setLogLevel(logging.DEBUG)
		else:
			# only alerts can occur now
			self.clear()
			self.logScroll.pack_forget()
			self.setLogLevel(logging.WARNING)
	
	def setLogLevel(self, level):
		'''
		Sets all package related loggers to a new level.
		This results in better performance, but other log handlers 
		won't see messages below level too of course.
		'''
		for logger in self.loggers:
			logger.setLevel(level)
	
	def warn(self, warning):
		'''
		Shows a warning
		'''
		# append linefeed to current text
		curText = self.alert.cget('text')
		if curText and not curText.endswith('\n'):
			curText += '\n'
		# add warning to current text and show
		self.alert.config(text=curText+warning)
		self.alert.pack()
	
	def resetWarning(self):
		'''
		Resets the warnings in the alert panel
		'''
		self.alert.config(text='')
		self.alert.pack_forget()
	
	def write(self, msg):
		'''
		This method is called from the logging module for each message
		'''
		if any(lvl in msg for lvl in ('WARNING', 'ERROR', 'CRITICAL')):
			# user needs attention
			self.warn(msg)
		
		if self.enabled:
			# normal logging
			self.logScroll.insert(tk.END, msg)
	
	def flush(self):
		'''
		This method might be called from the logging module
		'''
		pass
	
	def tail(self):
		'''
		Scrolls down to the last messages
		'''
		if self.enabled:
			self.logScroll.see(tk.END) # super useful but super slow
	
	def clear(self):
		self.logScroll.delete(1.0, tk.END)


class FlowApp(object):
	'''
	Main window of the application
	'''
	def __init__(self, extNodePkgs=[]):
		'''
		:param extNodePkgs: optional list with strings of external node packages to load
		'''
		self.root = tk.Tk()
		self.root.protocol('WM_DELETE_WINDOW', self.onQuit) # window closing redirected to quit
		self.extNodePkgs = extNodePkgs
		self.step = 0 # for manual processing nodes step-by-step
		self.graphStop = threading.Event() # for stopping the graph
		self.graphThread = None
		
		# initially place in the middle of the screen
		size = Point(1280, 720)
		screen = Point(self.root.winfo_screenwidth(), self.root.winfo_screenheight())
		pos = screen/2-size/2
		self.root.geometry('{}x{}+{}+{}'.format(size.x, size.y, int(pos.x), int(pos.y)))
		self.root.title('Graph Editor')
		
		# making the menus
		self.makeMenubar()
		self.makeToolbar()
		
		# background panel where node visuals are placed
		self.graphEditor = GraphEditor(self)
		
		# setup logging
		self.logHandler = LogHandler(self)
		logging.basicConfig(stream=self.logHandler, level=logging.WARNING)
		
		# start working
		while True:
			try:
				self.root.mainloop()
				break
			except UnicodeDecodeError:
				pass # because fast scrolling in python3 on macOS
	
	def makeMenubar(self):
		'''Creates the menubar with a file menu for saving and opening a graph'''
		# make menu bar
		menubar = tk.Menu(self.root)
		self.root.config(menu=menubar)
		# make file menu
		fileMenu = tk.Menu(menubar)
		fileMenu.add_command(label='Open graph', command=self.onOpen)
		fileMenu.add_command(label='Save graph', command=self.onSave)
		fileMenu.add_separator()
		fileMenu.add_command(label='Quit', command=self.onQuit)
		# add file menu to menubar
		menubar.add_cascade(label='File', menu=fileMenu)
	
	def onOpen(self):
		'''
		Opens a json file containing a graph
		'''
		filepath = tkFileDialog.askopenfilename()
		if filepath: # not canceled
			self.onClear() # clear old graph
			with open(filepath) as file:
				try:
					graphDict = json.loads(file.read()) # read file content as dict
					self.graphEditor.fromDict(graphDict)
				except:
					log.error('Invalid graph file')
	
	def onSave(self):
		'''
		Saves the current graph as a json encoded file
		'''
		filepath = tkFileDialog.asksaveasfilename()
		if filepath: # not canceled
			graphDict = self.graphEditor.toDict()
			with open(filepath, 'w') as file:
				file.write(json.dumps(graphDict, indent=4))
	
	def onQuit(self):
		# stop running graph
		if not self.stopGraph():
			log.warning('The graph is still processing. Stopping it now')
			return
		# quit the application
		self.root.quit()
	
	def addTool(self, icon, callback, side=tk.LEFT):
		'''
		Creates a button with icon.
		:param icon: icon file name
		:param callback: function to fire when button is clicked
		'''
		# get icon path in the package
		pkgPath = putil.dirname(__file__)
		iconPath = putil.join(pkgPath, 'gui_icons')
		# make button
		img = tk.PhotoImage(file='{}/{}'.format(iconPath, icon))
		btn = tk.Label(self.toolbar, image=img, bg=COL_PRIM)
		setupHoverColor(btn)
		btn.bind('<Button-1>', lambda _: callback()) # bind callback function
		btn.image = img # to prevent garbage collection of the image
		btn.pack(side=side)
	
	def makeToolbar(self):
		'''
		Creates the toolbar with icons for controlling the graph
		'''
		# make toolbar
		self.toolbar = tk.Frame(self.root, bg=COL_PRIM)
		self.toolbar.pack(side=tk.TOP, fill=tk.X)
		# add tools
		self.addTool('run.gif', self.onRun)
		self.addTool('step.gif', self.onStep)
		self.addTool('reset.gif', self.onReset)
		self.addTool('clear.gif', self.onClear)
		self.addTool('bug.gif', self.onLogEnable, tk.RIGHT)
		# make a small stats display
		self.stats = tk.StringVar()
		tk.Label(self.toolbar, textvariable=self.stats, 
			bg=COL_PRIM, fg=COL_HL).pack(side=tk.RIGHT, padx=10)
	
	def graphReady(self):
		'''
		:returns: True if graph is ready, False else
		'''
		# check if there is even a graph
		if not self.graphEditor.graph.nodes:
			return False
		# stop already running graph
		return self.stopGraph()
	
	def stopGraph(self):
		'''Tries to stop a running graph.
		:returns: True when graph is not running, else False'''
		if self.graphThread and self.graphThread.is_alive():
			if self.graphStop.is_set():
				log.error('Already tried to stop graph')
				self.graphThread.join(5)
				if self.graphThread.is_alive():
					log.fatal('Cannot stop graph')
				else:
					return True
			else:
				self.graphStop.set()
			return False
		return True
	
	def _graphRun(self, stopper):
		try:
			self.stats.set('processing...')
			_, iterCount, iterTime = self.graphEditor.graph.process(stopper)
			self.stats.set('{} | {:.2f} ms'.format(iterCount, 1e3*iterTime))
		except:
			self.stats.set('')
			log.exception('Graph processing failed')
		self.graphEditor.updateResults() # update visual results
		self.logHandler.tail()
		stopper.clear()
	
	def onRun(self):
		'''
		Runs the graph and shows the results
		'''
		if not self.graphReady():
			return
		
		self.onReset() # preparations
		# start processing
		self.graphThread = threading.Thread(target=self._graphRun, args=(self.graphStop,))
		self.graphThread.start()
	
	def onStep(self):
		'''
		Runs graph step-by-step, i.e. one node process at a call
		'''
		if not self.graphReady():
			return
		
		if not self.graphEditor.graph.prepared:
			self.onReset()
		runOrder = self.graphEditor.graph.nodesRunOrder
		# get last processed node to reset highlight
		if self.step > 0:
			node = runOrder[(self.step % len(runOrder))-1]
			node.visual.body.config(highlightthickness=0)
		# get current node to process and highlight
		node = runOrder[self.step % len(runOrder)]
		node.visual.body.config(highlightthickness=2)
		# process
		try:
			node.collect()
			self.graphEditor.updateResults()
			self.logHandler.tail()
		except:
			log.exception('Node {} failed to process'.format(node.name))
		self.step += 1
	
	def onReset(self):
		'''
		Resets the graph prior to run
		'''
		if not self.graphReady():
			return
		
		self.logHandler.clear() # clear log
		self.logHandler.resetWarning() # reset warning
		self.stats.set('')
		try:
			self.graphEditor.graph.prepare()
		except:
			log.exception('Preparing graph failed')
		self.graphEditor.updateResults()
		# reset stepping
		for node in self.graphEditor.graph.nodes:
			node.visual.body.config(highlightthickness=0)
		self.step = 0
	
	def onClear(self):
		'''
		Clears graph, i.e. delete all nodes
		'''
		if not self.graphReady():
			return
		
		self.stats.set('')
		# list because python3
		for nodeName in list(self.graphEditor.graph.nodeDict.keys()):
			self.graphEditor.deleteNode(nodeName)
	
	def onLogEnable(self):
		'''
		Toggle log enabled
		'''
		self.logHandler.enableLog(not self.logHandler.enabled)


def startApp(extNodePkgs=[]):
	'''
	starts the GUI
	'''
	FlowApp(extNodePkgs)


if __name__ == '__main__':
	startApp()