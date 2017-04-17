
# coding: utf-8

# In[1]:

from pyomo.environ import *
model = ConcreteModel()
infinity = float('inf')


# In[2]:

# sets
model.B = RangeSet(3, doc='Buses')
model.G = RangeSet(3, doc='Generators')
model.L = RangeSet(2, doc='Loads')
model.dBlocks = RangeSet(4, doc='block bids by demand')
model.gBlocks = RangeSet(3, doc='block offers of generators')


# In[3]:

# parameters
# -------------------------------------------------------------------------------
model.X = Param(initialize=0.1, doc='Reactance of Lines')
# -------------------------------------------------------------------------------
model.cap = Param(initialize=7, doc='Capacity of Lines')
# -------------------------------------------------------------------------------
pdm_tab = {
    (1,1) : 8, (1,2) : 5, (1,3) : 5, (1,4) : 3, 
    (2,1) : 7, (2,2) : 4, (2,3) : 4, (2,4) : 3,
}
model.pdm = Param(model.L, model.dBlocks, initialize=pdm_tab, doc='MW size of block by demand')
# -------------------------------------------------------------------------------
priceDm_tab = {
    (1,1) : 22, (1,2) : 17, (1,3) : 9, (1,4) : 6,  
    (2,1) : 20, (2,2) : 18, (2,3) : 13, (2,4) : 5,
}
model.priceDm = Param(model.L, model.dBlocks, initialize=priceDm_tab, doc='price of block by demand')
# -------------------------------------------------------------------------------
pgm_tab = {
    (1,1) : 5,  (1,2) : 12, (1,3) : 13,
    (2,1) : 8,  (2,2) : 8,  (2,3) : 9, 
    (3,1) : 10, (3,2) : 10, (3,3) : 5,
}
model.pgm = Param(model.G, model.gBlocks, initialize=pgm_tab, doc='MW size of block by generator')
# -------------------------------------------------------------------------------
priceGm_tab = {
    (1,1) : 3,   (1,2) : 5,  (1,3) : 7.5,
    (2,1) : 6.5, (2,2) : 7,  (2,3) : 8, 
    (3,1) : 10,  (3,2) : 11, (3,3) : 12,
}
model.priceGm = Param(model.G, model.gBlocks, initialize=priceGm_tab, doc='price of block by generator')
# -------------------------------------------------------------------------------
model.gMax = Param(model.G, initialize={1:30 , 2:25 , 3:25}, doc='Gen capacity')
# -------------------------------------------------------------------------------
model.gMin = Param(model.G, initialize={1:5 , 2:8 , 3:10}, doc='Min gen output')


# In[4]:

# variables
def pd_rule(model,i,j):
    return (0, model.pdm[i,j])
model.pd = Var(model.L, model.dBlocks, domain=Reals, bounds=pd_rule, doc='cleared power block bid by demand')
# -------------------------------------------------------------------------------
def pg_rule(model,i,j):
    return (0, model.pgm[i,j])
model.pg = Var(model.G, model.gBlocks, domain=Reals, bounds=pg_rule, doc='cleared power block offered by gen')
# -------------------------------------------------------------------------------
model.u = Var(model.G, domain=Binary, doc='on/off status of gen')


# In[5]:

# constraints
def meet_rule(model):
    return (summation(model.pd) ==
            summation(model.pg))    
#     return (sum(model.pd[i,j] for i in model.L for j in model.dBlocks) ==
#             sum(model.pg[i,j] for i in model.G for j in model.gBlocks))
model.meet = Constraint(rule=meet_rule, doc='Blocks demand = Blocks gen')
# -------------------------------------------------------------------------------
def gens_min_rule(model,i):
    return (model.u[i]*model.gMin[i] <=
            sum(model.pg[i,j] for j in model.gBlocks))
model.gens_min = Constraint(model.G, rule=gens_min_rule, doc='Generation between limits')
# -------------------------------------------------------------------------------
def gens_max_rule(model,i):
    return (model.u[i]*model.gMax[i] >=
            sum(model.pg[i,j] for j in model.gBlocks))
model.gens_max = Constraint(model.G, rule=gens_max_rule, doc='Generation between limits')


# In[6]:

# objective
def s_welfare_rule(model):     
    return (sum(model.priceDm[i,j]*model.pd[i,j] for i in model.L for j in model.dBlocks) -
            sum(model.priceGm[i,j]*model.pg[i,j] for i in model.G for j in model.gBlocks))      
model.s_welfare = Objective(rule=s_welfare_rule, sense=maximize) 


# In[7]:

solver = SolverFactory("gurobi")
model.dual = Suffix(direction=Suffix.IMPORT)
results = solver.solve(model)
model.solutions.load_from(results)


# In[8]:

model.display()

