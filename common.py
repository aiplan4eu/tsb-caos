from scenario_generator import ScenarioGenerator
from planner import Planner, PlanningProblem

class Client:
    def __init__(self, name, a, b):
        self.id = -1
        self.name = name
        self.alpha = a
        self.beta = b

class Contract:
    def __init__(self, p, a, c):
        self.id = -1
        self.client = c
        self.period = p
        self.amount = a

class CAOSProblem:
    def __init__(self, ):
        self.NumberOfClients = 0
        self.NumberOfPeriods = 0
        self.StartBalance = 0
        
        self.Contracts = {}
        self.InboundContracts = []
        self.OutboundContracts = []
        
        self.clients = []
        self.clientMap = {}

        self.scenarios = []
        
    def LoadInstance(self, instance):
        self.NumberOfClients = instance["NumberOfClients"]
        self.NumberOfPeriods = instance["NumberOfPeriods"]
        self.StartBalance = instance["StartBalance"]

        #Add Clients
        for c in instance["Clients"]:
            c_data = instance["Clients"][c]
            self.AddCounterParty(c, c_data["a"], c_data["b"])

        #Add Inbound Contracts
        for c in instance["Contracts"]["Inbound"]:
            client = self.clientMap[c["client"]]
            self.AddInboundContract(client.name, c["period"], c["amount"])

        #Add Outbound Contracts
        for c in instance["Contracts"]["Outbound"]:
            client = self.clientMap[c["client"]]
            self.AddOutboundContract(client.name, c["period"], c["amount"])


    def Report(self):
        print("CounterParties")
        for c in self.clients:
            print(c.name, c.alpha, c.beta)

        print("Inbound Contracts")
        for c in self.InboundContracts:
            print(c.client.name, c.amount, c.period)
        
        print("Outbound Contracts")
        for c in self.OutboundContracts:
            print(c.client.name, c.amount, c.period)

    
    def AddCounterParty(self, name, a, b):
        if (name in self.clients):
            print("Client", name, "exists")
            return

        #Create CounterParty
        c = Client(name, a, b)
        c.id = len(self.clients)
        self.clients.append(c)
        self.clientMap[name] = c

    
    def AddInboundContract(self, client_name, period, amount):
        if (client_name not in self.clientMap):
            print("Client", client_name, "does not exist")
            return
        
        c = self.clientMap[client_name]

        #Create Contract
        ctr = Contract(period, amount, c)
        ctr.id = len(self.Contracts)
        self.Contracts[ctr.id] = ctr
        self.InboundContracts.append(ctr)


    def AddOutboundContract(self, client_name, period, amount):
        if (client_name not in self.clientMap):
            print("Client", client_name, "does not exist")
            return
        
        c = self.clientMap[client_name]

        #Create Contract
        ctr = Contract(period, amount, c)
        ctr.id = len(self.Contracts)
        self.Contracts[ctr.id] = ctr
        self.OutboundContracts.append(ctr)

    
    def GenerateScenarios(self):
        self.scenarios = ScenarioGenerator.GenerateScenarios(self, 10)
    
    def SolveScenarios(self):
        for client_name in self.scenarios:
            for rate in self.scenarios[client_name]:
                for scn in self.scenarios[client_name][rate]:
                    self.SolveScenario(scn)

    def SolveScenario(self, s):
        #Create Planning Problem from scenario
        p = s.GeneratePlanningProblem()
        Planner.Solve(p)
        

    def SolvePlanningProblem(self, p):
        pass

    def PostProcess(self):
        pass

    def EvaluateScenario(self, s):
        pass


    def Solve(self):
        #Generate Scenarios
        self.GenerateScenarios()
        self.SolveScenarios()

    