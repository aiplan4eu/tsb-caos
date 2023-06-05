from problem import CAOSProblem
from plan_evaluator import PlanEvaluator, ContractEvaluation
import os, json

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
        menu.AddItem(Item('save', 'Save'))
        menu.AddItem(Item('load', 'Load'))
        menu.AddItem(Item('report', 'ProblemReport'))
        
        state_menu = Menu('state')
        state_menu.AddItem(Item('process', 'ProcessState'))
        state_menu.AddItem(Item('analyze', 'AnalyzeState'))
        state_menu.AddItem(Item('report', 'StateReport'))
        state_menu.AddItem(Item('select', 'SelectAction'))
        state_menu.AddItem(Item('apply', 'ApplyAction'))
        menu.AddItem(state_menu)
        
        self.active_menu = menu

    def Start(self):
        self.Greet()
        while (True):
            cmd = input("> ")
            
            if (cmd == "quit"):
                if (self.active_menu.parent == None):
                    print("Thanks for using CAOS!")
                    return    
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
    
    def ProblemReport(self):
        if (self.problem is None):
            print("No State Loaded")
            return
        self.problem.Report()

    def StateReport(self):
        print('Current Contract:', self.active_ctr)
        print('Current Action:', self.active_action)

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

    def ApplyAction(self):
        print("Current Action")
        print(self.active_action)
        
        ans = input("Apply? (y/n) ")
        if (ans in ['y', 'Y']):
            self.problem.ApplyAction(self.active_action)
        elif (ans in ['n', 'N']):
            return
        else:
            print('Please try again.')

    def ProcessState(self):
        if (self.problem is None):
            print("No State Loaded")
            return

        #Update PlanningHorizon for the planning problem and contracts
        self.problem.UpdatePlanningHorizon()

        #Get active contracts
        contract_list = self.problem.GetActiveContracts()

        if (len(contract_list) == 0):
            print("No remaining contracts for this period. Advancing to the next period")
            self.problem.AdvancePeriod()
            return self.ProcessState()
        else:
            #Ask the user to select a contract to negotiate
            print("Please select a contract to negotiate: ")
            for i in range(len(contract_list)):
                c = contract_list[i]
                print(f"{i}) Contract {c.id}")
            selected_contract_id = int(input("Selected Option: "))
        
        #Set Active Contract
        self.active_ctr = contract_list[selected_contract_id]

    def AnalyzeState(self):
        if (self.problem is None):
            print("No State Loaded")
            return
        
        if (self.active_ctr is None):
            print("Please process state first")

        #Generate Scenarios
        scn_count = self.problem.GenerateScenarios(self.active_ctr)
        print(f"{scn_count} Scenarios Generated")
        #Solve Them
        self.problem.SolveScenarios()
        print("Analysis completed successfully")
        
    def SelectAction(self):
        
        for contract_id in self.problem.scenarios:
            action = {'contract_id': contract_id,
                      'options': None}
            
            res = PlanEvaluator.EvaluateContract(contract_id, self.problem)
            results = [r.toDict() for r in res]

            #Cache results 
            f = open("report.json", "w")
            f.write(json.dumps(results))
            f.close()
            print("Analysis logged saved to report.json")

            #Start Interactive Dialog
            selected_policy = int(input("Please select a desired policy for the client (1: Weighted, 2: Greedy, 3: Optimistic): "))

            #Sort plans based on the selected policy
            
            if (selected_policy == 1):
                plan_list = sorted(res, key=lambda x: x.weighted_objective, reverse=True)
            elif (selected_policy == 2):
                plan_list = sorted(res, key=lambda x: x.objective, reverse=True)
            elif (selected_policy == 3):
                plan_list = sorted(res, key=lambda x: x.probability, reverse=True)

            plan_list = [p for p in plan_list if p.scenario_num > 0]

            while(len(plan_list) > 0) :
                negotiation = plan_list.pop(0)
                
                print("---------------------: ")
                print("Negotiation Suggestion: ")
                print("Deferral: ", negotiation.deferral_periods, "periods")
                print("Installments: ", negotiation.installments)
                print("Rate: ", negotiation.rate, "%")
                print("Avg. Decision Prob.", negotiation.decision_probability)
                print("Avg. Interest Rate Prob.", negotiation.rate_probability)
                print("Max Interest Rate Prob.", negotiation.max_rate_probability)
                print("Min Interest Rate Prob.", negotiation.min_rate_probability)
                print("Avg. Def Date Prob.", negotiation.def_date_probability)
                print("Avg. Scenario Prob.", negotiation.probability)
                print("Max Scenario Prob.", negotiation.max_probability)
                print("Min Scenario Prob.", negotiation.min_probability)
                print("Avg. Objective.", negotiation.objective)
                print("Avg. Weighted Objective.", negotiation.weighted_objective)
                
                while(True):
                    accepted = input("Did the negotiation succeed? (Y/N). Enter Q to cancel negotation mode: ")

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
            break




if __name__ == "__main__":
    cli = CAOS_CLI()
    cli.Start()