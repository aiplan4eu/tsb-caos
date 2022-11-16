import unified_planning
from  unified_planning.shortcuts import *

#Data
NumberOfClients = 3 #0,1 customers, #2 supplier
NumberOfPeriods = 3
StartBalance = 0


#Transaction Data
InboundContracts = [
    # Take 1000 from customer 0 at period 0 or 1500 on period 1
    {'id':0, 'client_id': 0, 'period': 0, 'amount': 1000, 'rate'  : 1.5  },
    {'id':1, 'client_id': 1, 'period': 1, 'amount': 500,  'rate'  : 2.0  },
    {'id':2, 'client_id': 0, 'period': 2, 'amount': 500,  'rate'  : 1.2  },
    {'id':3, 'client_id': 1, 'period': 2, 'amount': 500,  'rate'  : 1.0  }
]


OutboundContracts = [
    {'id':4, 'client_id': 2, 'period': 2, 'amount': 2000, 'rate' : 1.0},
    {'id':5, 'client_id': 2, 'period': 2, 'amount': 500,  'rate' : 1.2}
]


#Model
Period = UserType('Period')
Client = UserType('Client')
InContract = UserType('InContract')
OutContract = UserType('OutContract')

current_balance = unified_planning.model.Fluent('balance_current', IntType())
balance_at = unified_planning.model.Fluent('balance', IntType(), p=Period)
credit_line_charge = unified_planning.model.Fluent('credit_line_charge', IntType(), p=Period)
direct_inbound_data = unified_planning.model.Fluent('direct_inbound_data', IntType(), p=Period, c=InContract)

direct_outbound_data = unified_planning.model.Fluent('direct_outbound_data', IntType(), p=Period, c=OutContract)
in_contract_status = unified_planning.model.Fluent('in_contract_status', BoolType(), p=InContract)
out_contract_status = unified_planning.model.Fluent('out_contract_status', BoolType(), p=OutContract)


#Problem
problem = unified_planning.model.Problem('caos')
problem.add_fluent(balance_at, default_initial_value = 0)
problem.add_fluent(credit_line_charge, default_initial_value = 0)
problem.add_fluent(direct_inbound_data, default_initial_value = -1)
problem.add_fluent(direct_outbound_data, default_initial_value = -1)
problem.add_fluent(in_contract_status, default_initial_value = False)
problem.add_fluent(out_contract_status, default_initial_value = False)


#Initialize
clients = []
periods = []
in_contracts = []
out_contracts = []
for i in range(NumberOfPeriods):
    periods.append(unified_planning.model.Object('period_%s' % i, Period))

for i in range(NumberOfClients):
    clients.append(unified_planning.model.Object('client_%s' % i, Client))

problem.add_objects(periods)
problem.add_objects(clients)

for c in InboundContracts:
    start_p = c['period']
    amount = c['amount']
    rate = c['rate']
    contract = unified_planning.model.Object('contract_%s' % c['id'], InContract)
    in_contracts.append(contract)
    problem.add_object(contract)
    
    for p in range(NumberOfPeriods):
        if (p >= start_p):
            problem.set_initial_value(direct_inbound_data(periods[p], contract), (1 + (p - start_p)) *amount)


for c in OutboundContracts:
    start_p = c['period']
    amount = c['amount']
    rate = c['rate']
    contract = unified_planning.model.Object('contract_%s' % c['id'], OutContract)
    out_contracts.append(contract)
    problem.add_object(contract)
    
    for p in range(NumberOfPeriods):
        if (p >= start_p):
            problem.set_initial_value(direct_outbound_data(periods[p], contract), (1 + (p - start_p)) * amount)
    

#Actions

#Action A: Receive On Time
direct_recv_action = unified_planning.model.InstantaneousAction('direct_recv_action', at_period=Period, base_contract=InContract)
at_period = direct_recv_action.parameter('at_period')
rel_contract = direct_recv_action.parameter('base_contract')
direct_recv_action.add_precondition(Not(in_contract_status(rel_contract)))
direct_recv_action.add_precondition(GT(direct_inbound_data(at_period, rel_contract), 0))
direct_recv_action.add_effect(balance_at(at_period), Plus(balance_at(at_period), direct_inbound_data(at_period, rel_contract)))
direct_recv_action.add_effect(in_contract_status(rel_contract), True)
problem.add_action(direct_recv_action)

#Action C: Pay On Time
direct_pay_action = unified_planning.model.InstantaneousAction('direct_pay_action', at_period=Period, base_contract=OutContract)
at_period = direct_pay_action.parameter('at_period')
rel_contract = direct_pay_action.parameter('base_contract')
direct_pay_action.add_precondition(Not(out_contract_status(rel_contract)))
direct_pay_action.add_precondition(GT(direct_outbound_data(at_period, rel_contract), 0))
direct_pay_action.add_effect(balance_at(at_period), Minus(balance_at(at_period), direct_outbound_data(at_period, rel_contract)))
direct_pay_action.add_effect(out_contract_status(rel_contract), True)
problem.add_action(direct_pay_action)

#Action E: Credit Line Charge
credit_line_charge_action = unified_planning.model.InstantaneousAction('credit_line_charge_action', at_period=Period)
at_period = credit_line_charge_action.parameter('at_period')
credit_line_charge_action.add_precondition(LT(balance_at(at_period), 0))
credit_line_charge_action.add_effect(credit_line_charge(at_period), balance_at(at_period)) #first add to charge line
credit_line_charge_action.add_effect(balance_at(at_period), 0) #then reset the balance
problem.add_action(credit_line_charge_action)

#Initial Balance
problem.set_initial_value(balance_at(periods[0]), StartBalance)

#Objective

#Make sure that there is a non-negative balance every period
for p in periods:
    problem.add_goal(GE(balance_at(p), 0))

#Make sure that all contracts have been addressed
for c in in_contracts:
    problem.add_goal(in_contract_status(c))

for c in out_contracts:
    problem.add_goal(out_contract_status(c))

print(problem)

#Solve
with OneshotPlanner(problem_kind=problem.kind) as planner:
    result = planner.solve(problem)
    if result.status == up.engines.PlanGenerationResultStatus.SOLVED_SATISFICING:
        print("Output Schedule using", planner.name)
        for a in result.plan.actions:
            print(a)
    else:
        print("No plan found.")





