import random
from math import exp


class InterestRatePrediction:
    def __init__(self):
        pass

    @staticmethod
    def FindDeferralProbability(client, p):
        #Linear Function that controls the preference of clients for deferral days
        prob = (client.deferral_openess - 1.0) * p + 1
        return min(max(prob, 0.0), 1.0)


    @staticmethod
    def FindRateProbability(client, rate):
        #TODO: Needs calibration for the range of rates
        
        #Normal distribution
        #client alpha is the standard deviation > 0.4
        #client beta is the mean value of accepted rates
        #prob = (1.0 / (client.alpha * sqrt(2.0 * pi))) * exp(-pow(rate - client.beta, 2)/(2 * client.alpha * client.alpha))
        
        #Logistic Function
        #client alpha is the growth rate [1 , 50]
        #client beta is the mean value [1 , 10]
        prob = 1.0 - (1.0 / (1.0 + exp(-client.alpha * (rate - client.beta))))
        #Clamp the result
        return min(max(prob, 0.0), 1.0)


    @staticmethod   
    def GetInterestRateForClient(c, rates):
        for r in rates:
            r_prob = InterestRatePrediction.FindRateProbability(c, r)
            sample_num = random.random()
            
            if (sample_num < r_prob):
                return 0.01 * r #Normalize rate from 0-100 to 0-1
        
        return 1.0

    def GetMaxDeferralPeriods(c, periods):
        for p in periods:
            r_prob = InterestRatePrediction.FindDeferralProbability(c, p)
            sample_num = random.random()
            
            if (sample_num < r_prob):
                return p
        return 0

    
    @staticmethod
    def IsClientNegotiating(c):
        val = random.random() < c.negotiation_preference
        return val
