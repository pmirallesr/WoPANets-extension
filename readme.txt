Author: Pablo Miralles Roure

- The executable class is Main.py.

- Parser.py, Utils.py, Classes.py and Main.py need to be in the same folder. The folder containing the xml samples must be in the same directory.

- The program outputs to a folder called PythonResults

- Several parameters exist
	- In Main.py
		- directory: Where to locate the input xml files
		- searchFiles: ".xml" by default The program will examine all files within directory 			  finishing by this string
	- in Utils.py
		- verbose: Enables the program to output status reports to the terminal
		- checkStability: If True, links that are unstable will receive "inf" delays and 			  backlogs. Otherwise, the standard formula will be applied regardless of stability.
	- in Parser.py
		- digitsPrecision: How many digits of precision are used in the output file
