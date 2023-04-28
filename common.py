from enum import Enum
class Client:
    def __init__(self, name, a, b, neg_pref=0.5, def_open=0.5):
        self.id = -1
        self.name = name
        self.alpha = a
        self.beta = b
        self.negotiation_preference = neg_pref
        self.deferral_openess = def_open


class Payment:
    def __init__(self):
        self.contract = None
        self.period = 0
        self.amount = 0

class ContractStatus(Enum):
    UNDER_NEGOTATION = 0
    FINALIZED = 1

class ContractType(Enum):
    INBOUND = 0, 
    OUTBOUND = 1,
    NONE = 2

class Contract:
    def __init__(self, t, p, a, c, mfd=0, mbd=0):
        self.id = -1
        self.payments = [] #TODO: Add here the payments included in the contract
        self.client = c
        self.period = p
        self.amount = a
        self.fixed = False # Used to force a contract with its embedded details
        self.type = t
        self.status = ContractStatus.UNDER_NEGOTATION
        self.max_forward_deferral = mfd
        self.max_backward_deferral = mbd


    