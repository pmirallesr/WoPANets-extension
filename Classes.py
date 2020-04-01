from Utils import createQuantity, printIfVerbose, computeTheorem1Delay, computeTheorem1Backlog, ceilWithUnit

class AffineCurve():
    """ Represents an affice service or arrival curve """
    #TODO: Implement polynomial representations. Numpy?
    def __init__(self, m, n):
        self.m = m
        self.n = n
    
    def delayBy(self, delay):
        """ Returns y(t+delay) where y(t) was the original curve
        
        Theorem2: If delay introduced by a node is T then the arrival curve of its
        output flux D*(t) is equal to the input arrival curve D(t) delayed by T: D(t+T)
        With affine curves that corresponds to the same slope and a new burst
        b' = b + m x d, where b is the old burst and d is the max delay
        """
        return AffineCurve(self.m, self.n + self.m*delay)
    

    def __add__(self, v):
        if isinstance(v, AffineCurve):
            return AffineCurve(self.m + v.m, self.n + v.n)
        else:
            return AffineCurve(self.m, self.n + v.n)
    def __mul__(self, v):
        return AffineCurve(self.m*v, self.n*v)    
    def __div__(self, v):
        return AffineCurve(self.m/v, self.n/v)
    
    def __str__(self):
        return "y = {0}bps*x + {1}b".format(createQuantity(self.m), createQuantity(self.n))

class Target():
    """ This class represents the target of a data flow """
    def __init__(self, target, source, parentFlow, redundancy = "MAIN"):
        self.target = target
        self.name = target
        self.source = source
        self.redundancy = redundancy
        self.parentFlow = parentFlow
        self.path = []

    def setRedundancy(self, redundancy):
        self.redundancy = redundancy
        
    def setNetwork(self, network):
        self.network = network
        
    def hasPath(self):
        """ Returns true if the target's path has been correctly created within the network, false otherwise """
        intermediateSource = self.source #This variable will store the current source in any given link
        hasPath = True
        
        #Is the path propperly connected i.e. are there links between all intermediate steps?
        for pathElement in self.path: 
            for link in self.network.links.values():
                # Check if our current source and destination are connected.
                if link.connectsSystems(intermediateSource, pathElement):
                    #printIfVerbose(str(link) + " connects the systems")
                    link.flows[self.parentFlow.name] = self.parentFlow #Assign myself to the link's flows
                    hasPath = True
                    break
                else:
                    hasPath = False
            # If the current source and destination are not connected, the path is not propperly connected
            if not hasPath:
                return False
            # If they are connected, set the old destination as new source and check if its connected to the next destination
            intermediateSource = pathElement
        
        # The path is propperly connected. Does it lead to out target?
        if self.path[-1] == self.target:
            return True
        else:
            return False    

    def isDirectWith(self, nodeA, nodeB):
        """ Returns true if nodeB comes after nodeA in the target's path, false otherwise """
        direct = None
        
        if nodeA == nodeB:
            print("ERROR: Tried to see if {0} was direct with respect to identical nodes {1}".format(self, nodeA))
            raise ValueError
        
        completePath = [self.source] + self.path # XML path does not contain the source
        
        for node in completePath:
            if node == nodeA:
                if direct == False:
                    return False
                elif direct == True:
                    print("ERROR: This is a circular path that does not contain node B?")
                    raise ValueError # Circular path that does not contain nodeB?
                else:
                    direct = True
            elif node == nodeB:
                if direct == True:
                    return True
                elif direct == False:
                    print("ERROR: This is a circular path that does not contain node B?")
                    raise ValueError # Circular path that does not contain nodeA?
                else:
                    direct = False
        if direct == True:
            print("ERROR: {0} does not contain node B: {1}".format(self, nodeB))
            printIfVerbose([str(k) for k in completePath])
        elif direct == False:
            print("ERROR: {0} does not contain node A: {1}".format(self, nodeA))
            printIfVerbose([str(k) for k in completePath])
        else:
            print("ERROR: {0} does not contain neither {1} nor {2}".format(self, nodeA, nodeB))
        raise ValueError 
    
    def computeEndToEndDelay(self):
        """ Computes the end to end delay of the target's parent flow through the target's path """
        
        destinationNode = self.path[-1]
        priorToDestNode = self.findPreviousNode(destinationNode)
        delay = priorToDestNode.computeTargetArrivalAffine(self)["delay"]
#         return ceilWithUnit(delay, "u")
        return delay
    
    def findPreviousNode(self, node):
        """ Returns the node previous to a given node, None if the node has no previous node or is not in path """
        prevNode = None
        for i in range(len(self.path)):
            if self.path[i] == node:
                if i == 0:
                    prevNode = self.source
                else:
                    prevNode = self.path[i-1]
        if prevNode is None:
            print("ERROR: Tried to find the precedent of {0} in {1}'s path yet found none!".format(node, self))
            raise Exception
        return prevNode
    
    
    def findNextNode(self, node):
        """ Find the node after the given node, none if the node is not in the path or is the last one"""
        endNode = None
        if node == self.source:
            endNode = self.path[0]
        for i in range(len(self.path) - 1):
            if self.path[i] == node:
                endNode = self.path[i+1]
        if endNode is None:
            print("ERROR: Tried to find the subsequent of {0} in {1}'s path yet found none!".format(node, self))
            raise Exception
        return endNode
    
    def findOutgoingLink(self, node):
        """ Finds the link outgoing from the given node that carries this target's parent flow.
        
        Returns none if node is not within the path or is the path's final node.
        """
        endNode = self.findNextNode(node)
        return self.network.getConnectingLink(node, endNode)
        
        
    
    def __str__(self):
        return "Target to " + str(self.target.name) + " from " + str(self.source.name)
        

class Node():
    """ This class is a superclass of stations and switches of a network"""
    def __init__(self, name, service_policy, transmission_capacity, x, y, tech_latency = 0):
        self.name = name
        self.service_policy = service_policy
        self.transmission_capacity = transmission_capacity
        self.x = x
        self.y = y
        self.tech_latency = tech_latency
        self.flows = {}
        
    
    def setNetwork(self, network):
        self.network = network
        
    def initAllDicts(self):
        """ Some dictionaries can only be created when the network is fully initialised """
        self.initArrivalDict()
        self.initDelayDict()
        self.initBacklogDict()
    
    def initDelayDict(self):
        self.delayBoundsPerLink = {}
        for link in self.getLinks():
            self.delayBoundsPerLink[link] = -1
    def initArrivalDict(self):
        self.totalArrivalsPerLink = {}
        for link in self.getLinks():
            self.totalArrivalsPerLink[link] = AffineCurve(-1, 0)
            
    def initBacklogDict(self):
        self.backlogsPerLink = {}
        for link in self.getLinks():
            self.backlogsPerLink[link] = -1
            
    def computeServiceAffine(self):
        return AffineCurve(self.transmission_capacity, -self.transmission_capacity*self.tech_latency)
    
    def getWorstCaseService(self, target):
        """ Modifies node's service curve to account for worst-case multiplexing scenario for given flow """
        
        service = self.computeServiceAffine() # Get the unaltered service curve
        link = target.findOutgoingLink(self) # Find out the outgoing link of this traffic
        flows = link.flows.values() # Recover all flows outgoing on this link
        
        # First, calculate the arrival curves for all passing flows excluding the given one
        # Next calculate the worst-case service curve by assuming that
        # 1 - All higher priority flows are incoming at their maximum rates and before you.
        # 2 - All flows have their worst case bursts waiting in queue by the time you arrive, and
        # you must wait for the switch to treat more prioritary bursts and messages already being treated.
        maximumMsgSize = 0
        for flow in flows:
            # For higher priority flows
            if flow.priority > target.parentFlow.priority:
                # Find the target corresponding to this flow that passes by this node
                otherTarget = flow.findTargetPassingThroughNode(self)
                # Find the node previous to this one in the path to said target
                otherPrevious = otherTarget.findPreviousNode(self) 
                # Find the arrival curve at the output of the previous node by recursively calling this function
                otherArrival = otherPrevious.computeTargetArrivalAffine(otherTarget)["outputArrival"]
                # Modify service curve
                service.m -= otherArrival.m
                service.n -= otherArrival.n
            # For other flows when we're looking at a switch, and it implements store and forward
            if flow != target.parentFlow and isinstance(self, Switch):
                if self.switching_technique == "STORE_AND_FORWARD":
                    maximumMsgSize = max(flow.maxMessageSize, maximumMsgSize)
        
        # The max packet is sent at max speed so it doesn't impact the service in a 1:1 fashion
        service.n -= maximumMsgSize/self.transmission_capacity*service.m
        
        return service
    
    def computeTargetArrivalAffine(self, target):
        """ Computes target's output arrival affine curve, total delay up to this point, backlog, and total arrival curves incoming to this outgoing port of the node
        
        Relies on theorem 1 calculation to find the delay given a known arrival curve and a know service curve,
        and on theorem 2 to calculate the arrival curve at the output of a node knowing the maximum delay through
        that node and the input arrival curve.
        
        This calculation is highly recursive! It will call itself on all nodes within the paths of all flows using
        the same output link of this node as the one used by the given target.
        """
        
        printIfVerbose("Calculating affine output arrival of {0} for flux {1}\n".format(str(self), str(target)))
                
        totalArrival = AffineCurve(0, 0)
        tempArrival = AffineCurve(0, 0)
        totalDelay = 0 # Stores the flow's delay bound up until this node
        
        link = target.findOutgoingLink(self) # Find out the outgoing link of this traffic
        linkDelayCalculated = self.delayBoundsPerLink[link] >= 0
        flows = link.getFlowsInSameDirection(target)
        
        # If source, 
        if self == target.source:
            for flow in flows.values():
                tempArrival = flow.computeArrivalAffine()
                if flow == target.parentFlow:
                    arrival = tempArrival
                totalArrival += tempArrival 
        # Otherwise as per theorem 2, we can obtain it by computing the output affine of the intervening nodes
        else:           
            # Calculate the output arrival by recursively calling this function on said node
            for flow in flows.values():
                currentTarget = flow.findTargetPassingThroughNode(self)
                previousNode = currentTarget.findPreviousNode(self)
                if not linkDelayCalculated or flow == target.parentFlow:
                    tempOutput = previousNode.computeTargetArrivalAffine(currentTarget)
                    tempArrival = tempOutput["outputArrival"]
                    tempDelay = tempOutput["delay"]
                    if flow == target.parentFlow:
                        totalDelay += tempDelay # Add the delay up to this point
                        arrival = tempArrival
                    totalArrival += tempArrival
        
        printIfVerbose("Looking at node " + str(self.name))
        printIfVerbose("The input arrival curve to {0} for {1} is {2}".format(self, target.parentFlow, arrival))
        
        # Now we need to factor in how multiplexing flows affects the service curve of the node
        service = self.getWorstCaseService(target)      
        printIfVerbose("The adjusted service curve of {0} is {1}".format(link,service))
        printIfVerbose("The aggregate arrival curve to {0} for {1} is {2}".format(self, link, totalArrival))
        
        backlog = computeTheorem1Backlog(totalArrival, service)
        printIfVerbose("Backlog for {0} is {1}".format(self, backlog))
        
        # Next, calculate the incurred delay in this node given the new arrival and service curves 
        if not linkDelayCalculated:
            delay = computeTheorem1Delay(totalArrival, service)
            # Store values for future reference
            self.delayBoundsPerLink[link] = delay
            self.totalArrivalsPerLink[link] = totalArrival
            self.backlogsPerLink[link] = backlog
        else:
            delay = self.delayBoundsPerLink[link]
            totalArrival = self.totalArrivalsPerLink[link]
            backlog = self.backlogsPerLink[link] 
        totalDelay += delay
        printIfVerbose("Delay at node {0} is {1}s".format(self.name, createQuantity(delay)))
        
        outputArrival = arrival.delayBy(delay)
        printIfVerbose("The output arrival curve of {0} for {1} is {2} \n".format(self, target.parentFlow, outputArrival))
        
        return {"outputArrival": outputArrival, "delay": totalDelay, "totalArrival": totalArrival, "backlog": backlog}
    
    def getLinks(self):
        """ Returns a list containing all Links connected to self """
        connectingLinks = []
        for link in self.network.links.values():
            if link.start == self or link.end == self:
                connectingLinks.append(link)
        return connectingLinks
    
    def getBacklog(self, link):
        """ Returns the backlog on flows outgoing on this link """
        if self.backlogsPerLink[link] >= 0:
            return self.backlogsPerLink[link]
        else:
            anOutgoingTarget = self.getTargetLeavingThroughLink(link)
            if anOutgoingTarget is None:
                # No links outgoing through this link, so no backlog either
                return 0
            else:
                backlog = self.computeTargetArrivalAffine(anOutgoingTarget)["backlog"]
                return backlog
    
    def getTotalBacklog(self):
        totalBacklog = 0
        for link in self.getLinks():
            totalBacklog += self.getBacklog(link)
        return totalBacklog
       
    def getDelay(self, link):
        if self.delayBoundsPerLink[link] >= 0:
            return self.delayBoundsPerLink[link]
        else:
            anOutgoingTarget = self.getTargetLeavingThroughLink(link)
            if anOutgoingTarget is None:
                # No links outgoing through this link, so no delay either
                return 0
            else:
                delay = self.computeTargetArrivalAffine(anOutgoingTarget)["delay"]

                return delay
               
    def getTargetLeavingThroughLink(self, link):
        """ Returns a target leaving through the given link, None if there aren't any """
        # First we must find a target that goes out of the node through the given link to feed to other functions
        foundTarget = False
        anOutgoingTarget = None
        for flow in link.flows.values():
            for target in flow.targets.values():
                if target.findOutgoingLink(self) == link:
                    anOutgoingTarget = target # We just want one such target
                    foundTarget = True
                    break
            if foundTarget:
                break
        return anOutgoingTarget
        
    def __str__(self):
        return self.name
        
    
        
class Station(Node):
    """ This class represents a station in the network """
    def __init__(self, name, transmission_capacity, x, y, service_policy = "FIRST_IN_FIRST_OUT", tech_latency = 0):
        super().__init__(name, service_policy, transmission_capacity, x, y, tech_latency)
        
class Switch(Node):
    """ This class represents a switch in the network"""
    def __init__(self, name, transmission_capacity, x, y, switching_technique = "CUT_THROUGH", service_policy = "FIRST_IN_FIRST_OUT", tech_latency = 0, buffer_size = 65536):
        super().__init__(name, service_policy, transmission_capacity, x, y, tech_latency)
        self.switching_technique = switching_technique
        self.buffer = buffer_size
    
    def setRedundancy(self, redundancy):
        self.redundancy = redundancy
     
    # TODO: Implement getPorts, implement getBacklog(port), implement getTotalBacklog
    
class Link():
    """ This class represents a link in the network"""
    def __init__(self, name, start, startPort, end, endPort, transmission_capacity):
        self.name = name
        self.start = start
        self.startPort = startPort
        self.end = end
        self.endPort = endPort
        self.transmission_capacity = transmission_capacity
        self.flows = {}
    
    def setNetwork(self, network):
        self.network = network
        
    def connectsSystems(self, systemA, systemB):
        """ Returns true if the link connects system A with system B, or false otherwise """
        if self.start == systemA:
            if self.end == systemB:
                return True
        if self.end == systemA:
            if self.start == systemB:
                return True
        else:
            return False
    
    def findFlowTargetsPassingThroughLink(self, flow):
        """ Returns an array of targets belonging to flow that pass through the link"""
        targets = []
        for target in flow.targets.values():
            completePath = [target.source] + target.path
            if self.start in completePath and self.end in completePath:
                targets.append(target)
        return targets
    
    def getFlowsInSameDirection(self, target):
        """ Returns a dictionary containing only flows traversing the link in the sense of target"""
        
        sameDirFlows = {}
        
        for flow in self.flows.values():
            otherTargets = self.findFlowTargetsPassingThroughLink(flow)
            for otherTarget in otherTargets:
                if self.sameDirection(target, otherTarget):
                    sameDirFlows[flow.name] = flow
        return sameDirFlows
    
    def sameDirection(self, target, otherTarget):
        """ Returns whether the two targets are flowing in the same direction through link or not"""
        #print(self)
        sameDirection = target.isDirectWith(self.start, self.end) == otherTarget.isDirectWith(self.start, self.end)
        return sameDirection
    
    def computeLoad(self, mode):
        """Computes the total flow across this link. Assumes that flows have been assigned to the link previously. That is done by Target.hasPath()"""
        result = 0
        if self.network is None:
            raise Exception
        for flow in self.flows.values():
            for target in flow.targets.values():
                completePath = [target.source] + target.path # Including source
                if self.start in completePath and self.end in completePath:
                    if mode == "direct" and target.isDirectWith(self.start, self.end):
                        result += flow.maxMessageSize/flow.period
                    elif mode == "inverse" and not target.isDirectWith(self.start, self.end):
                        result += flow.maxMessageSize/flow.period
                    elif mode != "direct" and mode != "inverse":
                        raise ValueError
                    else:
                        continue
#                         print("ERROR: We should never enter this section. Arguments {0}, {1}".format(target.isDirectWith(self.start, self.end), mode))
        return result
    
    def getPort(self, node):
        """ Returns the port through which the link is connected to node, None if none exists """
        if self.start == node:
            return self.startPort
        elif self.end == node:
            return self.endPort
        else:
            return None
    def getUsage(self, mode):
        return self.computeLoad(mode)/self.transmission_capacity
        
    def __str__(self):
        return "Link {0} between {1}, {2} and {3}, {4}".format(self.name, str(self.start), str(self.startPort), str(self.end), str(self.endPort))
        
class Flow():
    """ This class represents a data flow in the network"""
    def __init__(self, deadline, jitter, max_payload, name, period, priority, source, min_payload = 0):
        self.deadline = deadline
        self.jitter = jitter
        self.max_payload = max_payload
        self.min_payload = min_payload
        self.name = name
        self.period = period
        self.priority = priority
        self.source = source
        self.targets = {}
        if jitter > period:
            print("ERROR: Jitter is larger than period for {0}! Don't you think you can do better mate?".format(self.name))
    
    def setNetwork(self, network):
        self.network = network
        self.maxMessageSize = self.max_payload + self.network.overhead
        
    def computeArrivalAffine(self, BE = True):
        """ return an (m,n) tuple where m is the slope and n the bias of the affine function 
        
        The affine function that is an upper bound to the flow's arrival rates, m = maxPayload/period. n = maxPayload - maxPayload^2/sourceCapacity/period
        """
        m = self.maxMessageSize/(self.period - self.jitter)
        if not BE:
            n1 = self.maxMessageSize
            n2 = -self.maxMessageSize**2/(self.source.transmission_capacity*self.period)
            n = n1+n2
        else:
            n1 = self.maxMessageSize
            n = n1
            
        return AffineCurve(m, n)
    
    def findTargetPassingThroughNode(self, node):
        """ Returns the target whose path passes through node, raises an exception if no such path exists """
        for target in self.targets.values():
            for otherNode in target.path:
                if otherNode == node:
                    return target
        print("ERROR: Tried to find a target of {0} passing through {0} but couldn't find any".format(self, node))
        raise Exception
    
    def __str__(self):
        return "Flow : " + str(self.name) + " with destinations: " + str([str(s) for s in self.targets])

class Network():
    """ This class represents the network being studied """
    def __init__(self, name, overhead, transmission_capcacity, x_type, shortest_path_policy = "DJIKSTRA", technology = "AFDX"):
        self.name = name
        self.overhead = overhead
        self.shortest_path_policy = shortest_path_policy
        self.technology = technology
        self.transmission_capacity = transmission_capcacity
        self.x_type = x_type
        self.stations = {}
        self.switches = {}
        self.links = {}
        self.flows = {}
    
    def initializeNodes(self):
        for station in self.stations.values():
            station.initAllDicts()
        for switch in self.switches.values():
            switch.initAllDicts()
    
    def getNode(self, nodeName):
        """ Returns the station or switch with name = nodeName, raises a KeyError if none exists """
        try:
            pathNode = self.stations[nodeName]
        except:
            try:
                pathNode = self.switches[nodeName]
            except:
                print("ERROR: " + nodeName + " is not a valid switch or station!")
                raise KeyError
        return pathNode
    
    def getConnectingLink(self, nodeA, nodeB):
        """ Gets the link connecting two given nodes, None if they are not connected """
        for link in self.links.values():
            if link.connectsSystems(nodeA, nodeB):
                return link
        return None
    
    def computeLoads(self):
        """ Computes the load of each link in the target net """
        loads = {}
        for link in self.links.values():
            loads[str(link)] = str(createQuantity(link.computeLoad("direct"))) + "b/s, direct. " + str(createQuantity(link.computeLoad("inverse"))) + "b/s, inverse."
            printIfVerbose(str(link) + " carries " + loads[str(link)] + " over the flows: " + str([str(s) for s in link.flows]))
        return loads
    
    def isStable(self):
        """ returns True if the network is stable, or False otherwise 
        
        A network is defined as stable if for all of its switches and stations
        the sum of the arrival curves is less than the capacity of the switch
        or station
        """
        def stabilityPrint(thing, arrival):
            printIfVerbose("{0} has a transmission capacity {1}b/s and an arrival curve {2}b/s".format(thing, createQuantity(thing.transmission_capacity), createQuantity(arrival)))
        
        stable = True
        arrival = 0
        
        # Verify that all links are capable of processing arrivals. We take advantage
        # of the fact that flows are assigned to the links they traverse by Link.hasPath()
        # upon network creation
        for link in self.links.values():
            for flow in link.flows.values():
                arrival += flow.computeArrivalAffine().m
            
            stabilityPrint(link, arrival) 
            # If the arrival curve exceeds the transmission capacity, the network is unstable
            if arrival > link.transmission_capacity:
                stable = False
                print("{0} is not stable!".format(link)) 
            arrival = 0 # Reset arrival accumulator for the next station
        
        
        return stable
                                
                    
        
    
    def __str__(self):
        result = "Network: " + str(self.name) + " working on: " + str(self.technology) + ", " + str(self.shortest_path_policy) + ", " + str(self.x_type) + ", containing: "
        for node in self.stations:
            result += "\n \t " + str(node)
        for node in self.switches:
            result += "\n \t " + str(node)
        for node in self.links:
            result += "\n \t " + str(node)
        for node in self.flows:
            result += "\n \t " + str(node)
        return result