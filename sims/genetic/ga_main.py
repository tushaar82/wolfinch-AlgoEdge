#! /usr/bin/env python
# '''
#  Wolfinch Auto trading Bot
#  Desc:  Genetic Optimizer
#  Copyright: (c) 2017-2020 Joshith Rayaroth Koderi
#  This file is part of Wolfinch.
# 
#  Wolfinch is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
# 
#  Wolfinch is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with Wolfinch.  If not, see <https://www.gnu.org/licenses/>.


import random
import numpy
from deap import algorithms
from deap import base
from deap import creator
from deap import tools
# from multiprocessing import Pool
# from contextlib import closing
from multiprocessing import Process, Manager
import json
import time
import copy

from utils import getLogger
from . import ga_ops
from . import eval_strategy

N_GEN = 1000
N_POP = 100
N_MP = 10  # num processes in parallel, bit of over-subscription is fine (# for 8 cores)
HOF_FILE = "data/ga_hof.log"
STATS_FILE = "data/ga_stats.log"
POP_DATA_FILE = "data/ga_pop.json"

# __name__ = "EA-BACKTEST"
log = getLogger (__name__)
log.setLevel (log.CRITICAL)

def ga_init (ga_config, evalfn = None):
    global N_GEN, N_POP, N_MP
    
    #init config:
#     print (ga_config)
    for ga_k, ga_v in ga_config.items():
        if ga_k == "GA_NGEN":
            N_GEN = ga_v
        if ga_k == "GA_NPOP":
            N_POP = ga_v            
        if ga_k == "GA_NMP":
            N_MP = ga_v
        if ga_k == "strategy":
            ga_strategy_name = ga_v
                    
#     print ("N_GEN: %d N_POP: %d N_MP:%d"%(N_GEN, N_POP, N_MP))
#     raise 

    #init stats
    with open (STATS_FILE, "w") as fp:
        fp.write("Wolfinch Genetica optimizer stats\n")    
        
#     ga_ops.GaTradingConfig = ga_tradecfg
    eval_strategy.config_ga_strategy(ga_strategy_name)
            
    eval_strategy.register_eval_hook (evalfn)
    
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    
    #TODO: FIXME: ideally, list should be a dict for strategy dict, working around some issues here. check ga_ops.py
    creator.create("Individual", dict, fitness=creator.FitnessMax)
    
    toolbox = base.Toolbox()
    
#     pool = Pool()
#     pool = ThreadPool(processes=1)
    
    toolbox.register("map", map)    
    
    toolbox.register("strat_gen", ga_ops.configGenerator)
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.strat_gen)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    
    toolbox.register("evaluate", ga_ops.selectOneMax)
    toolbox.register("mate", ga_ops.createOffSpring)
    toolbox.register("mutate", ga_ops.createMutant, indpb=0.05)
    toolbox.register("select", tools.selTournament, tournsize=3)

    return toolbox

def log_hof (ngen, hof):
    with open (HOF_FILE, "w") as fp:
        s = "**** hall of fame: ngen (%d) ****\n"%(ngen)
        fp.write (s)
        for e in hof:
            s = "config: %s profit: %s \n"%(str(e), str(e.fitness.values))
            fp.write(s)
            
def log_stats (stats_stream):
    s = stats_stream
    print (s)
    with open (STATS_FILE, "a") as fp:
        fp.write (stats_stream+"\n")

def eval_exec_async (eval_fn, ind_iter_o):
    # this is an ugly logic to make multiprocessing memory efficient
    # compared against mp.map,imap,imap_unordered, apply_async
    m = Manager()
    
    ind_iter = eliminate_duplicates(ind_iter_o)
    
    res_list = []
    p_num = 0
    eval_num = 0
    for ind in ind_iter:
        result_dict = m.dict()
        
        eval_num += 1
        result_dict ["res"] = 0
        print ("started eval (%d) process (%d)"%(eval_num, p_num))
        p = Process(target=eval_fn, args=(ind, result_dict))
        p.start()
        res_list.append ([True, p, result_dict, ind, None])
        p_num += 1
        
        while (p_num >= N_MP):
            print ("Max MP reached at time: %f"%(time.time()))
            time.sleep (1)
            for i in range(len(res_list)):
                if res_list[i][0] == True:
                    if not res_list[i][1].is_alive():
                        res_list[i][0] = False
                        res_list[i][4] = copy.deepcopy(res_list[i][2]["res"])
                        if type(res_list[i][4]) == int:
                            res_list[i][4] = (0.0,)
                        print ("res i(%d/%d) - %s"%(i,len(res_list), res_list[i][4]))
                        p.join()
    #                         del(res_list[i][2])                        
                        p_num -= 1
    while (p_num):
        print ("Waiting to complete all jobs time: %f"%(time.time()))
        time.sleep (1)
        for i in range(len(res_list)):
            if res_list[i][0] == True:
                if not res_list[i][1].is_alive():
                    res_list[i][0] = False
                    res_list[i][4] = copy.deepcopy(res_list[i][2]["res"])
                    if type(res_list[i][4]) == int:
                        res_list[i][4] = (0.0,)                    
                    print ("res i(%d/%d) - %s"%(i, len(res_list), res_list[i][4]))
                    p.join()
#                         del(res_list[i][2])                        
                    p_num -= 1                        
    print ("all jobs evaluated res_num(%d)"%(len(res_list)))
    fit_l = []
    for ind in ind_iter_o:
        for x in res_list:
            if x[3] == ind:
                fit_l.append(x[4])
#     fit_l = [x[4] for x in res_list]
    del(m)
    del(res_list)
    return fit_l
    
def population_persist (pop_list, ngen):
    
    with open (POP_DATA_FILE, "w") as fp:
        json.dump({"pop": pop_list, "ngen": ngen}, fp)
        
def population_load ():
    with open (POP_DATA_FILE, "r") as fp:
        data = json.load(fp)
        if data:
            return data["pop"], data["ngen"]
    return None, 0  

def eliminate_duplicates(pop_list):
    new_pop = []
    for ind in pop_list:
        if ind not in new_pop:
            new_pop.append(ind)
    return new_pop
    
def eaSimpleCustom(population, toolbox, cxpb, mutpb, sgen=1, ngen=1, stats=None,
             halloffame=None, verbose=__debug__):
    logbook = tools.Logbook()
    logbook.header = ['gen', 'nevals'] + (stats.fields if stats else [])

#     population = eliminate_duplicates(population)

    # Evaluate the individuals with an invalid fitness
    invalid_ind = [ind for ind in population if not ind.fitness.valid]
    
    fitnesses = eval_exec_async(toolbox.evaluate, invalid_ind)  
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit    

    if halloffame is not None:
        halloffame.update(population)
        log_hof (sgen, halloffame)

    record = stats.compile(population) if stats else {}
    logbook.record(gen=sgen, nevals=len(invalid_ind), **record)
    if verbose:
        log_stats(logbook.stream)        

    # Begin the generational process
    for gen in range(sgen, ngen + 1):
        # Select the next generation individuals
        offspring = toolbox.select(population, len(population))

        # Vary the pool of individuals
        offspring = algorithms.varAnd(offspring, toolbox, cxpb, mutpb)
#         offspring = eliminate_duplicates(offspring)        
        
        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        
        fitnesses = eval_exec_async(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit            
                
        # Update the hall of fame with the generated individuals
        if halloffame is not None:
            halloffame.update(offspring)
            log_hof (gen, halloffame)

        # Replace the current population by the offspring
        population[:] = offspring
        population += halloffame
        population_persist (population, gen)
        
        # Append the current generation statistics to the logbook
        record = stats.compile(population) if stats else {}
        logbook.record(gen=gen, nevals=len(invalid_ind), **record)
        if verbose:
            log_stats(logbook.stream)

    return population, logbook

#### Public APIs ####

        
def ga_main(ga_config, restart=False, evalfn = None):
    random.seed()
    
    toolbox = ga_init (ga_config, evalfn)
    
    pop = None
    gen = 1
    if restart:
        print ("restarting ga from previous run state")
        pop, gen = population_load()
    
    if pop == None:
        pop = toolbox.population(n=N_POP)
        population_persist(pop, 1)
    
#     log.debug ("pop: %s"%pop)
    
    # Numpy equality function (operators.eq) between two arrays returns the
    # equality element wise, which raises an exception in the if similar()
    # check of the hall of fame. Using a different equality function like
    # numpy.array_equal or numpy.allclose solve this issue.
    hof = tools.HallOfFame(4, similar=numpy.array_equal)
    
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)
    
    eaSimpleCustom(pop, toolbox, cxpb=0.5, mutpb=0.2, sgen=gen, ngen=N_GEN, stats=stats,
                        halloffame=hof)

    return pop, stats, hof

if __name__ == "__main__":
    ga_main()
    
    
#EOF    
