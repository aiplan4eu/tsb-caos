from scenario_generator import ScenarioGenerator
from plan_evaluator import PlanEvaluator
from planner import Planner
from common import Contract, Client, ContractStatus, ContractType
from matplotlib import pyplot as plt
import json
from multiprocessing.pool import ThreadPool
from utilities import log, random
import time



class CAOSProblem:
    CONTRACT_COUNTER = 0
    
    def __init__(self, ):
        self.Balance = 0
        self.PlanningHorizonEnd = 0
        self.CurrentPeriod = 0
        self.LoanRate = 0.0
        
        self.contracts = []
        self.contractMap = {}

        self.clients = []
        self.clientMap = {}

        self.scenarios = []
        

    def CreateRandomInstance(self):
        self.StartBalance = 0
        self.LoanRate = 1.0 + 2 * random.random()
        self.ScenariosPerRate = 20
        self.Rates = [v * 0.5 for v in range(2, 16)]
        self.Installments = [3, 6]
        
        max_periods = 10 * max(1, random.random())
        
        #Add Clients
        client_num = random.randint(10, 20)
        for c in range(client_num):
            self.AddCounterParty("Client" + str(c), 
                                 0.5 + 3.0 * random.random(),
                                 1.5 + 4.5 * random.random(),
                                 max(1.0, min(0.5, 0.5 + random.random())),
                                 max(1.0, min(0.25, 0.25 + random.random())))
        
        self.NumberOfClients = len(self.clients) # Calculate the correct number of clients
        total_contracts = random.randint(20, 50)
        
        for i in range(total_contracts):
            if random.random() > 0.5:
                contract_type = ContractType.INBOUND
            else:
                contract_type = ContractType.OUTBOUND

            contract_amount = 1000 * random.randint(1, 6)
            client = self.clients[random.randint(0, len(self.clients) - 1)]
            
            self.AddContract(client, random.randint(0, max_periods), contract_amount, contract_type)
        
    def ExportInstance(self):
        #Save Instance to file
        data = {}
        data["StartBalance"] = self.StartBalance
        data["LoanRate"] = self.LoanRate
        data["Rates"] = self.Rates
        data["Installments"] = self.Installments
        data["ScenariosPerRate"] = self.ScenariosPerRate
        
        data["Clients"] = {}
        for c in self.clients:
            data["Clients"][c.name] = {"a": c.alpha, 
                                       "b": c.beta, 
                                       "negotiation_preference": c.negotiation_preference,
                                       "deferral_openess": c.deferral_openess}
        

        data["Contracts"] = {}
        data["Contracts"]["Inbound"] = []
        data["Contracts"]["Outbound"] = []
        for c in self.contracts:
            if (c.type == ContractType.INBOUND):
                data["Contracts"]["Inbound"].append({"client": c.client.name, "period": c.period, "amount": c.amount})
            elif (c.type == ContractType.OUTBOUND):
                data["Contracts"]["Outbound"].append({"client": c.client.name, "period": c.period, "amount": c.amount})
        
        f = open("gen_data.json", "w")
        f.write(json.dumps(data))
        f.close()
    

    def LoadInstance(self, instance):
        self.StartBalance = instance["StartBalance"]
        self.LoanRate = instance["LoanRate"]
        self.ScenariosPerRate = instance["ScenariosPerRate"]
        self.Rates = instance["Rates"]
        self.Installments = instance["Installments"]
        
        #Add Clients
        for c in instance["Clients"]:
            c_data = instance["Clients"][c]
            self.AddCounterParty(c, c_data["a"], c_data["b"], 
                                 c_data["negotiation_preference"], c_data["deferral_openess"])
        self.NumberOfClients = len(self.clients) # Calculate the correct number of clients

        #Add Inbound Contracts
        for c in instance["Contracts"]["Inbound"]:
            client = self.clientMap[c["client"]]
            # NOTE: periods are zero indexed
            self.AddContract(client, c["period"], c["amount"], ContractType.INBOUND)

        #Add Outbound Contracts
        for c in instance["Contracts"]["Outbound"]:
            client = self.clientMap[c["client"]]
            # NOTE: periods are zero indexed
            self.AddContract(client, c["period"], c["amount"], ContractType.OUTBOUND)


    def Report(self):
        print("#######################")
        print("### Instance Statistics")
        print("### Total Periods:", self.PlanningHorizonEnd)
        print("### Total Contracts:", len(self.contracts))
        print("### Total CounterParties", len(self.clients))
        print("#######################")
        
        print("### Inbound Contracts:")
        for c in [f for f in self.contracts if f.type == ContractType.INBOUND]:
            print(f"#\t ID: {c.id} \t Period: {c.period} \t Client: {c.client.name:<8} \t Amount: {c.amount} \t Type: {c.status}")
            
        print("### Outbound Contracts")
        for c in [f for f in self.contracts if f.type == ContractType.OUTBOUND]:
            print(f"#\t ID: {c.id} \t Period: {c.period} \t Client: {c.client.name:<8} \t Amount: {c.amount} \t Type: {c.status}")
        
        print("#######################")

    def AddCounterParty(self, name, a, b, c, d):
        if (name in self.clients):
            log(f'Client {name} exists', "WARNING")
            return

        #Create CounterParty
        c = Client(name, a, b, c, d)
        c.id = len(self.clients)
        self.clients.append(c) # Client List
        self.clientMap[name] = c # Client Dictionary using their name as the key

    def AddContract(self, client, period, amount, typ):
        ctr = Contract(typ, period, amount, client)
        ctr.id = CAOSProblem.CONTRACT_COUNTER
        ctr.type = typ
        self.contracts.append(ctr)
        self.contractMap[ctr.id] = ctr
        self.PlanningHorizonEnd = max(self.PlanningHorizonEnd, period + 1)
        CAOSProblem.CONTRACT_COUNTER +=1

    def UpdateContract(self, contract, f_deferral, f_rate, f_installments):
        #Checks
        if not isinstance(contract, Contract):
            print("Cannot finalize non contract object", "ERROR")
            log("Non contract object provided", "ERROR")
            return

        if (contract not in self.contracts):
            print("Unable to finalize contract. Check log")
            log("Contract object does not belong to problem", "ERROR")
            return

        if (contract.period != self.CurrentPeriod):
            print("Unable to finalize contract. Check log")
            log("Finalizing a future contract is not yet supported", "WARNING")
            return

        #Finalize contract
        if (f_installments == 1):
            #In the case of 1 installment for a contract of the current period
            #We just have to update the balance appropriately and finalize the contract
            
            #Calculate final amount
            updated_amount = (1.0 + 0.01 * f_rate * (f_deferral - contract.period)) * contract.amount

            if (f_deferral == self.CurrentPeriod):
                #Update contract parameters
                contract.status = ContractStatus.FINALIZED
                contract.amount = updated_amount
                contract.rate = f_rate
            
                if (contract.type == ContractType.INBOUND):
                    self.Balance += updated_amount
                elif (contract.type == ContractType.OUTBOUND):
                    self.Balance -= updated_amount
                print("Contract Finalized!")
            else:
                #Just apply new settings to the contract
                contract.period = f_deferral
                contract.amount = updated_amount
                contract.rate = 1.0
        else:
            print("TODO")
            assert(False)
        
    def AdvancePeriod(self):
        for c in self.contracts:
            if (c.period == self.CurrentPeriod):
                print("Unable to advance schedule, non finalized contracts exist")
                return
        self.CurrentPeriod += 1

    def GenerateScenarios(self):
        self.scenarios, scn_count = ScenarioGenerator.GenerateScenarios(self)
        log(f'Generated {scn_count} scenarios', "INFO")
    
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
        processes_num = 8
        st = time.time()
        log(f'Solving {len(scenario_list)} scenarios using {processes_num} threads', "INFO")
        pool = ThreadPool(processes=processes_num)
        pool.map(self.SolveScenario, scenario_list)
        pool.close()
        pool.join()
        log(f'Solving Completed in {time.time() - st} seconds', "INFO")
    
    def SolveScenario(self, s):
        #Create Planning Problem from scenario
        p = s.GeneratePlanningProblem()
        #Save the planning problem solution in the scenario
        try:
            s.solution = Planner.Solve(p)
        except Exception as ex:
            log(f"Problem when solving Scenario {s.index}", "ERROR")
            log(ex, "ERROR")
        finally:
            #print("Done")
            pass
            
    
    def PostProcess(self):
        response = {}
        
        for contract_id in self.scenarios:
            response[contract_id] = {'scenario_results': []}
            res = PlanEvaluator.EvaluateContract(contract_id, self)
            response[contract_id]['scenario_results'] = [r.toDict() for r in res]
            
            #Post Process results and find scenario with the best score for every policy
            p1_ctr = PlanEvaluator.GetPlanWithMaxPolicy(res, 1)
            p2_ctr = PlanEvaluator.GetPlanWithMaxPolicy(res, 2)
            p3_ctr = PlanEvaluator.GetPlanWithMaxPolicy(res, 3)
            
            #Store results to the response
            response[contract_id]['Policy 1'] = p1_ctr.toDict()
            response[contract_id]['Policy 2'] = p2_ctr.toDict()
            response[contract_id]['Policy 3'] = p3_ctr.toDict()
            
            print("################")
            print("### Best Options for contract", contract_id)
            print("### Policy 1")
            print(p1_ctr.toDict())
            print("### Policy 2")
            print(p2_ctr.toDict())
            print("### Policy 3")
            print(p3_ctr.toDict())
            print("################")
            
            #TODO: Create Plots     
            #self.CreatePlot(res["Policy 1"]["Values"].keys(), res["Policy 1"]["Values"].values(), str(ctr.id) + "_pol1", "Policy 1")
            #self.CreatePlot(res["Policy 2"]["Values"].keys(), res["Policy 2"]["Values"].values(), str(ctr.id) + "_pol2", "Policy 2")
            #self.CreatePlot(res["Policy 3"]["Values"].keys(), res["Policy 3"]["Values"].values(), str(ctr.id) + "_pol3", "Policy 3")

        f = open("report.json", "w")
        f.write(json.dumps(response))
        f.close()
        print("### Results saved to report.json")
    
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
        



if (__name__ == "__main__"):
    p = CAOSProblem()
    p.CreateRandomInstance()
    p.ExportInstance()