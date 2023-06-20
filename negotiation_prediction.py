import random
from math import exp
from common import ContractType
from utilities import log, MessageType



class NegotiationPrediction:
    def __init__(self):
        pass


    @staticmethod
    def FindDeferralProbability(client, ctr_type, p, start_p):
        if (ctr_type == ContractType.INBOUND):
            return NegotiationPrediction.FindDeferralProbabilityInbound(client, p - start_p)
        elif (ctr_type == ContractType.OUTBOUND):
            return NegotiationPrediction.FindDeferralProbabilityOutbound(client, p - start_p)
        else:
            log(f"Unknown contract type {ctr_type}", MessageType.ERROR)
    
    @staticmethod
    def FindDeferralProbabilityInbound(client, p):
        #p is the difference in periods from the original date
        
        #Asymptotic Function that describes the acceptance probability of a client for a specific deferral
        #TODO: In the future this can be improved to take the payment details into account
        
        if (p < -client.deferral_openness):
            prob = 0.0
        elif (p > 0):
            prob = 1.0
        elif (client.negotiation_openness > 0.65):
            prob = -client.deferral_incline / (p - client.def_in_p2) + client.def_in_b2
        else:
            prob = -client.deferral_incline / (p - client.def_in_p1) + client.def_in_b1

        return min(max(prob, 0.0), 1.0)
    
    
    @staticmethod
    def FindDeferralProbabilityOutbound(client, p):
        #p is the difference in periods from the original date
        
        #Asymptotic Function that describes the acceptance probability of a client for a specific deferral
        #TODO: In the future this can be improved to take the payment details into account
        
        if (p > client.deferral_openness):
            prob = 0.0
        elif (p < 0):
            prob = 1.0
        elif (client.negotiation_openness > 0.65):
            prob = client.deferral_incline / (p - client.def_out_p2) + client.def_out_b2
        else:
            prob = client.deferral_incline / (p - client.def_out_p1) + client.def_out_b1

        return min(max(prob, 0.0), 1.0)


    @staticmethod
    def FindRateProbability(client, ctr_type, rate):
        if (ctr_type == ContractType.INBOUND):
            return NegotiationPrediction.FindRateProbabilityInbound(client, rate)
        elif (ctr_type == ContractType.OUTBOUND):
            return NegotiationPrediction.FindRateProbabilityOutbound(client, -rate)
        else:
            log(f"Unknown contract type {ctr_type}", MessageType.ERROR)


    @staticmethod
    def FindRateProbabilityOutbound(client, rate):
        #Logistic Function
        #client alpha is the growth rate [-30, 3.91/b]
        #client beta is the mean value [-6 , -1]
        
        if (rate > 0):
            prob = 1.0
        else:
            prob = 1.0 / (1.0 + exp(client.rate_out_a * (rate - client.rate_out_b)))
        
        #Clamp the result
        return min(max(prob, 0.0), 1.0)


    @staticmethod
    def FindRateProbabilityInbound(client, rate):
        #Logistic Function
        #client alpha is the growth rate [3.91/b , 30]
        #client beta is the mean value [1 , 4]
        
        if (rate < 0):
            prob = 1.0
        else:
            prob = 1.0 / (1.0 + exp(client.rate_in_a * (rate - client.rate_in_b)))
        
        #Clamp the result
        return min(max(prob, 0.0), 1.0)


    @staticmethod   
    def GetInterestRateForClient(c, ctr_type, rates, min_sample_val):
        sample = random.random()
        
        #Filter rates to satisfy probability requirements
        eff_rates = []
        for r in rates:
            if (NegotiationPrediction.FindRateProbability(c, ctr_type, r) > min_sample_val):
                eff_rates.append(r)

        if len(eff_rates) == 0:
            log(f"Could not find any rate for client {c.name}. Recheck thresholds", MessageType.ERROR)
            for r in rates:
                print(r, NegotiationPrediction.FindRateProbability(c, ctr_type, r))
            assert(False)
        
        t_sum = sum([NegotiationPrediction.FindRateProbability(c, ctr_type, r) for r in eff_rates])
        t_sum_inv = 1.0 / t_sum
        t_val = 0.0

        for r in eff_rates:
            r_prob = NegotiationPrediction.FindRateProbability(c, ctr_type, r)
            t_val += r_prob * t_sum_inv
            if (sample > t_val):
                continue
            else:
                return (0.01 * r, r_prob) #Normalize rate from 0-100 to 0-1
        
        return (1.0, 1.0)

    def GetMaxDeferralPeriods(c, periods):
        sample_num = random.random()
        t_sum = sum([NegotiationPrediction.FindDeferralProbability(c, p) for p in periods])
        t_sum_inv = 1.0 / t_sum
        t_val = 0.0

        for p in periods:
            r_prob = NegotiationPrediction.FindDeferralProbability(c, p)
            
            t_val += r_prob * t_sum_inv
            if (sample_num > t_val):
                continue
            else:
                return (p, r_prob)
        
        return (0, 1.0)

    @staticmethod
    def IsClientNegotiating(c):
        val = random.random() < c.negotiation_openness
        return val

