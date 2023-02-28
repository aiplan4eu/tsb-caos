from planner import PlanningProblem
import random


class Scenario:
    def __init__(self, p):
        self.problem = p
        self.rates = {}
        for c in p.clients:
            self.rates[c.name] = 1.0

    def AddRate(self, client_name, rate):
        if (client_name not in self.rates):
            print("Client does not exist")
            return
        self.rates[client_name] = rate

    def GeneratePlanningProblem(self):
        p = PlanningProblem()
        p.StartBalance = self.problem.StartBalance
        p.NumberOfClients = self.problem.NumberOfClients
        p.NumberOfPeriods = self.problem.NumberOfPeriods
        
        #Add Inbound Contracts
        for c in self.problem.InboundContracts:
            p.InboundContracts.append({
                                        'id' : c.id, 
                                        'period': c.period, 
                                        'amount': c.amount,
                                        'rate' : self.rates[c.client.name]
                                    })
            
        #Add Outbound Contracts
        for c in self.problem.OutboundContracts:
            p.OutboundContracts.append({
                                        'id' : c.id, 
                                        'period': c.period, 
                                        'amount': c.amount,
                                        'rate' : self.rates[c.client.name]
                                    })
        
        return p


class ScenarioGenerator:
    def __init__():
        pass

    @staticmethod
    def FindAcceptableRate(client):
        while(True):
            #Choose a rate at random
            pred_rate = random.randint(1, 100) / 100.0

            #Calculate the acceptance probability of the rate
            rate_val = client.beta / pow(pred_rate, client.alpha)
            
            #See if we can accept this rate with another experiment
            chance = random.randint(1, 100) / 100.0
            
            if (chance < rate_val):
                return 1.0 + pred_rate
    
    
    @staticmethod
    def GenerateScenarios(p, per_rate_scenarios):
        scenarios = {}
        
        for client in p.clients:
            scenarios[client.name] = {}

            #Iterate in interest rates 0-1 with a 0.1 step
            for i in range(11):
                rate = 1.0 + 0.1 * i
                scenarios[client.name][str(rate)] = []

                for j in range(per_rate_scenarios):
                    scn = Scenario(p)
                    scn.AddRate(client.name, rate)

                    #Create Rates for the other clients
                    for c in p.clients:
                        if (c.name == client.name):
                            continue
                        
                        scn.AddRate(c.name, ScenarioGenerator.FindAcceptableRate(c))
                
                    scenarios[client.name][str(rate)].append(scn)
        
        return scenarios
        



