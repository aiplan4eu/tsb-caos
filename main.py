from planner import CAOSProblem

#Data
NumberOfClients = 3 #0, 1 customers, #2 supplier
NumberOfPeriods = 3
StartBalance = 0

#Transaction Data
InboundContracts = [
    # Take 1000 from customer 0 at period 0 or 1500 on period 1
    {'id':0, 'client_id': 0, 'period': 0, 'amount': 1000, 'rate'  : 1.5  },
    {'id':1, 'client_id': 1, 'period': 1, 'amount': 500,  'rate'  : 2.0  }
    #{'id':2, 'client_id': 0, 'period': 2, 'amount': 500,  'rate'  : 1.2  },
    #{'id':3, 'client_id': 1, 'period': 2, 'amount': 500,  'rate'  : 1.0  }
]


OutboundContracts = [
    {'id':4, 'client_id': 2, 'period': 0, 'amount': 1000, 'rate' : 1.0 },
    {'id':5, 'client_id': 2, 'period': 0, 'amount': 1500,  'rate' : 1.2 }
]


#Generate Problem
p = CAOSProblem(NumberOfClients, NumberOfPeriods, StartBalance)

for c in InboundContracts:
    p.AddInboundContract(c)

for c in OutboundContracts:
    p.AddOutboundContract(c)

#Solve the Problem
p.Solve()

