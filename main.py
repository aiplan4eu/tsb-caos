from problem import CAOSProblem
#from scenario_generator import *
import json

#Load Instance
f = open("gen_data.json")
instance = json.loads(f.read())
f.close()

p = CAOSProblem()

#Load Instance
p.LoadInstance(instance)
p.Report()

p.UpdateContract(p.contracts[2], 0, 4.0, 3)
#p.UpdateContract(p.contracts[11], 0, 1.0, 1)
#p.UpdateContract(p.contracts[19], 0, 1.0, 1)
#p.UpdateContract(p.contracts[20], 0, 1.0, 1)
#p.UpdateContract(p.contracts[26], 0, 1.0, 1)

p.Report()

#Solve Problem
p.Solve()

p.PostProcess()













