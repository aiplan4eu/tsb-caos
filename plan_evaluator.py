import json
from utilities import log
from common import MessageType


class ContractEvaluation:
    def __init__(self):
        self.deferral_periods = -1
        self.rate = 0.0
        self.weighted_objective = 0.0
        self.objective = 0.0
        self.installments = 0
        self.probability = 0.0
        self.decision_probability = 0.0

    def toDict(self):
        return {
                    'Deferral Periods': self.deferral_periods,
                    'Rate': self.rate,
                    'Weighted Objective': self.weighted_objective,
                    'Objective': self.objective,
                    'Installments': self.installments,
                    'Probability': self.probability,
                    'Decision Probability': self.decision_probability
                }
    
class PlanEvaluator:
    def __init__(self):
        pass


    @staticmethod
    def EvaluateClientRate(client, rate, plan_list):
        #This method returns the average weighted score from all the scenarios
        #that have been solved for this client and this particular rate

        return 0.0 
    
    @staticmethod
    def EvaluateAlternativeScenarios(problem, scn_list, rate, def_periods, inst_num):
        p1_val = 0
        p2_val = 0
        p3_val = 0
        p4_val = 0
        
        #Accumulate policy metrics for all the scenarios of the same contract
        for scn in scn_list:
            p1_val += scn.GetWeightedObjective()
            p2_val += scn.probability
            p3_val += scn.GetObjective()
            p4_val += scn.decision_probability
        
        p1_val /= float(problem.ScenariosPerRate)
        p2_val /= float(problem.ScenariosPerRate)
        p3_val /= float(problem.ScenariosPerRate)
        p4_val /= float(problem.ScenariosPerRate)
        
        evaluation = ContractEvaluation()
        evaluation.deferral_periods = def_periods
        evaluation.installments = inst_num
        evaluation.rate = rate
        evaluation.weighted_objective = p1_val
        evaluation.probability = p2_val
        evaluation.decision_probability = p4_val
        evaluation.objective = p3_val

        return evaluation


    @staticmethod
    def EvaluateContract(ctr_id, problem):
        ctr_evaluations = [] #Use this list to store the contract evaluations
        
        for installment_num in problem.scenarios[ctr_id]:
            if (installment_num == 1): #Check for single installment scenarios (includes deferral periods)
                for def_period in problem.scenarios[ctr_id][1]:
                    for rate in problem.scenarios[ctr_id][1][def_period]:
                        evaluation = PlanEvaluator.EvaluateAlternativeScenarios(problem, 
                                                                                problem.scenarios[ctr_id][1][def_period][rate], 
                                                                                float(rate), 
                                                                                def_period, 1)
                        ctr_evaluations.append(evaluation)
            else: #Check for multiple installment scenarios (no deferral)
                for rate in problem.scenarios[ctr_id][installment_num]:
                    evaluation = PlanEvaluator.EvaluateAlternativeScenarios(problem, 
                                                                            problem.scenarios[ctr_id][installment_num][rate], 
                                                                            float(rate), 0, installment_num)
                    ctr_evaluations.append(evaluation)
        
        return ctr_evaluations
    
    

