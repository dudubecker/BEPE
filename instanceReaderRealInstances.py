import numpy as np

import pandas as pd


class Instance:

    def __init__(self, nome_instancia,
                 
                       # Parâmetros gerais
                       avgSpeed = 1,
                       
                       # Parâmetros para abordagem de HPDPTW
                       split_loads = False,
                       demand_factor = 1,
                       
                       # Parâmetros para abordagem de SMDHPDPTW
                       model = 'HPDPTW',
                       
                       # Tentativa de acabar rotas em depósito "artificial"
                       artificial_depot = False
                       
                       ):
        
        
        # Lendo linhas do arquivo
        lines = open(nome_instancia, 'r').readlines()
        
        # Número de veículos da instância
        
        self.m = int(lines[1])
        
        # Capacidades da frota
        
        vehicles =[list(map(int, el.split())) for el in lines[2].split(',')]
        
        self.K = []

        for vehicles_set in vehicles:
            
            self.K.extend(vehicles_set)
        
        # Localizações dos veículos, segundo depots
        
        self.vehicle_locations = []
        
        v = 0
        
        for location in vehicles:
            
            index_vehicles = []
            
            for vehicle in location:
                
                
                index_vehicles.append(v)
                v += 1
                
            self.vehicle_locations.append(index_vehicles)
        
        # Maior capacidade (usada para nós artificiais)
        
        self.maxQ = max([max(el) for el in vehicles if len(el) > 0])
        
        # Número de requests (incluindo pedidos artificiais)
        
        self.n = int(lines[0]) + self.m
        
        # Computando demais parâmetros da instância
        
        # Dados numéricos (tempo de serviço, demanda, time windows)
        
        instance_numerical_data = [list(map(float, line.split()[-4:])) for line in lines[3:]]
        
        # Dados categóricos (nomes dos municípios)
        
        # Pode dar algum erro caso os tempos de serviços não tenham ".", mas por agora serve
        
        instance_categorical_data = [line.split('.')[0][:-2] for line in lines[3:]]
        
        instance = [[instance_categorical_data[index]] + instance_numerical_data[index] for index in range(len(instance_categorical_data))]
        
        depot_nodes = [node for node in instance[:self.n] if node[2] == 0]
        
        if model == 'HPDPTW':
        
            # Incluindo nós artificiais
            
            artificial_pickups = []
            
            artificial_deliveries = []
            
            for location, depot in zip(vehicles, depot_nodes):
                
                for vehicle_capacity in location:
                    
                    artificial_pickup = depot.copy()
                    artificial_pickup[2] = self.maxQ - vehicle_capacity
                    
                    artificial_pickups.append(artificial_pickup)
                    
                    
                    artificial_delivery = depot.copy()
                    artificial_delivery[2] = - (self.maxQ - vehicle_capacity)
                    
                    artificial_deliveries.append(artificial_delivery)
            
            # Incluindo nós artificiais na instância
            
            instance[len(depot_nodes) + int(lines[0]):len(depot_nodes) + int(lines[0])] = artificial_deliveries
            
            instance[len(depot_nodes):len(depot_nodes)] = artificial_pickups
            
            
            # Multiplicando nós (split)
        
            if split_loads:
                
                fleet_capacities_1D = []
                for location in vehicles:
                    
                    for vehicle_capacity in location:
                        
                        fleet_capacities_1D.append(vehicle_capacity)
                
                capacities_GCD = np.gcd.reduce(fleet_capacities_1D)
                
                new_pickup_nodes = []
                
                new_delivery_nodes = []
                
                for index_request in range(len(depot_nodes) + self.m, len(depot_nodes) + self.n):
                    
                    pickup_node = instance[index_request]
                    
                    delivery_node = instance[index_request + self.n]
                    
                    demand = pickup_node[2]
                    
                    new_demand = demand * demand_factor
                    
                    
                    integer_division = int(new_demand // capacities_GCD)
                    residue = new_demand - capacities_GCD * integer_division 
                    
                    new_pickup_node = pickup_node.copy()
                    new_delivery_node = delivery_node.copy()
                    
                    new_pickup_node[2] = capacities_GCD
                    new_delivery_node[2] = - capacities_GCD
                    
                    for i in range(integer_division):
                        
                        new_pickup_nodes.append(new_pickup_node.copy())
                        new_delivery_nodes.append(new_delivery_node.copy())
                    
                    new_pickup_node[2] = round(residue,2)
                    new_pickup_nodes.append(new_pickup_node.copy())
                    
                    new_delivery_node[2] = - round(residue,2)
                    new_delivery_nodes.append(new_delivery_node.copy())    
                        
                # Removendo nós de pickup e delivery originais e incluindo os novos
                
                removal_indexes = list(range(len(depot_nodes) + self.m, len(depot_nodes) + self.n)) + list(range(len(depot_nodes) + self.n + self.m, len(depot_nodes) + self.n*2))
                
                instance = [instance[index] for index in range(len(instance)) if index not in removal_indexes]
                
                # Incluindo novos nós:
            
                # Delivery
                
                instance[len(depot_nodes)+2*self.m:len(depot_nodes)+2*self.m] = new_delivery_nodes
                
                # Pickup
                
                instance[len(depot_nodes)+self.m:len(depot_nodes)+self.m] = new_pickup_nodes
                
                # Atualizando valor de "n"
                
                self.n = self.m + len(new_pickup_nodes)
        
        # Second approach - model
        
        if model == 'SMDHPDPTW':
            
            # Grouping pickup supply
            
            pickup_nodes = [node for node in instance if node[2] > 0]
            
            pickup_locations = [node[0] for node in depot_nodes]
            
            new_pickup_nodes = []
            
            for location in pickup_locations:
                
                new_pickup_node = [pickup_node for pickup_node in pickup_nodes if pickup_node[0] == location][0]
                
                total_supply = sum([node[2] for node in pickup_nodes if node[0] == location])
                
                new_pickup_node[2] = total_supply
                
                new_pickup_nodes.append(new_pickup_node)
            
            # Appending new pickup nodes
            
            instance = [node for node in instance if node[2] <= 0]
            
            instance[len(depot_nodes):len(depot_nodes)] = new_pickup_nodes
        

        # Parâmetros da instância
        
        if artificial_depot:
            
            instance.append(instance[0])
        
        # Municípios
        counties = [line[0] for line in instance]
        
        # Tempo de serviço de cada nó "i"
        self.s = [line[1] for line in instance]

        # Demanda de cada nó "i"
        self.d = [line[2] for line in instance]

        # Início da janela de tempo de cada nó "i"
        self.w_a = [line[3] for line in instance]

        # Fim da janela de tempo de cada nó "i"
        self.w_b = [line[4] for line in instance]
        
        # Número de depósitos
        self.number_of_depots = len(depot_nodes)
        
        # Distâncias
        
        self.c = [[0 for i in range(len(instance))] for j in range(len(instance))]
        
        df_distances = pd.read_csv('Distances.csv', index_col=0)
        
        df_coordinates = pd.read_csv('Coordinates.csv', index_col=0)
        
        for i, county_i in enumerate(counties):
            for j, county_j in enumerate(counties):
                
                # A distância de um nó "i" para um nó "j" é igual ao tempo de viagem de "i" para "j" + o tempo de serviço do nó "j"!

                if i != j:

                    dist = round(df_distances[county_i][county_j].min()/avgSpeed, 3) + self.s[j]
                    
                else:
                    
                    dist = 0

                # Se for o depot artificial
                
                if (i == len(counties) - 1) and (artificial_depot):
                    
                    self.c[i][j] = 0
                    
                elif (j == len(counties) - 1) and (artificial_depot):
                    
                    self.c[i][j] = 0
                    
                else:
                    
                    self.c[i][j] = dist
        
        # Coordinates for plot
        
        lat = []

        lon = []
        
        for county in counties:
            
            lat.append(df_coordinates.loc[county]['lat'])
            
            lon.append(df_coordinates.loc[county]['lon'])
        
        
        # Uma das saídas do leitor são os dados para debug e para plot:
            
        df_instance = pd.DataFrame(data = [counties, lat, lon, self.s, self.d, self.w_a, self.w_b]).transpose()

        df_instance.columns = ["county", "lat", "lon","s","d","w_a","w_b"]
        
        if model == 'HPDPTW':
        
            df_instance['type'] = ["Depot"]*len(depot_nodes) + ["Artificial pickup"]*self.m + ["Pickup"]*(self.n - self.m) + ["Artificial delivery"]*(self.m) + ["Delivery"]*(self.n - self.m) +  ["Depot"]*len(depot_nodes)
        
        elif model == 'SMDHPDPTW' and not artificial_depot:
            
            df_instance['type'] = ["Depot"]*len(depot_nodes) + ["Pickup"]*len(depot_nodes) + ["Delivery"]*(self.n - self.m) +  ["Depot"]*len(depot_nodes)
            
        elif model == 'SMDHPDPTW' and artificial_depot:
            
            df_instance['type'] = ["Depot"]*len(depot_nodes) + ["Pickup"]*len(depot_nodes) + ["Delivery"]*(self.n - self.m) +  ["Depot"]*(len(depot_nodes)+1)
            
        
        df_instance = df_instance[["type","county", "lat", "lon","s","d","w_a","w_b"]]
        
        pd.set_option('display.max_rows', len(df_instance))
                    
        self.instance_data = df_instance
        
        

        
