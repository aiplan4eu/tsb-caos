from enum import Enum, IntEnum
from utilities import log, MessageType
from math import sqrt
import json

class Client:
    def __init__(self, name, a1, b1, a2, b2, neg_pref=0.5, def_open=4, def_incline=1.0):
        self.id = -1
        self.name = name
        

        #Parameters a1 and b1 are used for modeling the acceptance of interest rates for INBOUND payments
        self.rate_in_a = a1
        self.rate_in_b = b1

        #Parameters a2 and b2 are used for modeling the acceptance of interest rates for OUTBOUND payments
        self.rate_out_a = a2
        self.rate_out_b = b2

        #Parameter negotiation_openness is used to predict whether or not a client is willing to enter negotiations
        self.negotiation_openness = neg_pref
        #Parameter deferral_openess and deferral_incline are used to model the acceptance of proposed deferral periods
        self.deferral_openness = def_open
        self.deferral_incline = def_incline

        #Calculate internal parameters for modeling the acceptance of deferral dates for OUTBOUND payments
        self.def_out_p1 = 0.5 * ((1 + def_open) - sqrt((1 + def_open) * (1 + def_open) + 4 * def_incline * (def_open + 1)))
        self.def_out_p2 = 0.5 * ((1 + def_open) + sqrt((1 + def_open) * (1 + def_open) + 4 * def_incline * (def_open + 1)))
        
        #Check for numerical issues
        if (abs(self.def_out_p1) < 1e-5 or abs(self.def_out_p2 < 1e-5)):
            log("Invalid deferral prediction curve", MessageType.ERROR)

        if (abs(self.def_out_p1 - def_open + 1)) < 1e-5 or abs(self.def_out_p2 - def_open + 1) < 1e-5:
            log("Invalid deferral prediction curve", MessageType.ERROR)
        

        self.def_out_b1 = 1 + (def_incline / self.def_out_p1)
        self.def_out_b2 = 1 + (def_incline / self.def_out_p2)

        
        #Calculate internal parameters for modeling the acceptance of deferral dates for INBOUND payments
        self.def_in_p1 = 0.5 * (-(1 + def_open) + sqrt((1 + def_open) * (1 + def_open) + 4 * def_incline * (def_open + 1)))
        self.def_in_p2 = 0.5 * (-(1 + def_open) - sqrt((1 + def_open) * (1 + def_open) + 4 * def_incline * (def_open + 1)))
        
        #Check for numerical issues
        if abs(self.def_in_p1) < 1e-5 or abs(self.def_in_p2) < 1e-5:
            log("Invalid deferral prediction curve", MessageType.ERROR)

        if abs(self.def_in_p1 + def_open + 1) < 1e-5 or abs(self.def_in_p2 + def_open + 1) < 1e-5:
            log("Invalid deferral prediction curve", MessageType.ERROR)
        
        self.def_in_b1 = 1 + (-def_incline / self.def_in_p1)
        self.def_in_b2 = 1 + (-def_incline / self.def_in_p2)
    
    def Report(self):
        print("Name: ", self.name)
        print("Parameters:")
        print(f"delta: {self.negotiation_openness} a1: {self.rate_in_a}, b1: {self.rate_in_b}, a2: {self.rate_out_a}, b2: {self.rate_out_b}, gamma: {self.deferral_incline}, epsilon: {self.deferral_openness}")
    


class Payment:
    def __init__(self, c, p, a):
        self.contract = c
        self.period = p
        self.amount = a
        self.status = PaymentStatus.PENDING

    def Finalize(self):
        self.status = PaymentStatus.COMPLETED
    

class PaymentStatus(IntEnum):
    PENDING = 0
    COMPLETED = 1

class ContractStatus(IntEnum):
    UNDER_NEGOTIATION = 0
    NEGOTIATED = 1
    COMPLETED = 2

class ContractType(IntEnum):
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
        self.fixed = False

class Contract:
    def __init__(self, t, c):
        self.id = -1
        self.installments = [] #Holds the individual payments of the contract
        self.amount = 0
        self.client = c
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

    def ClearPayments(self):
        self.installments.clear()
        self.amount = 0
    
    def AddPayment(self, pmnt):
        if (pmnt.contract != self):
            log("Payment - Contract mismatch", MessageType.ERROR)
        self.amount += pmnt.amount
        self.installments.append(pmnt)
    
    def IsComplete(self):
        for pmnt in self.installments:
            if (pmnt.status != PaymentStatus.COMPLETED):
                return False
        return True
