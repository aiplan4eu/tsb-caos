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

#Solve Problem
p.Solve()

p.PostProcess()













