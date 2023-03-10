from planner import PlanningProblem
import random
from math import sqrt, pi, exp

class Scenario:
    def __init__(self, p):
        self.problem = p
        self.solution = None
        self.probability = 1.0
        self.rates = {}
        for c in p.clients:
            self.rates[c.name] = 1.0

    def GetWeightedObjective(self):
        return self.probability * self.solution.objective

    def GetObjective(self):
        return self.solution.objective
    
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
        p.LoanRate = self.problem.LoanRate * 0.01

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
    def FindRateProbability(client, rate):
        #TODO: Needs calibration for the range of rates
        
        #Normal distribution
        #client alpha is the standard deviation > 0.4
        #client beta is the mean value of accepted rates
        #prob = (1.0 / (client.alpha * sqrt(2.0 * pi))) * exp(-pow(rate - client.beta, 2)/(2 * client.alpha * client.alpha))
        
        #Logistic Function
        #client alpha is the growth rate [1 , 50]
        #client beta is the mean value [1 , 10]
        prob = 1.0 - (1.0 / (1.0 + exp(-client.alpha * (rate - client.beta))))
        #Clamp the result
        return min(max(prob, 0.0), 1.0)

    @staticmethod
    def FindAcceptableRate(client):
        while(True):
            #Choose a rate at random from 1% to 10%
            pred_rate = random.randint(1, 100) / 10.0

            #Calculate the acceptance probability of the rate
            prob =  ScenarioGenerator.FindRateProbability(client, pred_rate)
            
            #See if we can accept this rate with another experiment
            chance = random.randint(1, 100) / 100.0
            
            if (chance < prob):
                return pred_rate
    
    
    @staticmethod
    def GenerateScenarios(p, per_rate_scenarios):
        scenarios = {}
        
        #Generate scenarios for the clients of the current period
        client_list = []

        for i in range(p.NumberOfPeriods):
            #Check of period 0
            for c_id in p.Contracts:
                c = p.Contracts[c_id]
                if c.period == i and c.client not in client_list:
                    client_list.append(c.client)    

            if (len(client_list) != 0):
                break
        
        
        for client in client_list:
            scenarios[client.name] = {}

            #Iterate in interest rates 1-10 with a 0.5 step
            for i in range(8):
                rate = 1.0 + 0.5 * i
                scenarios[client.name][str(rate)] = []

                for j in range(per_rate_scenarios):
                    scn = Scenario(p)
                    scn.AddRate(client.name, rate)
                    scn.probability *= ScenarioGenerator.FindRateProbability(client, rate)
                    #Create Rates for the other clients
                    for c in p.clients:
                        if (c.name == client.name):
                            continue
                        
                        c_rate = ScenarioGenerator.FindAcceptableRate(c)
                        scn.probability *= ScenarioGenerator.FindRateProbability(c, c_rate)
                        scn.AddRate(c.name, c_rate)
                    
                    scenarios[client.name][str(rate)].append(scn)
        
        return scenarios
        



