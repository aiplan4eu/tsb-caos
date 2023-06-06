from problem import CAOSProblem

#Generate new problem instance
p = CAOSProblem()

#Create New Instance
#p.CreateRandomInstance(True)

#Load Instance
p.ImportState("test_state.json")

#Report Instance
p.Report()

while (True):
    ctr_list = p.GetActiveContracts()
    contract = ctr_list[0]
    p.GenerateScenarios(contract)
    p.SolveScenarios()
    
    #p.GenerateActions() #TODO: IMPLEMENT
    
    #action = p.AnalyzeState(contract)
    #£p.ApplyAction(action)
    #p.Report()

