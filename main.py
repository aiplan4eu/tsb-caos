from problem import CAOSProblem
#from scenario_generator import *
import utilities
import json

#Load Instance
f = open("test_instance.json")
instance = json.loads(f.read())
f.close()

p = CAOSProblem()

#Load Instance
p.LoadInstance(instance)
p.Report()

#Finalize contract 0
contract = p.contracts[0]
p.UpdateContract(contract, 1, 2.0, 1)

p.Report()

#Solve Problem
p.Solve()













