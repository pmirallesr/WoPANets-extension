verbose = False # Controls printIfVerbose function
checkStability = False # Controls whether delay and background calculations take into account the link's stability

# Don't touch these parameters
SIunits = {"G" : 1e9, "M": 1e6, "": 1, "m": 1e-3, "µ": 1e-6}
# SIUnits ordered by decreasing size
orderedSI = {k: v for k, v in sorted(SIunits.items(), key=lambda item: item[1], reverse=True)}

def ceilWithUnit(amount, selectUnit = None):
    if selectUnit == "u":
        selectUnit = "µ"
    if selectUnit is None:
        for unit in orderedSI:
            if abs(amount) >= orderedSI[unit]:
                    amount = amount/orderedSI[unit]
                    amount = amount - amount%1 + 1  
                    amount = amount*orderedSI[unit]
    else:
        if selectUnit in orderedSI:
            amount = amount/orderedSI[selectUnit]
            amount = amount - amount%1 + 1 
            amount = amount*orderedSI[selectUnit]
    return amount

def printIfVerbose(printString):
    """ Useful to control the program's verbosity and switch between nominal and debugging modes """
    if verbose:
        print(printString)

def interpretQuantity(quantity):
    """ Transforms expressions in M, G, m, or µ units to their numerical counterparts
    
    It takes as input a string ###Yxxx such as 100Mbits and outputs the corresponding number
    wihtout units. ### is a number, Y is a character to denote their SI meanings, and
    xxx is an arbitrary string, typically denoting the actual unit such as bits or s.
    
    Only characters within SIUnits are processed correctly, all other characters are ignored.
    xxx strings including characters from the SIUnits system can lead to uncontrolled behaviour.
    """
    a = float(''.join(ele for ele in quantity if ele.isdigit() or ele == '.'))
    for unit in SIunits:
        if unit in quantity:
            return a*SIunits[unit]
    return a

def createQuantity(amount, digits = 2, omitUnit = False, selectUnit = None):
    """ Reverse interpretQuantity 
    Omit unit to omit the unit in the final string, select unit = a given prefix to transform to that prefix,
    otherwise transforms to the closest prefix
    """
    template = "{0:." + str(digits) + "f}"
    if amount == float("inf"):
        return str(amount) + " "
    # Accepts u as µ
    if selectUnit == "u":
        selectUnit = "µ"
    if selectUnit is None:
        for unit in orderedSI:
            if abs(amount) >= orderedSI[unit]:
                if omitUnit:
                    return template.format(amount/orderedSI[unit])
                else:
                    return template.format(amount/orderedSI[unit]) + " " + unit
        return amount
    if selectUnit in SIunits.keys():
        if omitUnit:
            return template.format(amount/(SIunits[selectUnit]))
        else:
            return template.format(amount/(SIunits[selectUnit])) + " " + selectUnit
    else:
        raise ValueError
        
        

def computeTheorem1Delay(arrival, service):
    """ Calculates the upper bound on the delay introduced by a node on a given flux
    
    Relies on affine curve representation (y = mx+n) of the arrival and service curves.
    Applies Theorem 1: End2End delay bound = max(Delay(q)) with Delay(q) <= ts - td 
    with td and ts defined as the times such that arrival(td) = service(ts) = q.
    
    Returns infinity if no bounded delay exists for the given curves.
    """
    
    
    # Verify that this is not an unstable situation
    if service.m <= arrival.m and checkStability:
        print("ERROR: Arrival rate is {0}bps and service rate is {1}bps, \
        this situation is not stable and the delay is not bounded.".format(createQuantity(arrival.m), createQuantity(service.m)))
        return float("inf")
    
    # Find the largest burst, which occurs at t = 0 with stable behaviour and for affine curves  
    b = arrival.n - service.n
    
    # If there is no burst, there's no delay. Else delay = burst/speed
    if b <= 0:
        return 0
    else:
        return ceilWithUnit(b/service.m)
#         return b/service.m

def computeTheorem1Backlog(arrival, service):
    """ Calculates the upper bound on the delay introduced by a node on a given flux
    
    Relies on affine curve representation (y = mx+n) of the arrival and service curves.
    Applies Theorem 1: End2End delay bound = max(Delay(q)) with Delay(q) <= ts - td 
    with td and ts defined as the times such that arrival(td) = service(ts) = q
    """
    
    
    # Verify that this is not an unstable situation
    if service.m <= arrival.m and checkStability:
        print("ERROR: Arrival rate is {0}bps and service rate is {1}bps, \
        this situation is not stable and the backlog is not bounded.".format(createQuantity(arrival.m), createQuantity(service.m)))
        return float("inf")
    
    # Maximum backlog is the max arrival burst plus the accumulated backlog while the node handles other issues
    timeMaxBacklog = -service.n/service.m
    if timeMaxBacklog < 0: 
        timeMaxBacklog = 0
    
    
    maxBacklog =  timeMaxBacklog*arrival.m + arrival.n
    
    return maxBacklog    

def affineCurvePrint(element, curve):
    print("{0} has affine curve {1}".format(element, curve))