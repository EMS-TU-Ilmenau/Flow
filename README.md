# Flow
Flow based programming with an optional GUI for fast prototyping, visualizing calculations and processing, etc.

### Author
Niklas Beuster -- niklas.beuster@tu-ilmenau.de


![Showcase](Showcase.png)

## Getting started
Clone the repository and change to that directory. 

Optionally, install the package using `pip install .` or `pip install --user .`

#### Backend
To use the backend ([graph](flow/graph.py) and [node](flow/node.py)) without the GUI, run [test_graph.py](test_graph.py) with a graph file as argument:

`python test_graph.py examples/loop.json`

#### GUI
To use the [GUI](flow/gui.py), run [test_gui.py](test_gui.py):

`python test_gui.py`

Open and save graphs using the **File menu**.
You can add nodes by **right-clicking** on the dark background and choose a node from the tree.
**Scroll** on the dark background to navigate in the graph.
Add more nodes and connect them or test what happens when you just hit the **run** button (the triangle without the pipe).
When something seems broken, click the **step** button (triangle with pipe) to stop and step through the graph.
You can click the **log** button (the bug) and step or run again to get detailed informations.
You can reset or clear a graph using the other buttons.

#### Porttypes
The port types are just a rough orientation for the user when to connect nodes.
Knowing if nodes can connect beforehand is impossible because beside the datatype, there would be other conditions why data could be incompatible, e.g. length of an vector, shape of tensors, etc.
It would also be too restrictive to allow only same datatypes to connect, because a node could iterate over tuples and lists just fine for example.

What they **do**:
- Specify the port [color](flow/gui.py)
- Defines the GUI widgets as an interface for the user to input default values
	- For `float` and `int`, the user can click and **drag** the inputs title to enter values more convenient
	- For `file`, the user can **left-click** for an open file dialog and **right-click** for a save file dialog
	- For `bool`, there is a checkbox
- Warn the user when connecting port of different type

What they do **not**:
- Care about incompatible data processing


## Making a new node
You can either add a new node to an existing module or even create your own module.
Either case, writing a new node class is the same:

```python
from flow.node import Node, ptype

class MyNode(Node):
	def __init__(self):
		super(MyNode, self).__init__('My nodes name')
		# add some inputs, but at least 1
		self.addInput('someInput') # no spaces allowed for input names
		self.addInput('other', 3.0) # default defines porttype automatically
		self.addInput('bla', type=ptype.BOOL) # no default, but type specified
		# add some outputs, but at least 1
		self.myOut = self.addOutput('out', ptype.STR) # string type specified
	
	def process(self, someInput, other, bla):
		# process inputs
		result = '{}, {}, {}'.format(someInput, other, bla)
		# push results
		self.myOut.push(result)
```

Note that only **[JSON](https://www.w3schools.com/js/js_json_datatypes.asp) compatible default values** must be passed! 
For other porttypes, specify the `type` argument, e.g. type=ptype.COMPLEX. 
You may also have a look at the already existing [nodes](flow/nodes/).

In order to load the node in the GUI, two things are of importance:
- the line `super(MyNode, self).__init__('My nodes name')` (you can use single or double quotes for the name)
- the class needs to be importable from the [nodes](flow/nodes/) directory in the package.

#### Make a new module
When making a bunch of new node classes that are needed in a specific field (e.g. plotting, signal processing, device controls, ...) it is a good idea to make a new module.

The root of all node modules is [nodes](flow/nodes/).
As you can see, there are even subdirectories, which can contain modules, and other subdirectories, to specialize even further.

Let's say we want to make a module `my_fancy_nodes.py` in its own subdirectory `my_fancy_lib`:
- Create a folder in `nodes`and name it `my_fancy_lib`.
- Open the `__init__.py` file in the root and add `from . import my_fancy_lib` to the end. Save, close.
- Enter the newly created folder and create a file named `my_fancy_nodes.py`
- Open the file and write `from flow.node import Node, ptype`, then add your node class as described above. Save, close.
- Create a `__init__.py` file in the same folder.
- Open the file and write `from . import my_fancy_nodes.py`. Save, close.

That's it. The GUI will automatically recognize the new module and all node classes inside when started.

## Concept
The general concept is called **flow based programming** (FBP). 
It allows to handle data as if they are signals in the real world by connecting **inputs** and **outputs** of **nodes** together in a **graph**, like connecting devices via cables. 
This makes it intuitive for an end-user to build algorithms without programming. 
It is also useful for fast prototyping because useful code snippets is already there and have to be combined only.

This implementation transports data between the nodes and stores them in the inputs **buffer**. 
The node calls a **process** function when the data is synchronized and **pulled** from inputs.
Depending on the nodes purpose, processed data is **pushed** to the output(s). 
An output pushes data to all **connected** inputs, where it is queued in the input buffer.

Inputs have another data source, the **default** value, which is used for special cases. 
If the input is **disconnected**, i.e. no pipe attached, the default value gets visible in the GUI and the user can enter a value based on the **port type**. 
The default value is used **once** when the input is not connected or when the input is part of a **loop** and no package is in the buffer.
It is also used **always** when other inputs of the node have data in their buffers. 
pers can use this in conjuction with pulling, when input data should be processed synchronized and no pull should be wasted.

Outputs push data to a **result** if the port is not connected. 

#### Why not backward recursion?
A similar concept would be to recursively pull data from the nodes, starting from the sinks, until the sources are reached.
This sounds easy and fast, but there are some problems with that concept:

**Interface on output level**:
How would that concept be implemented? Each output would have a pull method, which would get the results from an output specific process method, that would pull from inputs which pull from connected outputs, etc.
The graph would be run be calling the pull method of all sink outputs.
To develop a new node, usually one wants only to implement the purpose, i.e. the processing method of a node.
The problem is, either there is only 1 output allowed to have a node-wide processing method, or each output would need its own process method.
The latter requires to either monkey-patch each created output in a node, or inherit new output classes.

**Synchronizing**:
If there is no node-wide process method, and each output have its own process method, how would input data be handled?
Think about it: the inputs belong to the node, for a user, it is not obvious which inputs are needed for an output.

**Time variance**:
The above problem could only be solved by restricting the graph to only process static data, i.e. the data in the graph must never change.
When multiple outputs pull from the same source, which would change its data, data is not synchronized anymore.
Imagine a node generating a random sample on each pull request.
When multiple connected nodes pull from that noise-generator, the data is not synchronized.

## Third party packages
The project is very generic, as any python code can be inside the node.
That means one could use the node editor primarily for signal processing, while someone else might use it for device controls/measurements or image processing as e.g. in Blender.
Most nodes will probably be just interfaces for already existing, mighty functions or classes from third party packages like fastmat, numpy or matplotlib.
That means a lot of third party code to install, which might not be needed for the other fields.

Therefore, only generic and standard library only nodes should be pushed to this project if any.
The existing nodes are merely examples and for demonstration purposes.

For real applications, proceed as follow:
- Install this project using `pip install .` or `pip install --user .` after `cd` to the cloned project
- In your own project (the real application), make sure the minial file structure is as follows:

```
- your_project
	- __init__.py (can be empty)
	- external_nodes (exactly this name! Can be layout like [nodes](flow/nodes/) inside)
		- __init__.py (must import your node modules)
		- [your node modules]
	- start_gui.py (can be any name, this is your GUI starter)
```

In your GUI starter, you need at least this code:

```python
import os, sys # for extending node database searchpath
from flow import gui # for nodeeditor

# add this packages nodes to the searchpath of the GUI
sys.path.append(os.path.abspath('.'))

gui.startApp()
```