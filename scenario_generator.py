from planner import PlanningProblem
from common import ContractStatus, ContractType, PaymentStatus
from interest_rate_prediction import InterestRatePrediction
from common import Contract, ScenarioPayment
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
        self.decision_probability = 1.0
        self.rate_probability = 1.0
        self.def_date_probability = 1.0
        self.rates = {}
        self.payments = []
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

    def AddPayment(self, pmnt):
        if (pmnt in self.payments):
            return
        
        self.payments.append(pmnt)

    def GeneratePlanningProblem(self):
        p = PlanningProblem()
        p.StartBalance = self.problem.Balance
        p.CurrentPeriod = self.problem.CurrentPeriod
        p.NumberOfClients = self.problem.NumberOfClients
        p.NumberOfPeriods = 0
        p.LoanRate = self.problem.LoanRate * 0.01

        #Identify Contracts
        for c in self.payments:
            p.NumberOfPeriods = max(p.NumberOfPeriods, c.max_forward_deferral)
            if (c.type == ContractType.INBOUND): #Inbound
                p.InboundPayments.append(c)
            elif (c.type == ContractType.OUTBOUND): #Outbound
                p.OutboundPayments.append(c)    
        
        p.NumberOfPeriods += 1
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
            
            rates = [0.0] + p.Rates
            periods = [0, 1, 2, 3, 4, 5] #Deferral Options
            
            #At first check if the contract is already negotatied
            if (ctr.status == ContractStatus.NEGOTIATED):
                
                #Add all included payments to the scenario with their precalculated amounts
                for inst in ctr.installments:
                    if (inst.status == PaymentStatus.PENDING):
                        ctr_copy = ScenarioPayment(ctr.id, ctr.type, inst.period,
                                                inst.amount, ctr.client, inst.period, inst.period)
                        ctr_copy.id = ctr.id
                        ctr_copy.rate = 0.0
                        scn.AddPayment(ctr_copy)
            
            elif (InterestRatePrediction.IsClientNegotiating(client) and (ctr.status == ContractStatus.UNDER_NEGOTIATION)):
                
                #Reverse in case of outbound contracts
                # if (ctr.type == ContractType.INBOUND):
                #     rates = list(reversed(rates))
                # elif (ctr.type == ContractType.OUTBOUND):
                #     periods = reversed(periods)
                
                rate, r_prob = InterestRatePrediction.GetInterestRateForClient(client, ctr.type, rates, p.IntRateProbCutoff)
                deferral_gap = client.deferral_openness
                
                if (r_prob < 0.5):
                    print("CHECK")

                #Add contract with custom deferral and rate
                ctr_copy = ScenarioPayment(ctr.id, ctr.type, ctr.PlanningHorizonStart,
                                           ctr.amount, ctr.client,
                                           min(p.PlanningHorizonEnd - 1, ctr.PlanningHorizonStart + deferral_gap),
                                           max(p.CurrentPeriod, ctr.PlanningHorizonStart - deferral_gap))
                ctr_copy.rate = rate
                scn.AddPayment(ctr_copy)
                scn.probability *= r_prob
            else:
                #Add contract without deferral
                ctr_copy = ScenarioPayment(ctr.id, ctr.type, ctr.PlanningHorizonStart,
                                           ctr.amount, ctr.client,
                                           min(p.PlanningHorizonEnd - 1, ctr.PlanningHorizonStart),
                                           max(p.CurrentPeriod, ctr.PlanningHorizonStart))
                ctr_copy.id = ctr.id
                ctr_copy.rate = 0.0
                scn.AddPayment(ctr_copy)
    
    @staticmethod
    def GenerateScenarios(p, contract):
        scenario_count = 0
        scenarios = {}
        
        rest_contracts = [c for c in p.contracts if c != contract and c.status != ContractStatus.COMPLETED]
        
        scenarios[contract.id] = {}

        #Generate scenarios for a single installment
        scenarios[contract.id][1] = {}

        #For single installments check the negotiation with multiple deferral periods
        #TODO: Move the deferral periods in a configuration file
        
        for def_period in range(1, 3):
            #Do not allow deferrals that exceed the planning horizon
            #if (def_period + contract.PlanningHorizonStart > p.PlanningHorizonEnd - 1):
            #    continue
            
            scenarios[contract.id][1][def_period] = {}
            for rate in p.Rates:
                scenarios[contract.id][1][def_period][str(rate)] = []

                #Scenario Probability Pre-check
                r_prob = InterestRatePrediction.FindRateProbability(contract.client, contract.type, rate)
                d_prob = InterestRatePrediction.FindDeferralProbability(contract.client, contract.type, def_period, contract.PlanningHorizonStart)
                
                if (r_prob * d_prob < 1e-5):
                    continue

                for j in range(p.ScenariosPerRate):
                    scn = Scenario(p)
                    scn.decision_probability = r_prob * d_prob
                    
                    #Add main contract in a single installment, with the predefined rate and deferral period
                    main_ctr = ScenarioPayment(contract.id,
                                                contract.type, 
                                                contract.PlanningHorizonStart,
                                                contract.amount,
                                                contract.client,
                                                contract.PlanningHorizonStart + def_period,
                                                contract.PlanningHorizonStart + def_period)
                    main_ctr.rate = 0.01 * rate
                    scn.probability *= r_prob * d_prob 
                    
                    scn.AddPayment(main_ctr)
                    
                    ScenarioGenerator.PopulateScenarios(p, scn, rest_contracts)
                    #print(f"Generated Scenarion prob: {scn.probability * 100.0:.2E}")
                    
                    scenarios[contract.id][1][def_period][str(rate)].append(scn)
                    scenario_count += 1
                    

        #Generate scenarios for multiple installments
        for installment_num in p.Installments:
            
            #Make sure there are enough period to accomodate the multiple installments after the contract's default period
            #if (installment_num > p.PlanningHorizonEnd - contract.PlanningHorizonStart + 1):
            #    continue
            
            scenarios[contract.id][installment_num] = {}
            for rate in p.Rates:
                scenarios[contract.id][installment_num][str(rate)] = []
                
                #Scenario Probability Pre-check
                r_prob = InterestRatePrediction.FindRateProbability(contract.client, contract.type, rate)
                d_prob = InterestRatePrediction.FindDeferralProbability(contract.client, contract.type, def_period, contract.PlanningHorizonStart)
                
                if (r_prob * d_prob < 1e-5):
                    continue

                
                for i in range(p.ScenariosPerRate):
                    scn = Scenario(p)
                    scn.decision_probability = r_prob * d_prob

                    #Split main contract into multiple installments starting from the period included in the contract
                    #Add contracts for all installments
                    ctr_installment_amount = (1.0 + 0.01 * rate) * contract.amount / installment_num
                    
                    for j in range(installment_num):
                        main_ctr = ScenarioPayment(contract.id, contract.type, contract.PlanningHorizonStart + j,
                                                    ctr_installment_amount, contract.client, 
                                                    contract.PlanningHorizonStart + j, contract.PlanningHorizonStart + j)
                        main_ctr.rate = 0.0 # Force a rate of 0.0 because the installment amount has been precalculated
                        scn.AddPayment(main_ctr)
                    
                    scn.probability *= InterestRatePrediction.FindRateProbability(contract.client, contract.type, rate)
                    
                    ScenarioGenerator.PopulateScenarios(p, scn, rest_contracts)
                    scenarios[contract.id][installment_num][str(rate)].append(scn)
                    scenario_count += 1

        
        
        return scenarios, scenario_count
        

    @staticmethod
    def CalculateScenarioProbability(s):
        
        #Calculate probability of the entire scenario using the scenario solution
        s.probability = 1.0
        s.rate_probability = 1.0
        s.def_date_probability = 1.0
        
        if s.solution is None:
            return

        for p in s.solution.actions:
            p_actions = s.solution.actions[p]

            for ctr in p_actions:
                #Load the rate from the payment info
                
                rate = ctr['Rate']
                client  = s.problem.GetCounterPartyByName(ctr['Client'])
                ctr_type = ctr['Type']
                period = ctr['StartPeriod']
                
                r_prob = InterestRatePrediction.FindRateProbability(client, ctr_type, rate * 100)
                d_prob = InterestRatePrediction.FindDeferralProbability(client, ctr_type, p, period)
                
                s.probability *= r_prob
                s.rate_probability *= r_prob
                s.probability *= d_prob
                s.def_date_probability *= d_prob

                
        if (s.def_date_probability < 1e-5):
            print("THIS SHOULD NOT HAPPEN")

        

        

        


