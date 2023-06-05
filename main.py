from problem import CAOSProblem

#Generate new problem instance
p = CAOSProblem()

#Create New Instance
#p.CreateRandomInstance(True)

#Load Instance
p.ImportState("gen_data.json")

#Report Instance
p.Report()

while (True):
    contract = p.ProcessState()
    action = p.AnalyzeState(contract)
    p.ApplyAction(action)
    p.Report()

