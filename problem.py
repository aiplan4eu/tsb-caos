from scenario_generator import ScenarioGenerator
from plan_evaluator import PlanEvaluator
from planner import Planner
from common import Contract, Client
from matplotlib import pyplot as plt
import json
from multiprocessing.pool import ThreadPool


class CAOSProblem:
    def __init__(self, ):
        self.NumberOfClients = 0
        self.NumberOfPeriods = 0
        self.StartBalance = 0
        self.LoanRate = 0.0
        
        self.Contracts = []
        self.clients = []
        self.clientMap = {}

        self.scenarios = []
        
    def LoadInstance(self, instance):
        self.NumberOfClients = instance["NumberOfClients"]
        self.NumberOfPeriods = instance["NumberOfPeriods"]
        self.StartBalance = instance["StartBalance"]
        self.LoanRate = instance["LoanRate"]
        self.ScenariosPerRate = instance["ScenariosPerRate"]
        self.Rates = instance["Rates"]
        
        #Add Clients
        for c in instance["Clients"]:
            c_data = instance["Clients"][c]
            self.AddCounterParty(c, c_data["a"], c_data["b"], 
                                 c_data["negotiation_preference"], c_data["deferral_openess"])

        #Add Inbound Contracts
        for c in instance["Contracts"]["Inbound"]:
            client = self.clientMap[c["client"]]
            self.AddContract(client, c["period"], c["amount"], 1)

        #Add Outbound Contracts
        for c in instance["Contracts"]["Outbound"]:
            client = self.clientMap[c["client"]]
            self.AddContract(client, c["period"], c["amount"], 2)


    def Report(self):
        print("CounterParties")
        for c in self.clients:
            print(c.name, c.alpha, c.beta)

        print("Contracts")
        for c in self.Contracts:
            print(c.client.name, c.amount, c.period, c.type)
    
    
    def AddCounterParty(self, name, a, b, c, d):
        if (name in self.clients):
            print("Client", name, "exists")
            return

        #Create CounterParty
        c = Client(name, a, b, c, d)
        c.id = len(self.clients)
        self.clients.append(c)
        self.clientMap[name] = c

    def AddContract(self, client, period, amount, typ):
        ctr = Contract(typ, period, amount, client)
        ctr.id = len(self.Contracts)
        ctr.type = typ
        self.Contracts.append(ctr)
    
    def GenerateScenarios(self):
        self.scenarios = ScenarioGenerator.GenerateScenarios(self)
    
    def SolveScenarios(self):
        #At first add all scenarios to a list
        scenario_list = []
        for ctr in self.scenarios:

            for inst in self.scenarios[ctr]:
                #Single installment
                if (inst == 1):
                    for d in self.scenarios[ctr][inst]:
                        for r in self.scenarios[ctr][inst][d]:
                            for s in self.scenarios[ctr][inst][d][r]:
                                scenario_list.append(s)    
                else: #Multi installments
                    for r in self.scenarios[ctr][inst]:
                        for s in self.scenarios[ctr][inst][r]:
                            scenario_list.append(s)

        #Solve Sequentially
        # for s in scenario_list:
        #     self.SolveScenario(s)
        
        #Create thread pool
        print("Solving ", len(scenario_list), "using 4 threads")
        pool = ThreadPool(processes=4)
        pool.map(self.SolveScenario, scenario_list)
        pool.close()
        pool.join()
        print("Threads Completed")
        
    def SolveScenario(self, s):
        #Create Planning Problem from scenario
        p = s.GeneratePlanningProblem()
        #Cache the planning problem solution in the scenario
        try:
            s.solution = Planner.Solve(p)
        except:
            print("ERROR EXECUTING PLAN")
            print(p)
        #print(s.GetWeightedObjective())
    
    def PostProcess(self):
        response = {}
        for client_name in self.scenarios:
            res = PlanEvaluator.EvaluateClient(self.clientMap[client_name], self)
            response[client_name] = res
            self.CreatePlot(res["Policy 1"]["Values"].keys(), res["Policy 1"]["Values"].values(), client_name + "_pol1", "Policy 1")
            self.CreatePlot(res["Policy 2"]["Values"].keys(), res["Policy 2"]["Values"].values(), client_name + "_pol2", "Policy 2")
            self.CreatePlot(res["Policy 3"]["Values"].keys(), res["Policy 3"]["Values"].values(), client_name + "_pol3", "Policy 3")

        f = open("report.txt", "w")
        f.write(json.dumps(response))
        f.close()
    
    
    def CreatePlot(self, keys, values, figname, policy):
        #Create bar plot for client
        f = plt.figure(figsize=(10,5))
        plt.bar(keys, values)
        plt.xlabel("Rates")
        plt.ylabel("Prob")
        plt.title("Rate recommendation for " + policy)
        f.savefig(figname, dpi=600)

    def Solve(self):
        #Generate Scenarios
        self.GenerateScenarios()
        self.SolveScenarios()
        self.PostProcess()

