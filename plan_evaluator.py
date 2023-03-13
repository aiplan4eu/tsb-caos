

class PlanEvaluator:
    def __init__(self):
        pass


    @staticmethod
    def EvaluateClientRate(client, rate, plan_list):
        #This method returns the average weighted score from all the scenarios
        #that have been solved for this client and this particular rate

        return 0.0 
        
    @staticmethod
    def EvaluateClient(client, problem):
        
        p1_client_rate_values = {} #Policy 1 : Highest weighted score
        p2_client_rate_values = {} #Policy 2 : Highest Prob Scenario
        p3_client_rate_values = {} #Policy 3 : Highest objective Scenario
        
        p1_min_val = 1000000000000
        p2_min_val = 1000000000000
        p3_min_val = 1000000000000
        p1_max_val = 0
        p2_max_val = 0
        p3_max_val = 0
        
        for rate in problem.scenarios[client.name]:
            p1_val = 0
            p2_val = 0
            p3_val = 0
            for scn in problem.scenarios[client.name][rate]:
                p1_val += scn.GetWeightedObjective()
                p2_val += scn.probability
                p3_val += scn.GetObjective()
            
            p1_val /= float(len(problem.scenarios[client.name][rate]))
            p2_val /= float(len(problem.scenarios[client.name][rate]))
            p3_val /= float(len(problem.scenarios[client.name][rate]))
            
            p1_client_rate_values[rate] = p1_val
            p1_min_val = min(p1_min_val, p1_val)
            p1_max_val = max(p1_max_val, p1_val)

            p2_client_rate_values[rate] = p2_val
            p2_min_val = min(p2_min_val, p2_val)
            p2_max_val = max(p2_max_val, p2_val)

            p3_client_rate_values[rate] = p3_val
            p3_min_val = min(p3_min_val, p3_val)
            p3_max_val = max(p3_max_val, p3_val)
        
        
        pol1_maxValueTuple = PlanEvaluator.GetMaxValueFromDict(p1_client_rate_values)
        pol2_maxValueTuple = PlanEvaluator.GetMaxValueFromDict(p2_client_rate_values)
        pol3_maxValueTuple = PlanEvaluator.GetMaxValueFromDict(p3_client_rate_values)
        
        response = {"Policy 1" : {"Best Rate" : pol1_maxValueTuple[0], "Best Value": pol1_maxValueTuple[1], "Values" : p1_client_rate_values},
                    "Policy 2" : {"Best Rate" : pol2_maxValueTuple[0], "Best Value": pol2_maxValueTuple[1], "Values" : p2_client_rate_values},
                    "Policy 3" : {"Best Rate" : pol3_maxValueTuple[0], "Best Value": pol3_maxValueTuple[1], "Values" : p3_client_rate_values}}

        return response
    
    
    @staticmethod
    def GetMaxValueFromDict(d):
        best_key = None
        best_value = -100000000000
        for k in d:
            if (d[k] > best_value):
                best_value = d[k]
                best_key = k
        
        return (best_key, best_value)
    

