class Client:
    def __init__(self, name, a, b, neg_pref=0.5, def_open=0.5):
        self.id = -1
        self.name = name
        self.alpha = a
        self.beta = b
        self.negotiation_preference = neg_pref
        self.deferral_openess = def_open

class Contract:
    def __init__(self, t, p, a, c, mfd=0, mbd=0):
        self.id = -1
        self.client = c
        self.period = p
        self.amount = a
        self.type = t #1 for inbound, 2 for outbound
        self.max_forward_deferral = mfd
        self.max_backward_deferral = mbd


    