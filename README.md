# WoPANets-extension
A simple extension to the network analysis tool wopanets that computes end to end delays, switch backlogs, and stability for networks specified in the WoPANets input format

- The executable class is Main.py.

- Parser.py, Utils.py, Classes.py and Main.py need to be in the same folder. The folder containing the xml samples must be in the same directory.

- Classes.py contains the classes used to represent the network entities, and most of the functions used to calculate the network attributes

- Parser.py contains methods to parse input XML files and produce output XML files with the computed characteristics

- Utils.py contains several helper functions

- The program outputs to a folder called PythonResults

- The following parameters are used to configure the behaviour of the program
	- In Main.py
		- directory: Where to locate the input xml files
		- searchFiles: ".xml" by default The program will examine all files within directory 			  finishing by this string
	- in Utils.py
		- verbose: Enables the program to output status reports to the terminal
		- checkStability: If True, links that are unstable will receive "inf" delays and 			  backlogs. Otherwise, the standard formula will be applied regardless of stability.
	- in Parser.py
		- digitsPrecision: How many digits of precision are used in the output file

