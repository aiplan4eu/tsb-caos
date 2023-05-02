import json
from utilities import log


class ContractEvaluation:
    def __init__(self):
        self.deferral_periods = -1
        self.rate = 0.0
        self.weighted_objective = 0.0
        self.objective = 0.0
        self.installments = 0
        self.probability = 0.0

    def toDict(self):
        return {
                    'Deferral Periods': self.deferral_periods,
                    'Rate': self.rate,
                    'Weighted Objective': self.weighted_objective,
                    'Objective': self.objective,
                    'Installments': self.installments,
                    'Probability': self.probability
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
        
        #Accumulate policy metrics for all the scenarios of all 
        for scn in scn_list:
            p1_val += scn.GetWeightedObjective()
            p2_val += scn.probability
            p3_val += scn.GetObjective()
        
        p1_val /= float(problem.ScenariosPerRate)
        p2_val /= float(problem.ScenariosPerRate)
        p3_val /= float(problem.ScenariosPerRate)
        
        evaluation = ContractEvaluation()
        evaluation.deferral_periods = def_periods
        evaluation.installments = inst_num
        evaluation.rate = rate
        evaluation.weighted_objective = p1_val
        evaluation.probability = p2_val
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
    

    @staticmethod
    def GetPlanWithMaxPolicy(plan_list, policy_id):
        best_plan = None
        
        if (policy_id == 1): #Weighted Objective
            best_score = -10000000
            for p in plan_list:
                if (p.weighted_objective > best_score):
                    best_plan = p
                    best_score = p.weighted_objective
        
        elif (policy_id == 2):
            best_score = -10000000
            for p in plan_list:
                if (p.objective > best_score):
                    best_plan = p
                    best_score = p.objective
        
        elif (policy_id == 3):
            best_score = -10000000
            for p in plan_list:
                if (p.probability > best_score):
                    best_plan = p
                    best_score = p.probability
        else:
            log("Incorrect Policy ID", "WARNING")
        
        return best_plan
    
    

