from scenario_generator import ScenarioGenerator
from plan_evaluator import PlanEvaluator, ContractEvaluation
from interest_rate_prediction import InterestRatePrediction
from planner import Planner
from common import Contract, Payment, Client, ContractStatus, ContractType, PaymentStatus
from matplotlib import pyplot as plt
import json
from multiprocessing.pool import ThreadPool
from utilities import log, MessageType, random
from math import sqrt
import time

class CAOSProblem:
    CONTRACT_COUNTER = 0
    
    def __init__(self, rates=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5],
                 installments=[3, 6], snpr=5):
        self.Balance = 0
        self.PlanningHorizonEnd = 0
        self.CurrentPeriod = 0
        self.LoanRate = 0.0
        self.Rates = rates
        self.ScenariosPerRate = snpr
        self.Installments = installments
        

        self.contracts = []
        self.contractMap = {}

        self.NumberOfClients = 0
        self.clients = []
        self.clientMap = {}

        self.scenarios = []



    def CreateRandomInstance(self, export_instance=False):
        self.Balance = 0
        self.LoanRate = 1.0 + 2 * random.random()
        self.ScenariosPerRate = 20
        self.Rates = [v * 0.5 for v in range(2, 16)]
        self.Installments = [3, 6]
        
        max_periods = 10 * max(1, random.random())
        
        #Add Clients
        client_num = random.randint(10, 20)
        for c in range(client_num):

            #calculate means for sigmoid functions
            #inbound rate parameters
            b1 = random.uniform(1.0,  4)
            a1 = random.uniform(3.91 / b1, 30)
            
            #outbound rate parameters
            b2 = random.uniform(-6 , -1 )
            a2 = random.uniform(-30, 3.91 / b2)

            d_o = random.randint(0, 5)
            d_i = random.uniform(0.1, (d_o + 1) / 4)

            cl = Client("Client" + str(c), 
                        a1, b1, a2, b2, #Interest rate parameters
                        min(1.0, 0.2 + random.random()), #Negotiation Pref
                        d_o, #Deferral Openness in periods
                        d_i) #Incline of deferral period curve 
                        
            self.AddCounterParty(cl)
        
        self.NumberOfClients = len(self.clients) # Calculate the correct number of clients
        total_contracts = random.randint(20, 50)
        
        for i in range(total_contracts):
            if random.random() > 0.5:
                contract_type = ContractType.INBOUND
            else:
                contract_type = ContractType.OUTBOUND
            
            contract_amount = 1000 * random.randint(1, 6)
            client = self.clients[random.randint(0, len(self.clients) - 1)]
            
            #Create contract
            ctr = Contract(contract_type, client)
            pmnt = Payment(ctr, random.randint(0, max_periods), contract_amount)
            ctr.AddPayment(pmnt)
            self.AddContract(ctr)

        if (export_instance):
            self.ExportState("gen_data.json")
        
    def ExportState(self, filename = 'state.json'):
        #Save Instance to file
        data = {}
        data["Balance"] = self.Balance
        data["CurrentPeriod"] = self.CurrentPeriod
        data["LoanRate"] = self.LoanRate
        data["Rates"] = self.Rates
        data["Installments"] = self.Installments
        data["ScenariosPerRate"] = self.ScenariosPerRate
        
        data["Clients"] = {}
        for c in self.clients:
            data["Clients"][c.name] = {"rate_in_alpha": c.rate_in_a, 
                                       "rate_in_beta": c.rate_in_b, 
                                       "rate_out_alpha": c.rate_out_a, 
                                       "rate_out_beta": c.rate_out_b, 
                                       "negotiation_openness": c.negotiation_openness,
                                       "deferral_openness": c.deferral_openness,
                                       "deferral_incline": c.deferral_incline}
            
        data["Contracts"] = {}
        data["Contracts"]["Inbound"] = []
        data["Contracts"]["Outbound"] = []
        for c in self.contracts:
            c_dict = {'client': c.client.name, 'status': c.status, 'amount': c.amount, 'payments' : []}
            
            for p in c.installments:
                c_dict['payments'].append({'period': p.period, 'amount': p.amount, 'status':p.status})

            if (c.type == ContractType.INBOUND):
                data["Contracts"]["Inbound"].append(c_dict)
            elif (c.type == ContractType.OUTBOUND):
                data["Contracts"]["Outbound"].append(c_dict)
        
        f = open(filename, "w")
        f.write(json.dumps(data))
        f.close()
    
    
    def ImportState(self, instance_name):
        f = open(instance_name)
        data = json.loads(f.read())
        f.close()
        self.LoadJsonData(data)

    def LoadJsonData(self, instance):
        self.CurrentPeriod = instance["CurrentPeriod"]
        self.Balance = instance["Balance"]
        self.LoanRate = instance["LoanRate"]
        self.ScenariosPerRate = instance["ScenariosPerRate"]
        self.Rates = instance["Rates"]
        self.Installments = instance["Installments"]
        
        #Add Clients
        for c in instance["Clients"]:
            c_data = instance["Clients"][c]
            cl = Client(c, 
                        c_data["rate_in_alpha"], c_data["rate_in_beta"],
                        c_data["rate_out_alpha"], c_data["rate_out_beta"],
                        c_data["negotiation_openness"],
                        c_data["deferral_openness"],
                        c_data["deferral_incline"])
            self.AddCounterParty(cl)
        
        self.NumberOfClients = len(self.clients) # Calculate the correct number of clients

        #Add Inbound Contracts
        for c in instance["Contracts"]["Inbound"]:
            client = self.clientMap[c["client"]]
            # NOTE: periods are zero indexed
            
            ctr = Contract(ContractType.INBOUND, client)
            ctr.status = ContractStatus(c["status"])
            for p in c["payments"]:
                #By default add a single payment for now
                pmnt =  Payment(ctr, p["period"], p["amount"])
                pmnt.status = PaymentStatus(p["status"])
                ctr.AddPayment(pmnt)
            self.AddContract(ctr)
        
        #Add Outbound Contracts
        for c in instance["Contracts"]["Outbound"]:
            client = self.clientMap[c["client"]]
            # NOTE: periods are zero indexed

            ctr = Contract(ContractType.OUTBOUND, client)
            ctr.status = ContractStatus(c["status"])
            for p in c["payments"]:
                #By default add a single payment for now
                pmnt =  Payment(ctr, p["period"], p["amount"])
                pmnt.status = PaymentStatus(p["status"])
                ctr.AddPayment(pmnt)
            self.AddContract(ctr)

    #Tweak system configuration
    def SetInstallments(self, installments):
        self.Installments = installments
    
    def SetScenariosPerRate(self, n):
        self.ScenariosPerRate = n

    def SetLoanRate(self, rate):
        self.LoanRate = rate
    
    def ReportContract(self, c):
        print(f"#\t ID: {c.id:03d} \t Client: {c.client.name:<8} \t Status: {c.status.name:<10}")
        for p in c.installments:
            print(
                f"#\t\t Period: {p.period:03d} \t Amount: {p.amount:07.2f} \t Status: {p.status.name:<10}")

    def Report(self):
        print("#######################")
        print("### Statistics")
        print(f"### Current Balance: {self.Balance}")
        print(f"### Current Period: {self.CurrentPeriod} / {self.PlanningHorizonEnd}")
        print("### Total Contracts:", len(self.contracts))
        print("### Total CounterParties", len(self.clients))
        print("#######################")
        
        print("### Inbound Contracts:")
        for c in [f for f in self.contracts if f.type == ContractType.INBOUND]:
            self.ReportContract(c)
            
        print("### Outbound Contracts")
        for c in [f for f in self.contracts if f.type == ContractType.OUTBOUND]:
            self.ReportContract(c)
        
        print("#######################")

    def AddCounterParty(self, client):
        if (client.name in self.clients):
            log(f'Client {client.name} exists', MessageType.WARNING)
            return False
        
        #Set correct Id and save client
        client.id = len(self.clients)
        self.clients.append(client) # Client List
        self.clientMap[client.name] = client # Client Dictionary using their name as the key
        self.NumberOfClients +=1 
        return True

    def GetCounterPartyByName(self, name):
        if (name not in self.clientMap):
            log(f'No client exists with name: {name}', MessageType.WARNING)
            return None
        return self.clientMap[name]

    def AddContract(self, ctr):
        if (ctr.client.name not in self.clientMap):
            log(f'Client {ctr.client.name} does not exist', MessageType.WARNING)
            return False
        
        #TODO: Adopt a better id system. For the prototype contract id's are overridden
        ctr.id = CAOSProblem.CONTRACT_COUNTER
        self.contracts.append(ctr)
        self.contractMap[ctr.id] = ctr
        CAOSProblem.CONTRACT_COUNTER += 1
        self.UpdatePlanningHorizon()
        return True
    
    def GetContractById(self, id):
        if (id not in self.contractMap):
            log(f'No contract exists with id: {id}', MessageType.WARNING)
            return None
        return self.contractMap[id]

    def UpdatePlanningHorizon(self):
        self.PlanningHorizonEnd = 0
        for ctr in self.contracts:
            ctr.UpdatePlanningHorizon() #Update individual contract planning horizons
            self.PlanningHorizonEnd = max(self.PlanningHorizonEnd, ctr.PlanningHorizonEnd)
        
    def ApplyAction(self, action):
        ctr = self.GetContractById(action["contract_id"])
        deferral = action["options"].deferral_periods
        installments = action["options"].installments
        rate = action["options"].rate
        
        print("Calculated Prob: ", InterestRatePrediction.FindRateProbability(ctr.client, ctr.type, rate))
        self.UpdateContract(ctr, deferral, rate, installments)

    
    def UpdateContract(self, contract, f_deferral, f_rate, f_installments):
        #Checks
        if not isinstance(contract, Contract):
            print("Cannot finalize non contract object", MessageType.ERROR)
            log("Non contract object provided", MessageType.ERROR)
            return

        if (contract not in self.contracts):
            print("Unable to finalize contract. Check log")
            log("Contract object does not belong to problem", MessageType.ERROR)
            return

        if (contract.PlanningHorizonStart != self.CurrentPeriod):
            print("Unable to finalize contract. Check log")
            log("Finalizing a future contract is not yet supported", MessageType.WARNING)
            return

        if (contract.status == ContractStatus.COMPLETED):
            print("Contract already finalized. Check log")
            log("Processing of completed contracts is not yet supported", MessageType.WARNING)
            return

        #Finalize contract
        if (f_installments == 1):
            #In the case of 1 installment for a contract of the current period
            #We just have to update the balance appropriately and finalize the contract
            
            #Calculate final amount
            #Since we take decisions on the current period, f_deferral can only be forward in time
            #TODO: Check if we need negative deferral periods
            
            updated_amount = (1.0 + 0.01 * f_rate * f_deferral) * contract.amount

            #Set contract as negotiated
            contract.status = ContractStatus.NEGOTIATED
            contract.ClearPayments()

            #Add new payment
            pmnt = Payment(contract, f_deferral + self.CurrentPeriod, updated_amount)
            contract.AddPayment(pmnt)
            contract.UpdatePlanningHorizon()

        else:
            updated_amount = (1.0 + 0.01 * f_rate) * contract.amount
            installment_amount = updated_amount / f_installments
            
            contract.ClearPayments()

            for i in range(f_installments):
                pmnt = Payment(contract, contract.PlanningHorizonStart + i, installment_amount)
                contract.AddPayment(pmnt)
            
            contract.UpdatePlanningHorizon()
            contract.status = ContractStatus.NEGOTIATED

    def ProcessPayments(self):
        #At first do a precheck that all contracts due for this period have been negotiated
        for c in self.contracts:
            if (c.PlanningHorizonStart == self.CurrentPeriod and c.status != ContractStatus.NEGOTIATED):
                print("Non negotiated contracts for this period!")
                return False
        
        #Since all contracts of this period have been negotiated we can process the payments
        for c in self.contracts:
            for scn_pmnt in c.installments:
                if (scn_pmnt.period == self.CurrentPeriod):
                    if (c.type == ContractType.INBOUND):
                        self.Balance += scn_pmnt.amount
                    elif (c.type == ContractType.OUTBOUND):
                        self.Balance -= scn_pmnt.amount
                    scn_pmnt.status = PaymentStatus.COMPLETED #Complete Payment
            if (c.IsComplete()):
                c.status = ContractStatus.COMPLETED
        return True

    def AdvancePeriod(self):
        #Advance Period only if payments for this period were successfully negotiated
        if (self.ProcessPayments()):
            self.CurrentPeriod += 1

    def GetActiveContracts(self):
        #Check for contracts of the current period
        contract_list = []
        for c in self.contracts:
            if c.PlanningHorizonStart == self.CurrentPeriod and c.status == ContractStatus.UNDER_NEGOTIATION:
                contract_list.append(c)

        return contract_list

    def GeneratePlanEvaluations(self, ctr, policy_id):
        res = PlanEvaluator.EvaluateContract(ctr.id, self)
        results = [r.toDict() for r in res]

        #Cache results 
        f = open("report.json", "w")
        f.write(json.dumps(results))
        f.close()
        print("Analysis logged saved to report.json")

        #Sort plans based on the selected policy
        if (policy_id == 1):
            plan_list = sorted(res, key=lambda x: x.weighted_objective, reverse=True)
        elif (policy_id == 2):
            plan_list = sorted(res, key=lambda x: x.objective, reverse=True)
        elif (policy_id == 3):
            plan_list = sorted(res, key=lambda x: x.probability, reverse=True)

        #Filter empty actions
        plan_list = [p for p in plan_list if p.scenario_num > 0]

        return plan_list

    def GenerateAction(self, ctr, evaluation):
        return {'contract_id': ctr.id, 'options': evaluation}

    def GenerateScenarios(self, ctr):
        self.scenarios, scn_count = ScenarioGenerator.GenerateScenarios(self, ctr)
        log(f'Generated {scn_count} scenarios', MessageType.WARNING)
        return scn_count
    
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

        #Create thread pool
        processes_num = 2
        st = time.time()
        log(f'Solving {len(scenario_list)} scenarios using {processes_num} threads', MessageType.INFO)
        pool = ThreadPool(processes=processes_num)
        pool.map(self.SolveScenario, scenario_list)
        pool.close()
        pool.join()
        log(f'Solving Completed in {time.time() - st} seconds', MessageType.INFO)
    
    def SolveScenario(self, s):
        #Create Planning Problem from scenario
        p = s.GeneratePlanningProblem()
        #Save the planning problem solution in the scenario
        try:
            s.solution = Planner.Solve(p)
            #print("Calculating Probability")
            ScenarioGenerator.CalculateScenarioProbability(s) #Recalculate probabilities
        except Exception as ex:
            log(f"Problem when solving Scenario {s.index}", MessageType.ERROR)
            log(ex, MessageType.ERROR)
        finally:
            #print("Done")
            pass
    


if (__name__ == "__main__"):
    p = CAOSProblem()
    p.CreateRandomInstance()
    p.ExportInstance()
