import unified_planning
from unified_planning.shortcuts import *
from unified_planning.engines import SequentialSimulator
from unified_planning.model import UPCOWState, Fluent
from typing import cast
from utilities import log


def convert_to_float(frac):
    sp = frac.split('/')
    if (len(sp) == 1):
        return float(sp[0])
    else:
        return float(sp[0])/float(sp[1])

#Classes
class PlanningProblem:
    def __init__(self):
        self.NumberOfClients = 0
        self.NumberOfPeriods = 0
        self.StartBalance = 0
        self.LoanRate = 0
        self.InboundContracts = []
        self.OutboundContracts = []
        self.solution = None


class PlanningSolution:
    def __init__(self):
        self.actions = {}
        self.objective = -1
    
    def AddAction(self, ctr, period):
        if (period not in self.actions):
            self.actions[period] = []
        self.actions[period].append(ctr)

    def Report(self):
        print("Actions:", self.actions)
        print('Objective:', self.objective)

    def CreateFromPlan(self, pp, plan):
        self.objective = pp.StartBalance
        
        period_id = 0
        for a in plan.actions:
            if a.action.name == 'direct_pay_action':
                #Find Contract id
                contract_id = int(str(a.actual_parameters[1]).split('_')[-1])
                ctr = pp.OutboundContracts[contract_id]
                self.AddAction(ctr.id, period_id)
                self.objective -= ctr.amount * (1 + (period_id - ctr.period) * ctr.rate) 
            elif a.action.name == 'direct_recv_action':
                #Find Contract id
                contract_id = int(str(a.actual_parameters[1]).split('_')[-1])
                ctr = pp.InboundContracts[contract_id]
                self.AddAction(ctr.id, period_id)
                self.objective += ctr.amount * (1 + (period_id - ctr.period) * ctr.rate)
            elif a.action.name == 'advance_period':
                period_id += 1
                if (self.objective < 0):
                    self.objective *= pp.LoanRate 
            else:
                print("Unsupported Action")

                

class Planner:
    
    @staticmethod
    def Solve(pp):
        #Model
        Period = UserType('Period')
        Client = UserType('Client')
        InContract = UserType('InContract')
        OutContract = UserType('OutContract')

        current_period = Fluent('current_period', BoolType(), p=Period)
        connected_periods = Fluent('connected_periods', BoolType(), from_period=Period, to_period=Period)
        start_balance_at = Fluent('start_balance_at', RealType(), p=Period)
        final_balance_at = Fluent('final_balance_at', RealType(), p=Period)
        #credit_line_charge = Fluent('credit_line_charge', IntType(), p=Period)
        direct_inbound_data = Fluent('direct_inbound_data', RealType(), p=Period, c=InContract)

        direct_outbound_data = Fluent('direct_outbound_data', RealType(), p=Period, c=OutContract)
        in_contract_status = Fluent('in_contract_status', BoolType(), p=InContract)
        out_contract_status = Fluent('out_contract_status', BoolType(), p=OutContract)


        #Problem
        problem = unified_planning.model.Problem('caos')
        problem.add_fluent(current_period, default_initial_value = False)
        problem.add_fluent(connected_periods, default_initial_value = False)
        problem.add_fluent(start_balance_at, default_initial_value = 0)
        problem.add_fluent(final_balance_at, default_initial_value = 0)
        
        problem.add_fluent(direct_inbound_data, default_initial_value = -1)
        problem.add_fluent(direct_outbound_data, default_initial_value = -1)
        problem.add_fluent(in_contract_status, default_initial_value = False)
        problem.add_fluent(out_contract_status, default_initial_value = False)

        #Initialize
        clients = []
        periods = []
        in_contracts = []
        out_contracts = []
        for i in range(pp.NumberOfPeriods + 1):
            periods.append(unified_planning.model.Object('period_%s' % i, Period))

        for i in range(pp.NumberOfClients):
            clients.append(unified_planning.model.Object('client_%s' % i, Client))

        problem.add_objects(periods)
        problem.add_objects(clients)

        
        #Init Period Connections
        problem.set_initial_value(current_period(periods[0]), True)
        for i in range(pp.NumberOfPeriods):
            problem.set_initial_value(connected_periods(periods[i], periods[i + 1]), True)

        for i in range(len(pp.InboundContracts)):
            c = pp.InboundContracts[i]
            start_p = c.period
            max_p = min(pp.NumberOfPeriods - 1, c.max_forward_deferral)
            min_p = max(0, c.max_backward_deferral)
            amount = c.amount
            rate = c.rate
            contract = unified_planning.model.Object('incontract_%s' % i, InContract)
            in_contracts.append(contract)
            problem.add_object(contract)
            
            for p in range(pp.NumberOfPeriods):
                if (p >= min_p and p <= max_p):
                    problem.set_initial_value(direct_inbound_data(periods[p], contract), (1.0 + rate * (p - start_p)) * amount)
        
        for i in range(len(pp.OutboundContracts)):
            c = pp.OutboundContracts[i]
            start_p = c.period
            max_p = min(pp.NumberOfPeriods - 1, c.max_forward_deferral)
            min_p = max(0, c.max_backward_deferral)
            amount = c.amount
            rate = c.rate
            contract = unified_planning.model.Object('outcontract_%s' % i, OutContract)
            out_contracts.append(contract)
            problem.add_object(contract)
            
            for p in range(pp.NumberOfPeriods):
                if (p >= min_p and p <= max_p):
                    problem.set_initial_value(direct_outbound_data(periods[p], contract), (1.0 + rate * (p - start_p)) * amount)
            
        #Initial Balance
        problem.set_initial_value(start_balance_at(periods[0]), pp.StartBalance)
        problem.set_initial_value(final_balance_at(periods[0]), pp.StartBalance)

        #Actions


        #Action A: Execute Receiving Contract
        direct_recv_action = unified_planning.model.InstantaneousAction('direct_recv_action', at_period=Period, base_contract=InContract)
        at_period = direct_recv_action.parameter('at_period')
        rel_contract = direct_recv_action.parameter('base_contract')
        direct_recv_action.add_precondition(Not(in_contract_status(rel_contract))) #Ensure that the contract has not been executed already
        direct_recv_action.add_precondition(current_period(at_period)) #Make sure the contract is executed in the current period
        direct_recv_action.add_precondition(GT(direct_inbound_data(at_period, rel_contract), 0))
        direct_recv_action.add_increase_effect(final_balance_at(at_period), direct_inbound_data(at_period, rel_contract))
        direct_recv_action.add_effect(in_contract_status(rel_contract), True)
        problem.add_action(direct_recv_action)


        #Action B: Execute Payment Contract
        direct_pay_action = unified_planning.model.InstantaneousAction('direct_pay_action', at_period=Period, base_contract=OutContract)
        at_period = direct_pay_action.parameter('at_period')
        rel_contract = direct_pay_action.parameter('base_contract')
        direct_pay_action.add_precondition(Not(out_contract_status(rel_contract))) #Ensure that the contract has not been executed already
        direct_pay_action.add_precondition(current_period(at_period)) #Make sure the contract is executed in the current period
        direct_pay_action.add_precondition(GT(direct_outbound_data(at_period, rel_contract), 0))
        direct_pay_action.add_decrease_effect(final_balance_at(at_period), direct_outbound_data(at_period, rel_contract))
        direct_pay_action.add_effect(out_contract_status(rel_contract), True)
        problem.add_action(direct_pay_action)


        #Action D: Advance Period
        period_advance_action = unified_planning.model.InstantaneousAction('advance_period', from_period=Period, to_period=Period)
        from_period = period_advance_action.parameter('from_period')
        to_period = period_advance_action.parameter('to_period')
        period_advance_action.add_precondition(connected_periods(from_period, to_period))
        period_advance_action.add_precondition(current_period(from_period))
        period_advance_action.add_effect(start_balance_at(to_period), Times(pp.LoanRate, final_balance_at(from_period)), LT(final_balance_at(from_period), 0))
        period_advance_action.add_effect(final_balance_at(to_period), Times(pp.LoanRate, final_balance_at(from_period)), LT(final_balance_at(from_period), 0))
        period_advance_action.add_effect(start_balance_at(to_period), final_balance_at(from_period), GT(final_balance_at(from_period), 0))
        period_advance_action.add_effect(final_balance_at(to_period), final_balance_at(from_period), GT(final_balance_at(from_period), 0))

        period_advance_action.add_effect(current_period(from_period), False)
        period_advance_action.add_effect(current_period(to_period), True)
        problem.add_action(period_advance_action)


        #Constraints
        
        #Make sure that there is a non-negative balance every period
        #for p in periods:
        #    problem.add_goal(GE(final_balance_at(p), 0))

        #Make sure to advance to the final period
        problem.add_goal(current_period(periods[-1]))

        #Make sure that all contracts have been addressed
        for c in in_contracts:
            problem.add_goal(in_contract_status(c))

        for c in out_contracts:
            problem.add_goal(out_contract_status(c))

        #Cost Maximization 
        problem.add_quality_metric(
            unified_planning.model.metrics.MaximizeExpressionOnFinalState(final_balance_at(periods[-1]))
        )
        
        log(problem)
        
        #Solve
        # OLD
        # with OneshotPlanner(
        #     optimality_guarantee= unified_planning.engines.PlanGenerationResultStatus.SOLVED_OPTIMALLY) as planner:
        #     result = planner.solve(problem)
        #     if result.status == up.engines.PlanGenerationResultStatus.SOLVED_SATISFICING:
        #         print("Output Schedule using", planner.name)
        #         for a in result.plan.actions:
        #             print(a)
        #     else:
        #         print("No plan found.")
        
        
        #Solve
        with OneshotPlanner(name = "enhsp-opt", ) as planner:
            planner.skip_checks = True
            result = planner.solve(problem)
            log(result.status)
            if result.status == unified_planning.engines.PlanGenerationResultStatus.SOLVED_OPTIMALLY or result.status == unified_planning.engines.PlanGenerationResultStatus.SOLVED_SATISFICING:
                log("Output Schedule using " + planner.name)
                
                #Create Solution
                sol = PlanningSolution()
                sol.CreateFromPlan(pp, result.plan)
                #sol.Report()

                '''
                NOTE: SIMULATION WORKS ONLY WITHOUT THE PLAN METRIC FUNCTIONS
                        
                print("Simulate the plan")
                simulator = SequentialSimulator(problem)
                state = UPCOWState(problem.initial_values)
                for a in result.plan.actions:
                    action_events = simulator.get_events(a.action, a.actual_parameters)
                    for e in action_events:
                        state = cast(UPCOWState, simulator.apply(e, state))
                    
                    #REPORT ACTION RESULTS
                    for p in periods:
                        if (state.get_value(current_period(p)) == problem.env.expression_manager.TRUE()):
                            print('CURRENT PERIOD', p)
                            print('Action', a)
                            print('Start Balance', convert_to_float(str(state.get_value(start_balance_at(p)).constant_value())))
                            print('Final Balance', convert_to_float(str(state.get_value(final_balance_at(p)).constant_value())))
                            break
                
                if not (simulator.is_goal(state)):
                    print("ERROR: NO GOAL STATE")
                '''
                return sol
            else:
                print("No plan found.", result.status)
                return None



    


        