from Parser import parseXML, produceXML
import Utils
import os

searchFiles = "xml" # Analyze all files in current folder whose name finishes by this string
directory = 'XMLsamples/Inputs'

for filename in os.listdir(directory):
    if filename.endswith(searchFiles):
        # Analyze each matching network, prints the results on top of writing the XML
        print("-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+")
        print(filename)
        print("-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+")
        net = parseXML(directory + "/" + filename)
        if Utils.verbose:
            Utils.printIfVerbose("----------------------------------------")
            print("\n------------LOADS------------------")
            loads = net.computeLoads()
            print(loads)
            print("\n------------STABILITY------------------")
            isStable = net.isStable()
            if isStable:
                print(net.name + " is stable")
            else:
                print(net.name + " is NOT! stable")
                
            print("\n------------AFFINE CURVES------------------")
            print("Flow arrival curves:")
            for flow in net.flows.values():
                arrival = flow.computeArrivalAffine()
                Utils.affineCurvePrint(flow, arrival)
            print("Nodes service curves:")
            for station in net.stations.values():
                service = station.computeServiceAffine()
                Utils.affineCurvePrint(station.name, service)
            for switch in net.switches.values():
                service = switch.computeServiceAffine()
                Utils.affineCurvePrint(flow.name, service)
                
            print("\n---------End to End Delay -----------------")
            for flow in net.flows.values():
                for target in flow.targets.values():
                    print("{0}, target {1} has an end to end delay of {2}s".format(str(target.parentFlow.name), \
                    str(target.path[-1]), Utils.createQuantity(target.computeEndToEndDelay(), digits = 4)))  
            
            print("\n--------- Backlogs -----------------")
            for switch in net.switches.values():
                for outLink in switch.getLinks():
                    delay = str(Utils.createQuantity(switch.getDelay(outLink)))
                    backlog = str(Utils.createQuantity(switch.getBacklog(outLink), digits = 0))   
                    print("{0} leaving from {1} has backlog {2}b and delay {3}s".format(outLink, switch, backlog, delay))
        print("\n---------Producing XML-----------------")
        name = "PythonResults/" + net.name + "_res.xml"
        print("done")
        produceXML(net, name)
        
#         print("\n---------Comparing XML-----------------")
#         compareResults(net.name)
        print("\n\n\n\n")
    else:
        continue