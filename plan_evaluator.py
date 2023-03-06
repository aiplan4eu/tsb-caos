

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
        client_rate_values = {}

        min_val = 1000000000000
        max_val =0
        for rate in problem.scenarios[client.name]:
            val = 0
            for scn in problem.scenarios[client.name][rate]:
                val += scn.GetWeightedObjective()
            val /= float(len(problem.scenarios[client.name][rate]))
            
            client_rate_values[rate] = val
            min_val = min(min_val, val)
            max_val = max(max_val, val)
        
        
        print("PreNormalized Rates")
        print(client_rate_values)

        #Normalize Values
        for r in client_rate_values:
            client_rate_values[r] -= min_val
            client_rate_values[r] /= max(max_val - min_val, 1e-5)
    
        print("Normalized Rates")
        print(client_rate_values)
        
        return client_rate_values
        


    

    

