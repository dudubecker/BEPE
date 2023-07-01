import numpy as np

import pandas as pd

def pickupSitesModel(number_of_requests, number_of_pickup_sites):
    
    # Importing pyomo modules

    import pyomo.environ as pyo
    import numpy as np
    
    # Creating model
    model = pyo.ConcreteModel()
    
    # Set - Pickup sites

    model.setP = pyo.Set(initialize=range(number_of_pickup_sites))
    
    # Variable - Number of pickup nodes on pickup site "i"

    model.N = pyo.Var(model.setP, within = pyo.PositiveIntegers)
    
    model.exprobj = sum(sum(model.N[i] - model.N[j] for j in model.setP) for i in model.setP)

    model.obj = pyo.Objective(expr= model.exprobj, sense = pyo.minimize)
    
    # (1) 

    model.R1 = pyo.ConstraintList()
     
    model.R1.add(expr = sum(model.N[i] for i in model.setP) == number_of_requests)
    
    # (2) 

    model.R2 = pyo.ConstraintList()
    
    for i in model.setP:
    
        model.R2.add(expr = model.N[i] <= np.ceil(number_of_requests/number_of_pickup_sites))
        model.R2.add(expr = model.N[i] >= np.floor(number_of_requests/number_of_pickup_sites))
        
    # Solver

    TimeLimit = 20

    opt = pyo.SolverFactory('cplex', executable='C:/Program Files/IBM/ILOG/CPLEX_Studio201/cplex/bin/x64_win64/cplex')
    opt.options['TimeLimit'] = TimeLimit
    

    results = opt.solve(model)
    
    numbers_of_nodes = [int(pyo.value(model.N[i])) for i in model.setP]
    
    return numbers_of_nodes

class Instance:

    def __init__(self, nome_instancia,
                       
                       # Parameter for heterogeneous fleet
                       fleet_capacities=[],
                       
                       # Parameters for multidepot
                       multiple_depots=False,
                       number_of_depots=1,
                       vehicle_locations=[[]],
                       
                       # Parameters for split deliveries
                       split_loads=False,
                       demand_factor=1):
        

        # Reading file data
        lines = open(nome_instancia, 'r').readlines()
        
        # Populating K attribute, for notation
        self.K = fleet_capacities
        
        # Greatest capacity of vehicles on the fleet (for artificial nodes)
        self.maxQ = max(self.K)
        
        # Number of vehicles at fleet
        self.m = len(self.K)
        
        # First line with number of requests, already adding artificial requests
        self.n = int(lines[0].split()[0]) + self.m
    
        # All other parameters of instance
        instance = [list(map(float, line.split())) for line in lines[1:]]
        
        ### Modifying instance for multiple depots
        
        if multiple_depots:
            
            # Depots set
            depots = []
            
            # This function returns the number of nodes that each depot supplies
            numbers_of_nodes = pickupSitesModel(self.n - self.m, number_of_depots)
            
            index = 1
            
            for number_of_nodes in numbers_of_nodes:
                
                np.random.seed(123)
                
                instance_chunk = instance[index: index + number_of_nodes]
            
                for chunk in instance_chunk:
                    
                    # Changing instance values
                    
                    chunk[1] = instance_chunk[0][1]
                    chunk[2] = instance_chunk[0][2]
                    chunk[3] = instance_chunk[0][3]
                    
                    # Assumptions importantes: time windows dos nós de pickup se tornam iguais às do depósito!
                    
                    chunk[5] = 0
                    chunk[6] = 1000
                
                index += number_of_nodes
                
                # Guardando dados para o conjunto de depots
                depots.append(instance_chunk[0].copy())
                
                
        ### Adding artificial nodes
        
            # Excluindo depots originais
            instance.pop(0)
            instance.pop(-1)
            
            # Incluindo depots nos pickup sites
            for index, depot in enumerate(depots):
                
                depot.pop(4)
                
                depot.insert(4, 0)
                
                instance.insert(index, depot)
            
            # Incluindo nós artificiais para cada veículo em cada depósito
            
            i = 0
            
            for index_depot, vehicle_location in enumerate(vehicle_locations):
                
                for index_vehicle in vehicle_location:
                    
                    
                    artificial_pickup = depots[index_depot].copy()
                    
                    # Adicionando demanda
                    artificial_pickup[4] = self.maxQ - self.K[index_vehicle]
                    
                    
                    artificial_delivery = depots[index_depot].copy()
                    
                    # Adicionando demanda
                    artificial_delivery[4] = -(self.maxQ - self.K[index_vehicle])
                    
                    # Adicionando nós na instância
                    instance.insert(number_of_depots + i, artificial_pickup)
                    
                    instance.insert(number_of_depots - 1 + (i+1)*2 + (self.n - self.m), artificial_delivery)
                    
                    i += 1
            
            # Colocando nós finais de depot
            
            for depot in range(number_of_depots):
                
                instance.append(instance[depot])
            
            
        # Caso não seja multiple depots, é apenas necessário adicionar nós artificiais
        else:
        
            # Lista com os parâmetros para o depot
            
            depot = instance[0]
        
            # Iterando no conjunto de capacidades da frota
            
            for i, k in enumerate(self.K):
                
                artificial_pickup = depot.copy()
                
                # Adicionando demanda
                artificial_pickup[4] = self.maxQ - k
                
                instance.insert(i + 1, artificial_pickup)
                
                artificial_delivery = depot.copy()
                
                # Adicionando demanda
                artificial_delivery[4] = -(self.maxQ - k)
                
                instance.insert((i + 1)*2 + (self.n - self.m), artificial_delivery)
        
        
        # "Split loads" approach: multiplying demands on nodes and expanding number of nodes
        
        if split_loads:
            
            capacities_GCD = np.gcd.reduce(self.K)
            
            new_pickup_nodes = []
            
            new_delivery_nodes = []
            
            for index_request in range(number_of_depots + self.m, number_of_depots + self.n):
                
                pickup_node = instance[index_request]
                
                delivery_node = instance[index_request + self.n]
                
                demand = pickup_node[4]
                
                new_demand = demand * demand_factor
                
                while (new_demand > 0):
                    
                    new_pickup_node = pickup_node.copy()
                    new_pickup_node[4] = min(new_demand, capacities_GCD)
                    
                    new_pickup_nodes.append(new_pickup_node)
                    
                    new_delivery_node = delivery_node.copy()
                    new_delivery_node[4] = - min(new_demand, capacities_GCD)
                    
                    new_delivery_nodes.append(new_delivery_node)
                    
                    new_demand -= capacities_GCD
            
            # Removendo nós de pickup e delivery originais e incluindo os novos
            
            removal_indexes = list(range(number_of_depots + self.m, number_of_depots + self.n)) + list(range(number_of_depots + self.n + self.m, number_of_depots + self.n*2))
            
            instance = [instance[index] for index in range(len(instance)) if index not in removal_indexes]
            
            # Pickup nodes
            
            for i in range(number_of_depots + self.m, len(new_pickup_nodes) + number_of_depots + self.m):
                
                instance.insert(i, new_pickup_nodes[i - (number_of_depots + self.m)])
            
            # Delivery nodes
            
            j = 0
            
            for i in range(len(instance) - number_of_depots, len(instance) - number_of_depots + len(new_delivery_nodes)):
            
                instance.insert(i, new_delivery_nodes[j])    
                
                j += 1
                
            self.n = self.m + len(new_pickup_nodes)

        # Coordenada x de cada nó "i"
        self.x = [line[1] for line in instance]

        # Coordenada y de cada nó "i"
        self.y = [line[2] for line in instance]

        # Tempo de serviço de cada nó "i"
        self.s = [line[3] for line in instance]

        # Demanda de cada nó "i"
        self.d = [line[4] for line in instance]

        # Início da janela de tempo de cada nó "i"
        self.w_a = [line[5] for line in instance]

        # Fim da janela de tempo de cada nó "i"
        self.w_b = [line[6] for line in instance]

        # Tempo de viagem (igual/proporcional à distância entre cada nó): inicia-se como 0
        self.c = [[0 for i in range(len(instance))] for j in range(len(instance))]
        
        for i in range(len(instance)):
            for j in range(len(instance)):
                

                # Calculando distância euclidiana, arrendondando para 2 casas
                dist = round(((self.x[i]-self.x[j])**2 + (self.y[i]-self.y[j])**2)**(1/2),2)
                self.c[i][j] = dist
        
        # Uma das saídas do leitor são os dados para debug e para plot:

        types = ["Depot"]*number_of_depots + ["Artificial pickup"]*self.m + ["Pickup"]*(self.n - self.m) + ["Artificial delivery"]*(self.m) + ["Delivery"]*(self.n - self.m) +  ["Depot"]*number_of_depots

        df_instance = pd.DataFrame(data = [types, self.x, self.y, self.d, self.w_a, self.w_b]).transpose()

        df_instance.columns = ["type","x","y","d","w_a","w_b"]
        
        pd.set_option('display.max_rows', len(df_instance))
                    
        self.instance_data = df_instance
        
        # print(self.instance_data)
    
        
        
