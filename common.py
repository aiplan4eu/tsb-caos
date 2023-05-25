from enum import Enum
from utilities import log

class Client:
    def __init__(self, name, a, b, neg_pref=0.5, def_open=0.5):
        self.id = -1
        self.name = name
        self.alpha = a
        self.beta = b
        self.negotiation_preference = neg_pref
        self.deferral_openess = def_open


class Payment:
    def __init__(self, c, p, a, mfd=0, mbd=0):
        self.contract = c
        self.period = p
        self.amount = a
        self.status = PaymentStatus.PENDING
        self.max_forward_deferral = mfd
        self.max_backward_deferral = mbd

    def Finalize(self):
        self.status = PaymentStatus.COMPLETED
    

        


class PaymentStatus(Enum):
    PENDING = 0
    COMPLETED = 1

class ContractStatus(Enum):
    UNDER_NEGOTIATION = 0
    NEGOTIATED = 1
    COMPLETED = 2

class ContractType(Enum):
    INBOUND = 0, 
    OUTBOUND = 1,
    NONE = 2

class ScenarioPayment:
    def __init__(self, ctr_id, t, p, a, c, mfd, mbd):
        self.contract_id = ctr_id
        self.type = t
        self.period = p
        self.amount = a
        self.client = c
        self.max_forward_deferral = mfd
        self.max_backward_deferral = mbd

class Contract:
    def __init__(self, t, c):
        self.id = -1
        self.installments = [] #Holds the individual payments of the contract
        self.amount = 0
        self.client = c
        self.fixed = False # Used to force a contract with its embedded details
        self.type = t
        self.status = ContractStatus.UNDER_NEGOTIATION
        self.PlanningHorizonEnd = -1
        self.PlanningHorizonStart = -1

    def UpdatePlanningHorizon(self):
        self.PlanningHorizonEnd = 0
        self.PlanningHorizonStart = 1000000
        
        for p in self.installments:
            self.PlanningHorizonStart = min(self.PlanningHorizonStart, p.period)
            self.PlanningHorizonEnd = max(self.PlanningHorizonEnd, p.period + 1)

    def AddPayment(self, pmnt):
        if (pmnt.contract != self):
            log("Payment - Contract mismatch", "ERROR")
        self.amount += pmnt.amount
        self.installments.append(pmnt)
    
