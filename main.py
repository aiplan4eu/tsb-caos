from common import CAOSProblem
from scenario_generator import *
import json


#Load Instance
f = open("test_instance.json")
instance = json.loads(f.read())
f.close()

p = CAOSProblem()

#Load Instance
p.LoadInstance(instance)
p.Report()

#Solve Problem
p.Solve()


