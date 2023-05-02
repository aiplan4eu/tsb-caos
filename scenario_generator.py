from planner import PlanningProblem
from common import ContractStatus, ContractType
from interest_rate_prediction import InterestRatePrediction
from common import Contract
import random
from math import sqrt, pi, exp

scenarioIndex = 0

class Scenario:
    def __init__(self, p):
        global scenarioIndex
        self.index = scenarioIndex
        self.problem = p
        self.solution = None
        self.probability = 1.0
        self.rates = {}
        self.contracts = []
        for c in p.clients:
            self.rates[c.name] = 1.0
        scenarioIndex += 1

    def GetWeightedObjective(self):
        if (self.solution is None):
            return -1000.0
        return self.probability * self.solution.objective

    def GetObjective(self):
        if (self.solution is None):
            return -1000.0
        return self.solution.objective
    
    def AddRate(self, client_name, rate):
        if (client_name not in self.rates):
            print("Client does not exist")
            return
        
        self.rates[client_name] = rate

    def AddContract(self, contract):
        if (contract in self.contracts):
            return
        
        self.contracts.append(contract)

    def GeneratePlanningProblem(self):
        p = PlanningProblem()
        p.StartBalance = self.problem.Balance
        p.CurrentPeriod = self.problem.CurrentPeriod
        p.NumberOfClients = self.problem.NumberOfClients
        p.NumberOfPeriods = self.problem.PlanningHorizonEnd
        p.LoanRate = self.problem.LoanRate * 0.01

        #Identify Contracts
        for c in self.contracts:
            if (c.type == ContractType.INBOUND): #Inbound
                p.InboundContracts.append(c)    
            elif (c.type == ContractType.OUTBOUND): #Outbound
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
            periods = [0, 1, 2, 3, 4, 5] #Deferral Options
            
            if (InterestRatePrediction.IsClientNegotiating(client) and not ctr.fixed):
                #Reverse in case of outbound contracts
                if (ctr.type == ContractType.INBOUND):
                    rates = reversed(rates)
                elif (ctr.type == ContractType.OUTBOUND):
                    periods = reversed(periods)
                
                rate, r_prob = InterestRatePrediction.GetInterestRateForClient(client, rates)
                deferral_gap, def_prob = InterestRatePrediction.GetMaxDeferralPeriods(client, periods)
                
                #Add contract with custom deferral and rate
                ctr_copy = Contract(ctr.type, ctr.period, ctr.amount, ctr.client, 
                                    min(p.PlanningHorizonEnd - 1, ctr.period + deferral_gap), 
                                    max(0, ctr.period - deferral_gap))
                
                ctr_copy.id = ctr.id
                ctr_copy.rate = rate
                scn.AddContract(ctr_copy)
                scn.probability *= (r_prob * def_prob)
            else:
                #Add contract without deferral
                ctr_copy = Contract(ctr.type, ctr.period, ctr.amount, ctr.client, ctr.period, ctr.period)
                ctr_copy.id = ctr.id
                ctr_copy.rate = 1.0
                scn.AddContract(ctr_copy)
    
    
    @staticmethod
    def GenerateScenarios(p):
        scenario_count = 0
        scenarios = {}
        
        #Generate scenarios for the clients with contracts on the first period
        contract_list = []
        
        #Check for contracts of the current period
        for c in p.contracts:
            if c.period == p.CurrentPeriod and c.status == ContractStatus.UNDER_NEGOTATION:
                contract_list.append(c)
        
        for contract in contract_list:
            rest_contracts = [c for c in p.contracts if c != contract and c.period >= p.CurrentPeriod and c.status != ContractStatus.FINALIZED]
            
            scenarios[contract.id] = {}

            #Generate scenarios for a single installment
            scenarios[contract.id][1] = {}

            #For single installments check the negotiation with multiple deferral periods
            #TODO: Move the deferral periods in a configuration file
            for def_period in [1, 2, 3, 4, 5]:
                if (def_period + contract.period > p.PlanningHorizonEnd - 1):
                    continue
                
                scenarios[contract.id][1][def_period] = {}
                for rate in p.Rates:
                    scenarios[contract.id][1][def_period][str(rate)] = []

                    for j in range(p.ScenariosPerRate):
                        scn = Scenario(p)

                        #Add main contract in a single installment, with the predefined rate and deferral period
                        main_ctr = Contract(contract.type, contract.period, contract.amount, contract.client, 
                                            contract.period + def_period, contract.period + def_period)
                        main_ctr.id = contract.id
                        main_ctr.rate = 0.01 * rate
                        scn.probability *= InterestRatePrediction.FindRateProbability(contract.client, rate) * InterestRatePrediction.FindDeferralProbability(contract.client, def_period)
                        scn.AddContract(main_ctr)
                        
                        ScenarioGenerator.PopulateScenarios(p, scn, rest_contracts)
                        scenarios[contract.id][1][def_period][str(rate)].append(scn)
                        scenario_count += 1

            
            #Generate scenarios for multiple installments
            for installment_num in p.Installments:
                
                #Make sure there are enough period to accomodate the multiple installments after the contract's default period
                if (installment_num > p.PlanningHorizonEnd - contract.period + 1):
                    continue
                
                scenarios[contract.id][installment_num] = {}
                for rate in p.Rates:
                    scenarios[contract.id][installment_num][str(rate)] = []
                    
                    for i in range(p.ScenariosPerRate):
                        scn = Scenario(p)

                        #Split main contract into multiple installments starting from the period included in the contract
                        #Add contracts for all installments
                        ctr_installment_amount = (1.0 + 0.01 * rate) * contract.amount / installment_num
                        
                        for j in range(installment_num):
                            main_ctr = Contract(contract.type, contract.period + j, ctr_installment_amount, contract.client, contract.period + j, contract.period + j)
                            main_ctr.id = contract.id
                            main_ctr.rate = 1.0 # Force a rate of 1.0 because the installment amount has been precalculated
                            scn.AddContract(main_ctr)
                        
                        scn.probability *= InterestRatePrediction.FindRateProbability(contract.client, rate)
                        
                        ScenarioGenerator.PopulateScenarios(p, scn, rest_contracts)
                        scenarios[contract.id][installment_num][str(rate)].append(scn)
                        scenario_count += 1

            break #STUDY THE FIRST FOUND CONTRACT FOR PERIOD 0
        
        return scenarios, scenario_count
        



