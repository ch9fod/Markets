
# coding: utf-8

# In[1]:

from pyomo.environ import *
m = ConcreteModel()
infinity = float('inf')


# In[2]:

# sets
m.B = RangeSet(3, doc='Buses')
m.G = RangeSet(3, doc='Generators')
m.L = RangeSet(2, doc='Loads')
m.dBlocks = RangeSet(4, doc='block bids by demand')
m.gBlocks = RangeSet(3, doc='block offers of generators')


# In[3]:

# parameters
# -------------------------------------------------------------------------------
m.X = Param(initialize=0.1, doc='Reactance of Lines')
# -------------------------------------------------------------------------------
m.cap = Param(initialize=7, doc='Capacity of Lines')
# -------------------------------------------------------------------------------
pdm_tab = {
    (1,1) : 8, (1,2) : 5, (1,3) : 5, (1,4) : 3, 
    (2,1) : 7, (2,2) : 4, (2,3) : 4, (2,4) : 3,
}
m.pdm = Param(m.L, m.dBlocks, initialize=pdm_tab, doc='MW size of block by demand')
# -------------------------------------------------------------------------------
priceDm_tab = {
    (1,1) : 22, (1,2) : 17, (1,3) : 9, (1,4) : 6,  
    (2,1) : 20, (2,2) : 18, (2,3) : 13, (2,4) : 5,
}
m.priceDm = Param(m.L, m.dBlocks, initialize=priceDm_tab, doc='price of block by demand')
# -------------------------------------------------------------------------------
pgm_tab = {
    (1,1) : 5,  (1,2) : 12, (1,3) : 13,
    (2,1) : 8,  (2,2) : 8,  (2,3) : 9, 
    (3,1) : 10, (3,2) : 10, (3,3) : 5,
}
m.pgm = Param(m.G, m.gBlocks, initialize=pgm_tab, doc='MW size of block by generator')
# -------------------------------------------------------------------------------
priceGm_tab = {
    (1,1) : 3,   (1,2) : 5,  (1,3) : 7.5,
    (2,1) : 6.5, (2,2) : 7,  (2,3) : 8, 
    (3,1) : 10,  (3,2) : 11, (3,3) : 12,
}
m.priceGm = Param(m.G, m.gBlocks, initialize=priceGm_tab, doc='price of block by generator')
# -------------------------------------------------------------------------------
m.gMax = Param(m.G, initialize={1:30 , 2:25 , 3:25}, doc='Gen capacity')
# -------------------------------------------------------------------------------
m.gMin = Param(m.G, initialize={1:5 , 2:8 , 3:10}, doc='Min gen output')
# -------------------------------------------------------------------------------
m.BP = Param(initialize=100.0, doc='Base Power')
# -------------------------------------------------------------------------------
m.d2b = Param(m.B, initialize={1:0 , 2:1 , 3:2}, doc='demands connected to bus')
# -------------------------------------------------------------------------------
m.g2b = Param(m.B, initialize={1:1 , 2:2 , 3:3}, doc='gen units connected to bus')


# In[4]:

# variables
def pd_rule(model,i,j):
    return (0, m.pdm[i,j])
m.pd = Var(m.L, m.dBlocks, domain=Reals, bounds=pd_rule, doc='cleared power block bid by demand')
# -------------------------------------------------------------------------------
def pg_rule(model,i,j):
    return (0, m.pgm[i,j])
m.pg = Var(m.G, m.gBlocks, domain=Reals, bounds=pg_rule, doc='cleared power block offered by gen')
# -------------------------------------------------------------------------------
m.u = Var(m.G, domain=Binary, doc='on/off status of gen')
# -------------------------------------------------------------------------------
m.ang = Var(m.B, doc='angles of buses')


# In[5]:

# constraints
def meet_rule(model):
    return (summation(m.pd) ==
            summation(m.pg))    
m.meet = Constraint(rule=meet_rule, doc='Blocks demand = Blocks gen')
# -------------------------------------------------------------------------------
def gens_min_rule(model,i):
    return (m.u[i]*m.gMin[i] <=
            sum(m.pg[i,j] for j in m.gBlocks))
m.gens_min = Constraint(m.G, rule=gens_min_rule, doc='Generation between limits')
# -------------------------------------------------------------------------------
def gens_max_rule(model,i):
    return (m.u[i]*m.gMax[i] >=
            sum(m.pg[i,j] for j in m.gBlocks))
m.gens_max = Constraint(m.G, rule=gens_max_rule, doc='Generation between limits')
# -------------------------------------------------------------------------------
def slack_rule(model):
    return m.ang[1] == 0
m.slackBusCon = Constraint(rule=slack_rule, doc='Angle of slack bus=0')
# -------------------------------------------------------------------------------
def flow_rule(model,i,j):
    if i == j:
        return Constraint.Skip
    return (-m.cap ,
            (m.BP/m.X)*(m.ang[i]-m.ang[j]),
            m.cap)
m.FlowCon = Constraint(m.B, m.B, rule=flow_rule, doc='Max flow')
# -------------------------------------------------------------------------------
def bus_rule(model,i):   
    if i == 1:
        return(sum(m.pg[i,j] for j in m.gBlocks) ==
               ((m.BP/m.X)*((m.ang[i]-m.ang[3]) + (m.ang[i]-m.ang[2]))))
    elif i == 2:
        return(sum(m.pg[i,j] for j in m.gBlocks) -
               sum(m.pd[i-1,j] for j in m.dBlocks) ==
               ((m.BP/m.X)*((m.ang[i]-m.ang[1]) + (m.ang[i]-m.ang[3]))))
    elif i == 3:
        return(sum(m.pg[i,j] for j in m.gBlocks) -
               sum(m.pd[i-1,j] for j in m.dBlocks) ==
               ((m.BP/m.X)*((m.ang[i]-m.ang[1]) + (m.ang[i]-m.ang[2]))))
m.BusCon = Constraint(m.B, rule=bus_rule)


# In[6]:

# objective
def s_welfare_rule(model):     
    return (sum(m.priceDm[i,j]*m.pd[i,j] for i in m.L for j in m.dBlocks) -
            sum(m.priceGm[i,j]*m.pg[i,j] for i in m.G for j in m.gBlocks))      
m.s_welfare = Objective(rule=s_welfare_rule, sense=maximize) 


# In[7]:

solver = SolverFactory("gurobi")
m.dual = Suffix(direction=Suffix.IMPORT)
results = solver.solve(m)
m.solutions.load_from(results)


# In[8]:

m.display()

