import numpy as np

import pandas as pd

class Instance:

    def __init__(self, nome_instancia,
                       
                       #Parameters for fleet and depots
                       fleet_capacities=[],
                       number_of_depots=1,
                       vehicle_locations=[[]],
                       
                       # Parameters for demands
                       pickup_factor=1,
                       delivery_factor=1,
                       
                       # Parameter for time windows
                       tw_factor = 1 ):
        
        # Reading file data
        lines = open(nome_instancia, 'r').readlines()
        
        # Populating K attribute, for notation
        self.K = fleet_capacities
        
        # Number of vehicles at fleet
        self.m = len(self.K)
        
        # First line with number of requests
        self.n = int(lines[0].split()[0])
    
        # All other parameters of instance
        instance = [list(map(float, line.split())) for line in lines[1:]]
        
        
        # Adding pickup and depot nodes
        
        # Depots set
        depots = []
        
        # Pickups set
        pickups = []
        
        for i in range(1, number_of_depots + 1):
            
            # Depot node - 0 demand and large time windows
            depot_node = instance[i].copy()
            
            depot_node[4] = 0
            depot_node[5] = 0
            depot_node[6] = 1000*tw_factor
            
            depots.append(depot_node)
            
            # Pickup node - Not 0 demand and large time windows
            pickup_node = instance[i].copy()
            
            pickup_node[4] = pickup_node[4]*pickup_factor
            pickup_node[5] = 0
            pickup_node[6] = 1000*tw_factor
            
            pickups.append(pickup_node)
        
        # Excluding depot nodes on instance
        instance.pop(0)
        instance.pop(-1)
        
        # Excluding pickup nodes on instance
        instance = instance[self.n:]
        
        # Multiplying demands for factor
        for line in instance:
            
            line[4] = line[4]*delivery_factor
        
        # Appending pickup nodes
        instance[0:0] = pickups
        
        # Appending initial and final depots
        instance[0:0] = depots
        instance.extend(depots)
        
        # Parameters
        
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

        types = ["Depot"]*number_of_depots + ["Pickup"]*number_of_depots + ["Delivery"]*(self.n) +  ["Depot"]*number_of_depots

        df_instance = pd.DataFrame(data = [types, self.x, self.y, self.d, self.w_a, self.w_b]).transpose()

        df_instance.columns = ["type","x","y","d","w_a","w_b"]
        
        pd.set_option('display.max_rows', len(df_instance))
                    
        self.instance_data = df_instance
        
        print(self.instance_data)
        
        
        
        
        
            
            
            
            
            
            