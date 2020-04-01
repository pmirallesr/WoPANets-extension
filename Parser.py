from xml.etree.ElementTree import Element, SubElement, parse, ElementTree
import Classes
from Utils import createQuantity, printIfVerbose, interpretQuantity

digitsPrecision = 2 # Number of decimal places included in results

def indent(elem, level=0):
    i = "\n" + level*"\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

def produceXML(net, name):
    """" Writes the results XML object to the file given by name following the results file standard"""
    resultsXML = Element('results')
    
    delaysXML = SubElement(resultsXML, "delays")
    for flow in net.flows.values():
        flowXML = SubElement(delaysXML, "flow", {"name":flow.name})
        for target in flow.targets.values():
            delay = str(createQuantity(target.computeEndToEndDelay(), digitsPrecision, omitUnit = True, selectUnit = "u"))
            SubElement(flowXML, "target", {"name": target.name, "value": delay})
    
    jittersXML = SubElement(resultsXML, "jitters")
    for flow in net.flows.values():
        flowXML = SubElement(jittersXML, "flow", {"name":flow.name})
        for target in flow.targets.values():
            delay = "0"
            target = SubElement(flowXML, "target", {"name": target.name, "value": delay})

    backlogsXML = SubElement(resultsXML, "backlogs")
    for switch in net.switches.values():
        switchXML = SubElement(backlogsXML, "switch", {"name": switch.name})
        for outLink in switch.getLinks():
            delay = str(createQuantity(switch.getDelay(outLink), digitsPrecision, omitUnit = True, selectUnit = "u"))
            backlog = str(createQuantity(switch.getBacklog(outLink), digitsPrecision))
            if (backlog == "0"):
                continue
            SubElement(switchXML, "port", {"backlog": str(backlog + "b"), "delay": delay, "num": str(outLink.getPort(switch))})
        SubElement(switchXML, "total", {"backlog": str(createQuantity(switch.getTotalBacklog(), digitsPrecision) + "b"), "buffer": str(switch.buffer), "percent": "{:.1f}%".format(100 * switch.getTotalBacklog()/switch.buffer)})
    
    loadsXML = SubElement(resultsXML, "loads")
    for link in net.links.values():
        edgeXML = SubElement(loadsXML, "edge", {"name": link.name})
        SubElement(edgeXML, "usage", {"percent": str(round(100 * link.getUsage("direct"), digitsPrecision)) + "%", "type": "direct", "value": str(link.computeLoad("direct"))})
        SubElement(edgeXML, "usage", {"percent": str(round(100 * link.getUsage("inverse"), digitsPrecision)) + "%", "type": "inverse", "value": str(link.computeLoad("inverse"))})
    
    
    indent(resultsXML)
    tree = ElementTree(resultsXML)
    
    tree.write(name, xml_declaration=True, encoding='utf-8', method="xml")
    
    return resultsXML
    
def parseXML(XMLPath):
    """ Parses an XML file with the appropriat format for the exercice and creates its data structure, returning a network object """
    tree = parse(XMLPath)
    root = tree.getroot()
    
    for child in root:
        
        # Parse the network first
        if child.tag == "network":
            printIfVerbose("Building a " + child.tag + " called " + child.attrib["name"])
            name = ""
            overhead = 0
            transmission_capacity = 0
            x_type = ""
            for attributeName in child.attrib:
                if attributeName == "name":
                    name = child.attrib[attributeName]
                elif attributeName == "overhead":
                    overhead = 8* interpretQuantity(child.attrib[attributeName])
                elif attributeName == "transmission-capacity":
                    transmission_capacity = interpretQuantity(child.attrib[attributeName])
                elif attributeName == "x-type":
                    x_type = child.attrib[attributeName]
            net = Classes.Network(name, overhead, transmission_capacity, x_type)
            break
        else:
            print("ERROR: Could not find a network node!")
    
    # All attribute assignation referring to network nodes are first done as strings, and then
    # the corresponding nodes are assigned AFTER we've ensured all the nodes have been created.
    for child in root:
        printIfVerbose("Building a " + child.tag + " called " + child.attrib["name"])
        if child.tag == "station":
            name = ""
            transmission_capacity = 0
            x = 0
            y = 0
            for attributeName in child.attrib:
                if attributeName == "name":
                    name = child.attrib[attributeName]
                elif attributeName == "transmission-capacity":
                    transmission_capacity = interpretQuantity(child.attrib[attributeName])
                elif attributeName == "x":
                    x = child.attrib[attributeName]
                elif attributeName == "y":
                    y = child.attrib[attributeName]
            
            newStation = Classes.Station(name, transmission_capacity, x, y)
            newStation.setNetwork(net)
            net.stations[name] = newStation
        
        elif child.tag == "switch":
            name = ""
            transmission_capacity = 0
            x = 0
            y = 0
            redundancy = "Unspecified"
            for attributeName in child.attrib:
                if attributeName == "name":
                    name = child.attrib[attributeName]
                elif attributeName == "transmission-capacity":
                    transmission_capacity = interpretQuantity(child.attrib[attributeName])
                elif attributeName == "x":
                    x = child.attrib[attributeName]
                elif attributeName == "y":
                    y = child.attrib[attributeName]
                elif attributeName == "redundancy":
                    redundancy = child.attrib[attributeName]
           
            newSwitch = Classes.Switch(name, transmission_capacity, x, y)
            if redundancy != "Unspecified":
                newSwitch.setRedundancy(redundancy)
            newSwitch.setNetwork(net)
            net.switches[name] = newSwitch
        
        elif child.tag == "link":
            name = ""
            start = ""
            startPort = ""
            end = ""
            endPort = ""
            transmission_capacity = 0
            for attributeName in child.attrib:
                if attributeName == "name":
                    name = child.attrib[attributeName]
                elif attributeName == "from":
                    start = child.attrib[attributeName]
                elif attributeName == "fromPort":
                    startPort = child.attrib[attributeName]
                elif attributeName == "to":
                    end = child.attrib[attributeName]
                elif attributeName == "toPort":
                    endPort = child.attrib[attributeName]
                elif attributeName == "transmission-capacity":
                    transmission_capacity = interpretQuantity(child.attrib[attributeName])
            
            newLink = Classes.Link(name, start, startPort, end, endPort, transmission_capacity)
            newLink.setNetwork(net)
            net.links[name] = newLink
        
        elif child.tag == "flow":
            deadline = 0
            jitter = 0
            max_payload = 0
            name = ""
            period = 0
            priority = 0
            source = ""
            redundancy = "MAIN"
            for attributeName in child.attrib:
                if attributeName == "deadline":
                    deadline = interpretQuantity(child.attrib[attributeName])
                elif attributeName == "jitter":
                    jitter = interpretQuantity(child.attrib[attributeName])
                elif attributeName == "max-payload":
                    max_payload = 8*interpretQuantity(child.attrib[attributeName])
                elif attributeName == "name":
                    name = child.attrib[attributeName]
                elif attributeName == "period":
                    period = 1e-3*interpretQuantity(child.attrib[attributeName])
                elif attributeName == "priority":
                    priorityString = child.attrib[attributeName]
                    if priorityString == "Low":
                        priority = 0
                    elif priorityString == "High":
                        priority = 1
                    else:
                        print("ERROR: The priority string for {0} is not admitted!".format(name))
                elif attributeName == "transmission-capacity":
                    transmission_capacity = interpretQuantity(child.attrib[attributeName])
                elif attributeName == "source":
                    source = child.attrib[attributeName]
                    #Find the end system and add it to the targets list
            newFlow = Classes.Flow(deadline, jitter, max_payload, name, period, priority, source)
            newFlow.setNetwork(net)
            net.flows[name] = newFlow
            
            
            for targetElement in child:
                # Gather attributes
                targetStationName = targetElement.attrib["name"]
                sourceStationName = child.attrib["source"]
                try:
                    redundancy = child.attrib["redundancy"]
                except:
                    redundancy = "Unspecified"
                # Create target
                target = Classes.Target(targetStationName, sourceStationName, newFlow)
                # Assign redundancy
                if redundancy != "Unspecified":
                    target.setRedundancy(redundancy)
                
                # Add target to flow targets
                newFlow.targets[targetStationName] = target
                
                # Build target's path
                for pathComponent in targetElement:
                    pathNodeName = pathComponent.attrib["node"]
                    target.path.append(pathNodeName)
                    
                target.setNetwork(net)
                
    
    # Nodes have been asigned as names, correct to objects
    for link in net.links.values():
        link.start = net.getNode(link.start)
        link.end = net.getNode(link.end)
    
    for flow in net.flows.values():
        source = net.getNode(flow.source)
        flow.source = source
        for target in flow.targets.values():
            target.target = net.getNode(target.target)
            target.source = net.getNode(target.source) 
            for i in range(len(target.path)):
                target.path[i] = net.getNode(target.path[i])
            printIfVerbose("Path for target " + target.name + " is " + str([str(s) for s in target.path]))
            if not target.hasPath():
                print("ERROR: " + str(target) + " path was not built correctly!")
                
    # Initializes some variables
    net.initializeNodes()
    
    printIfVerbose("The network has been fully built!")
    
    return net
