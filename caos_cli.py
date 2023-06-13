from problem import CAOSProblem, Client, Contract, ContractType, Payment
from plan_evaluator import PlanEvaluator, ContractEvaluation
import os, time

class Item:
    def __init__(self, name, f):
        self.name = name
        self.func_name = f
        self.parent = None

    def Activate(self, ob):
        getattr(ob, self.func_name)()
    
class Menu:
    def __init__(self, name):
        self.name = name
        self.items = {}
        self.parent = None

    def AddItem(self, item):
        item.parent = self
        self.items[item.name] = item

    def RemoveItem(self, name):
        del self.items[name]


class CAOS_CLI:
    
    def __init__(self):
        self.problem = None
        self.active_ctr = None
        self.active_action = None
        self.active_cmd_set = None
        self.parent_cmd_set = None
        
        #Create Menus
        menu = Menu('main')
        
        
        state_menu = Menu('state')
        state_menu.AddItem(Item('create', 'Create'))
        state_menu.AddItem(Item('save', 'Save'))
        state_menu.AddItem(Item('load', 'Load'))
        state_menu.AddItem(Item('config', 'Configure'))
        state_menu.AddItem(Item('analyze', 'AnalyzeState'))
        state_menu.AddItem(Item('advance', 'AdvanceState'))
        state_menu.AddItem(Item('report', 'ProblemReport'))
        
        action_menu = Menu('action')
        action_menu.AddItem(Item('apply', 'ApplyAction'))
        action_menu.AddItem(Item('select', 'SelectAction'))

        state_menu.AddItem(action_menu)

        client_menu = Menu("client")
        client_menu.AddItem(Item('add', 'AddClient'))
        client_menu.AddItem(Item('view', 'ViewClient'))
        
        contract_menu = Menu("contract")
        contract_menu.AddItem(Item('add', 'AddContract'))
        contract_menu.AddItem(Item('view', 'ViewContract'))
        contract_menu.AddItem(Item('select', 'SelectContract'))

        state_menu.AddItem(client_menu)
        state_menu.AddItem(contract_menu)
        
        menu.AddItem(state_menu)
        menu.AddItem(Item('help', 'Help'))
        menu.AddItem(Item('exit', None))
        
        self.active_menu = menu

    def Run(self):
        self.Greet()
        while (True):
            cmd = input("> ")
            
            if (cmd == 'exit'):
                self.Terminate()
                return
            elif (cmd == "back"):
                if (self.active_menu.parent == None):
                    continue
                else:
                    self.active_menu = self.active_menu.parent
            elif (cmd == 'help'):
                self.Help()
            elif (cmd in self.active_menu.items):
                if (isinstance(self.active_menu.items[cmd], Menu)):
                    self.active_menu = self.active_menu.items[cmd]
                else:
                    self.active_menu.items[cmd].Activate(self)
            else:
                print("Unknown command")

    def Greet(self):
        print("------------------------")
        print("CMD Client for CAOS System v0.1")
        print("Type help for a list of all available commands")
        print("------------------------")
    
    def Help(self):
        print("Available Commands: ", list(self.active_menu.items.keys()))

    def Configure(self):
        if (self.problem is None):
            print("Uninitialized state.")
            return
        
        self.problem.ScenariosPerRate =  int(input("Set Scenarios Per Rate (int): "))
        self.problem.WorkerNum =  int(input("Set Number of Workers to work on scenarios (int): "))
        self.problem.DecisionProbCutoff = float(input("Set cutoff for decision probabilities (decimal): "))
        self.problem.DefDateProbCutoff = float(input("Set Deferral Date Probability Cutoff (decimal): "))
        self.problem.IntRateProbCutoff = float(input("Set Interest Rate Probability Cutoff (decimal): "))
    
    def Terminate(self):
        #Ask user if they wish to save changes
        while(True):
            ans = input("Save changes? (Y/N): ")
            
            if (ans in ['Y', 'y']):
                self.Save()
                return
            elif (ans in ['N', 'n']):
                return
            else:
                continue

        
    def ProblemReport(self):
        if not self.CheckState():
            return
        self.problem.Report()

    def StateReport(self):
        print('Current Contract:', self.active_ctr)
        print('Current Action:', self.active_action)

    def CheckState(self):
        if (self.problem is None):
            print("Uninitialized state.")
            return False
        return True
        
    def Create(self):
        self.problem = CAOSProblem()
        print("New state successfully created.")

    def Load(self):
        fname = input("Select filename to load from: ")
        
        if (os.path.exists(fname)):
            self.problem = CAOSProblem()
            self.problem.ImportState(fname)
            print(f"Loaded System state from {fname}")
        else:
            print("File does not exist")
    
    def Save(self):
        fname = input("Select filename to save to: ")
        self.problem.ExportState(fname)
        print(f"State saved successfully to {fname}")

    def ViewClient(self):
        if not self.CheckState():
            return
        
        if (len(self.problem.clients) == 0):
            print("No clients registered to the system")
            return
        else:
            #Ask the user to select a contract to negotiate
            print("Please select a client to overview: ")
            for i in range(len(self.problem.clients)):
                c = self.problem.clients[i]
                print(f"{i}) Client {c.name}")

            selected_contract_id = int(input("Selected Option: "))
            c = self.problem.clients[selected_contract_id]
            c.Report()

    def AddClient(self):
        if not self.CheckState():
            return
        
        print('Please input client parameters')
        name = input('Client name: ')
        neg_pref = float(input('Negotiation Preference (decimal) : '))
        a1 = float(input('a1 (decimal) : '))
        b1 = float(input('b1 (decimal) : '))
        a2 = float(input('a2 (decimal) : '))
        b2 = float(input('b2 (decimal) : '))
        epsilon = float(input('epsilon (int) : '))
        gamma = float(input('gamma (decimal) : '))
        
        c = Client(name, a1, b1, a2, b2, neg_pref, epsilon, gamma)
        
        if not self.problem.AddCounterParty(c):
            print('Client insertion failed. Check log')
        else:
            print('Client successfully inserted.')
    

    def AddContract(self):
        if not self.CheckState():
            return
        print('Please select Contract Type')
        print('0) Inbound')
        print('1) Outbound')
        c_type = int(input('Select Option: '))

        if (c_type == 0):
            ctr_type = ContractType.INBOUND
        else:
            ctr_type = ContractType.OUTBOUND

        print('Please select Client')
        for i in range(len(self.problem.clients)):
            c = self.problem.clients[i]
            print(f'{i}) {c.name}')

        c_id = int(input('Select Client Option: '))
        
        client = self.problem.clients[c_id]

        amount = float(input('Set total contract amount: '))
        period = int(input('Set due period for the contract: '))

        c = Contract(ctr_type, client)
        p = Payment(c, period, amount)
        c.AddPayment(p)

        if not self.problem.AddContract(c):
            print('Contract insertion failed. Check log.')
        else:
            print('Contract successfully inserted')

    def ViewContract(self):
        if not self.CheckState():
            return
        
        if (len(self.problem.contracts) == 0):
            print("No contracts registered to the system")
            return
        else:
            #Ask the user to select a contract to negotiate
            print("Please select a client to overview: ")
            for i in range(len(self.problem.contracts)):
                c = self.problem.contracts[i]
                print(f"{i}) Contract {c.id}")

            selected_contract_id = int(input("Selected Option: "))
            c = self.problem.contracts[selected_contract_id]
            self.problem.ReportContract(c)

    def SelectContract(self):
        if not self.CheckState():
            return
        
        print("Please select contract period range:")
        start_p = int(input("From Period: "))
        end_p = int(input("To Period: "))
        
        #Get contracts
        contract_list = self.problem.GetContracts(start_p, end_p)
        
        if (len(contract_list) == 0):
            print("No contracts for the selected period range")
            return
        else:
            #Ask the user to select a contract to negotiate
            print("Please select a contract to negotiate: ")
            for i in range(len(contract_list)):
                c = contract_list[i]
                print(f"{i}) Contract {c.id}")
            selected_contract_id = int(input("Selected Option: "))
            
            #Set Active Contract
            self.active_ctr = contract_list[selected_contract_id]

    def ApplyAction(self):
        if not self.CheckState():
            return
        print("Current Action")
        print(f"Contract : {self.active_action['contract_id']}")
        print(f"Deferral : {self.active_action['options'].deferral_periods} period(s)")
        print(f"Interest Rate : {self.active_action['options'].rate} %")
        print(f"No. Installments : {self.active_action['options'].installments}")
        
        ans = input("Apply? (y/n) ")
        if (ans in ['y', 'Y']):
            self.problem.ApplyAction(self.active_action)
            print(f"Contract {self.active_ctr.id} Successfully Updated!")
            #Reset active action and contract once addressed
            self.active_action = None
            self.active_ctr = None
        elif (ans in ['n', 'N']):
            return
        else:
            print('Please try again.')

        #Update PlanningHorizon for the planning problem and contracts
        self.problem.UpdatePlanningHorizon()

    def AdvanceState(self):
        if not self.CheckState():
            return
        self.problem.AdvancePeriod()
            
    def AnalyzeState(self):
        if not self.CheckState():
            return
        
        if (self.active_ctr is None):
            print("Please process state first")

        start = time.time_ns()
        #Generate Scenarios
        scn_count = self.problem.GenerateScenarios(self.active_ctr)
        print(f"{scn_count} Scenarios Generated")
        #Solve Them
        self.problem.SolveScenarios()
        elapsed = time.time_ns() - start
        print(f"Analysis completed successfully in {elapsed / 1000000000.0} s")
        
    def SelectAction(self):
        #Start Interactive Dialog
        selected_policy = int(input("Please select a desired policy for the client (1: Weighted, 2: Greedy, 3: Optimistic): "))
        eval_list = self.problem.GeneratePlanEvaluations(self.active_ctr, selected_policy)
        
        action = {'contract_id': self.active_ctr.id,
                  'options': None}

        while(len(eval_list) > 0) :
            negotiation = eval_list.pop(0)
            
            print("---------------------: ")
            print("Negotiation Suggestion: ")
            print("Deferral: ", negotiation.deferral_periods, "periods")
            print("Installments: ", negotiation.installments)
            print(f"Rate: {negotiation.rate}%")
            print(f"Scenario Evaluations: {negotiation.scenario_num}")
            print(f"Avg. Counterparty Acceptance Prob. : {negotiation.decision_probability:.2%}")
            print(f"Avg. Total Interest Rate Prob. : {negotiation.rate_probability:.2%} (Min: {negotiation.min_rate_probability:.2%} Max: {negotiation.max_rate_probability:.2%})")
            print(f"Avg. Total Def Date Prob. : {negotiation.def_date_probability:.2%} (Min: {negotiation.min_def_date_probability:.2%} Max: {negotiation.max_def_date_probability:.2%})")
            print(f"Avg. Total Prob. : {negotiation.probability:.2%} (Min: {negotiation.min_probability:.2%} Max: {negotiation.max_probability:.2%})")
            print(f"Avg. Objective. : {negotiation.objective:.2f}")
            print(f"Avg. Weighted Objective. : {negotiation.weighted_objective:.2f}")
            
            while(True):
                accepted = input("Did the negotiation succeed? (Y/N). Enter Q to cancel negotiation mode: ")

                if (accepted == "Y" or accepted == 'y'):
                    action["options"] = negotiation
                    self.active_action = action
                    return
                elif (accepted == "N" or accepted == 'n'):
                    break
                elif (accepted == "Q"): 
                    print("Negotiations Terminated")
                    action["options"] = ContractEvaluation()
                    action["options"].installments = 1
                    action["options"].rate = 0.0
                    action["options"].deferral_periods = 0
                    
                    self.active_action = action
                    return
                else:
                    print("Invalid Response")
                    continue
        
        #Add default options
        action["options"] = ContractEvaluation()
        action["options"].installments = 1
        action["options"].rate = 0.0
        action["options"].deferral_periods = 0
        
        self.active_action = action


if __name__ == "__main__":
    cli = CAOS_CLI()
    cli.Run()