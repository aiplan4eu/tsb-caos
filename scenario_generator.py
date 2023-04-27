from planner import PlanningProblem
from interest_rate_prediction import InterestRatePrediction
from common import Contract
import random
from math import sqrt, pi, exp
from utilities import log


class Scenario:
    def __init__(self, p):
        self.problem = p
        self.solution = None
        self.probability = 1.0
        self.rates = {}
        self.Contracts = []
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

    def AddContract(self, contract):
        if (contract in self.Contracts):
            return
        
        self.Contracts.append(contract)

    def GeneratePlanningProblem(self):
        p = PlanningProblem()
        p.StartBalance = self.problem.StartBalance
        p.NumberOfClients = self.problem.NumberOfClients
        p.NumberOfPeriods = self.problem.NumberOfPeriods
        p.LoanRate = self.problem.LoanRate * 0.01

        #Identify Contracts
        for c in self.Contracts:
            if (c.type == 1): #Inbound
                p.InboundContracts.append(c)    
            elif (c.type == 2): #Outbound
                p.OutboundContracts.append(c)    
        
        return p


class ScenarioGenerator:
    def __init__():
        pass
    
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
    def PopulateScenarios(p, scn, rem_contracts):
        #Process remaining contracts
        for ctr in rem_contracts:
            client = ctr.client
            
            rates = p.Rates
            periods = [0, 1, 2, 3, 4, 5]
            
            if (InterestRatePrediction.IsClientNegotiating(client)):
                #Reverse in case of outbound contracts
                if (ctr.type == 1):
                    rates = reversed(rates)
                elif (ctr.type == 2):
                    periods = reversed(periods)
                
                rate = InterestRatePrediction.GetInterestRateForClient(client, rates)
                deferral_gap = InterestRatePrediction.GetMaxDeferralPeriods(client, periods)
                
                #Add contract with custom deferral and rate
                ctr_copy = Contract(ctr.type, ctr.period, ctr.amount, ctr.client, ctr.period + deferral_gap, ctr.period - deferral_gap)
                ctr_copy.id = ctr.id
                ctr_copy.rate = rate
                scn.AddContract(ctr_copy)
            
            else:
                #Add contract without deferral
                ctr_copy = Contract(ctr.type, ctr.period, ctr.amount, ctr.client, ctr.period, ctr.period)
                ctr_copy.id = ctr.id
                ctr_copy.rate = 0.0
                scn.AddContract(ctr_copy)
    
    
    @staticmethod
    def GenerateScenarios(p):
        scenario_count = 0
        scenarios = {}
        
        #Generate scenarios for the clients with contracts on the first period
        contract_list = []
        
        for i in range(p.NumberOfPeriods):
            #Check of period 0
            for c in p.Contracts:
                if c.period == i:
                    contract_list.append(c)    
            
            if (len(contract_list) != 0):
                break
        
        
        for contract in contract_list:
            rest_contracts = [c for c in p.Contracts if c != contract]
            
            scenarios[contract.id] = {}

            #Generate scenarios for a single installment
            scenarios[contract.id][1] = {}

            #For single installments check the negotiation with multiple deferral periods
            for def_period in [0, 1, 2, 3, 4, 5]:
                if (def_period > p.NumberOfPeriods - 1):
                    continue
                
                scenarios[contract.id][1][def_period] = {}
                for rate in p.Rates:
                    scenarios[contract.id][1][def_period][str(rate)] = []

                    for j in range(p.ScenariosPerRate):
                        scn = Scenario(p)
                        main_ctr = Contract(contract.type, contract.period, contract.amount, contract.client, 
                                            contract.period + def_period, contract.period - def_period)
                        main_ctr.id = contract.id
                        main_ctr.rate = rate
                        scn.AddContract(main_ctr)
                        
                        ScenarioGenerator.PopulateScenarios(p, scn, rest_contracts)
                        scenarios[contract.id][1][def_period][str(rate)].append(scn)
                        scenario_count += 1


            #Generate scenarios for multiple installments
            #payments in 3 or in 6 installments
            
            for installment_num in [3, 6]:
                
                if (installment_num > p.NumberOfPeriods):
                    continue
                
                scenarios[contract.id][installment_num] = {}
                for rate in p.Rates:
                    scenarios[contract.id][installment_num][str(rate)] = []

                    for j in range(p.ScenariosPerRate):
                        scn = Scenario(p)

                        #Add contracts for all installments
                        main_ctr = Contract(contract.type, contract.period, contract.amount, contract.client, contract.period, contract.period)
                        main_ctr.id = contract.id
                        main_ctr.rate = rate
                        scn.AddContract(main_ctr)
                        
                        ScenarioGenerator.PopulateScenarios(p, scn, rest_contracts)
                        scenarios[contract.id][installment_num][str(rate)].append(scn)
                        scenario_count += 1
            

        log("Generated " + str(scenario_count) + " Scenarios")
        return scenarios
        



