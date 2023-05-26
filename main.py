from problem import CAOSProblem
#from scenario_generator import *
import json


#Generate new problem instance
p = CAOSProblem()

#Create New Instance
#p.CreateRandomInstance(True)

#Load Instance
p.LoadInstance("gen_data.json")

#Report Instance
p.Report()

#p.UpdateContract(p.contracts[2], 0, 4.0, 3)
#p.UpdateContract(p.contracts[11], 0, 1.0, 1)
#p.UpdateContract(p.contracts[19], 0, 1.0, 1)
#p.UpdateContract(p.contracts[20], 0, 1.0, 1)
#p.UpdateContract(p.contracts[26], 0, 1.0, 1)

p.Report()

#Get Actions
action = p.AnalyzeState()

#Apply Action
p.ApplyAction(action)
p.Report()

#Progress to next contract
action = p.AnalyzeState()

#Apply New action
p.ApplyAction(action)
p.Report()






