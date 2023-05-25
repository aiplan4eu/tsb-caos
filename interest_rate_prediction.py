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
    def GetInterestRateForClient(c, rates, min_sample_val, max_sample_val):
        sample = min(max(random.random(), min_sample_val), max_sample_val)
        
        t_sum = sum([InterestRatePrediction.FindRateProbability(c, r) for r in rates])
        t_sum_inv = 1.0 / t_sum
        t_val = 0.0

        for r in rates:
            r_prob = InterestRatePrediction.FindRateProbability(c, r)
            t_val += r_prob * t_sum_inv
            if (sample > t_val):
                continue
            else:
                return (0.01 * r, r_prob) #Normalize rate from 0-100 to 0-1
        
        return (1.0, 1.0)

    def GetMaxDeferralPeriods(c, periods):
        sample_num = random.random()
        t_sum = sum([InterestRatePrediction.FindDeferralProbability(c, p) for p in periods])
        t_sum_inv = 1.0 / t_sum
        t_val = 0.0

        for p in periods:
            r_prob = InterestRatePrediction.FindDeferralProbability(c, p)
            
            t_val += r_prob * t_sum_inv
            if (sample_num > t_val):
                continue
            else:
                return (p, r_prob)
        
        return (0, 1.0)

    @staticmethod
    def IsClientNegotiating(c):
        val = random.random() < c.negotiation_preference
        return val
