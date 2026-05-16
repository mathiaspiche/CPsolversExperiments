import sys
import math
from userInputs import vars_start_domains, constraints, constraints_of_var, obj_func, minimize


def domain_init(var, lb, ub, domains):
        domains[var] = list(range(lb, ub))
        return domains[vars]

def test_sol(values):
    args = []
    for v in obj_func["vars"]:
        args.append(values[v])
    value = obj_func["func"](*args)
    return value

class Domains:
    def __init__(self, domains):
        self.domains = domains
    def removeval(self, var, value):
        self.domains[f"{var}"].pop(value)
    def get_domains(self, var):
        return self.domains[f"{var}"]

class Node :
    def __init__(self, domains):
        self.domains = domains
        self.popped = []

    def next(self):
        t_var = next(iter(self.domains))
        target_var_dom = self.domains[f"{t_var}"]
        if len(target_var_dom) == 0 :
            return 0
        elif len(target_var_dom) == 1 :
            return 1
        else :
            self.domains[f"{t_var}"] = target_var_dom[0]
            return self.domains
    def get_domains(self):
        return self.domains

class Propagator:
    def __init__(self, target_var, assigned_values):
        self.constraints_of_var = constraints_of_var
        self.constraints = constraints
        self.target_var  = target_var
        self.node = Node(Domains)
        self.assigned_values = assigned_values
        self.best_sol = math.inf if minimize else -math.inf
        self.sol = {}

    def propagate(self, domains):
        doms = self.node.next()
        possible_values, valid = self.constraint_respect(doms)
        if all(len(str(k)) == 1 for k in possible_values.keys()):
            sol = test_sol(possible_values)
            if minimize :
                if sol < self.best_sol:
                    print(f"New best solution found! Variables values : {possible_values}")
                    self.best_sol = sol
                    self.sol = possible_values
            else :
                if sol > self.best_sol:
                    print(f"New best solution found! Variables values : {possible_values}")
                    self.best_sol = sol
                    self.sol = possible_values
        if valid :
            self.assigned_values.target_var = doms[f"{self.target_var}"]
        else :
            domains[f"{self.target_var}"].removeval(self.target_var, doms[f"{self.target_var}"])
            if not domains.get_domains(f"{self.target_var}"):
                sys.exit("Unfeasible problem.")
        return possible_values, self.best_sol

    def constraint_respect(self, domains):
        new_domains = {}
        possible_values = {}
        valid = False
        for v in domains.keys():
            if v in self.constraints_of_var:
                for i in range(new_domains[f"{v}"]):
                    new_domains[f"{v}"] = domains[f"{v}"][i]
                    for c in self.constraints_of_var[v]:
                        c = self.constraints[c]
                        needed_vars = c["vars"]
                        if all(v in new_domains for v in needed_vars):
                            args = [new_domains[v] for v in needed_vars]
                            if c["func"](*args):
                                possible_values[f"{v}"].append(new_domains["var"])
                                valid = True
        return possible_values, valid


class Solver:
    def __init__(self, node, t_var, domains):
        self.vars = []
        self.props = []
        self.Node = node
        self.assigned_values = {}
        self.Propagator = Propagator(target_var,self.assigned_values)
        self.Domains = domains
        self.target_var = t_var
    def explore(self):
        domains = self.Node.get_domains()
        possible_values, _ = self.Propagator.propagate(domains)
        self.Propagator.propagate(domains)
        while not all(len(str(k)) == 1 for k in possible_values.keys()):
            domains = self.Domains
            self.Node = Node(domains)
            possible_values = self.Propagator.propagate(domains)
            self.Node = self.Node.next()

if __name__ == "main":
    start_domains = {}
    assigned_values = {}
    for var in vars_start_domains.keys():
        start_domains[f"{var}"] = domain_init(var, vars_start_domains[f"{var}"][0],
                                              vars_start_domains[f"{var}"][1], start_domains)
    doms = Domains(start_domains)
    curr_domains = doms.domains
    # Input order heuristic
    target_var = next(iter(curr_domains))
    curr_node = Node(Domains)
    solver = Solver(Node,target_var, curr_domains)
    while True:
        while doms.get_domains(curr_node.domains[f"{target_var}"]):
            solver.explore()












