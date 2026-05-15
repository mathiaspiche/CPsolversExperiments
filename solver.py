import sys
import math

minimize = True

obj_func = {
    "vars": ("x", "y", "z"),
    "func" : lambda x,y,z : x + y + z
}

vars_start_domains = { # to be specified by user
    "x" : [2,3],
    "y" : [1,4],
    "z" : [1]
}

constraints = {
    "c1": {
        "vars": ("x", "y"),
        "func": lambda x, y: x + y <= 2
    },

    "c2": {
        "vars": ("x", "z"),
        "func": lambda x, z: x + z <= 2
    }
}

constraints_of_var = {
    "x": ["c1", "c2"],
    "y": ["c1"],
    "z": ["c2"]
}

def domain_init(self, var, lb, ub):
    self.domains[var] = list(range(lb, ub))
    return self.domains[vars]

class Domains:
    def __init__(self, domains):
        self.domains = domains
    def removeval(self, var, value):
        self.domains[f"{var}"].pop(value)
    def get_domains(self, var):
        return self.domains[f"{var}"]

class Node :
    def __init__(self, Domains):
        self.domains = Domains
        self.popped = []
    def get_target_var(self):
        return next(iter(self.domains))

    def next(self):
        target_var = next(iter(self.domains))
        target_var_dom = self.domains[f"{target_var}"]
        if len(target_var_dom) == 0 :
            return 0
        elif len(target_var_dom) == 1 :
            return 1
        else :
            self.domains[f"{target_var}"] = target_var_dom[0]
            return self.domains
    def get_domains(self):
        return self.domains

class Propagator:
    def __init__(self, constraints, target_var, assigned_values):
        self.constraints_of_var = constraints_of_var
        self.constraints = constraints
        self.target_var  = target_var
        self.node = Node(Domains)
        self.assigned_values = assigned_values
        self.best_sol = math.inf if minimize else -math.inf
        self.sol = {}

    def test_sol(self, values):
        args = []
        for v in obj_func["vars"]:
            args.append(values[v])
        value = obj_func["func"](*args)
        return value
    def propagate(self, Domains):
        domains = self.node.next()
        possible_values, valid = self.constraint_respect(domains)
        if all(len(str(k)) == 1 for k in possible_values.keys()):
            sol = self.test_sol(possible_values)
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
            self.assigned_values.target_var = domains[f"{self.target_var}"]
        else :
            Domains[f"{self.target_var}"].removeval(self.target_var, domains[f"{self.target_var}"])
            if not Domains.get_domains(f"{self.target_var}"):
                sys.exit("Unfeasible problem.")
        return possible_values, self.best_sol

    def constraint_respect(self, Domains):
        new_domains = {}
        possible_values = {}
        valid = False
        for var in Domains.keys():
            if var in self.constraints_of_var:
                for i in range(new_domains[f"{var}"]):
                    new_domains["var"] = Domains["var"][i]
                    for c in self.constraints_of_var[var]:
                        c = self.constraints[c]
                        needed_vars = c["vars"]
                        if all(v in new_domains for v in needed_vars):
                            args = [new_domains[v] for v in needed_vars]
                            if c["func"](*args):
                                possible_values[f"{var}"].append(new_domains["var"])
                                valid = True
        return possible_values, valid


class Solver:
    def __init__(self,Propagator, Node, Domains):
        self.vars = []
        self.props = []
        self.Node = Node
        self.Propagator = Propagator
        self.Domains = Domains

    def explore(self):
        domains = self.Node.get_domains()
        possible_values = self.Propagator.propagate(domains)
        while all(len(str(k)) == 1 for k in possible_values.keys()):
            domains = self.Domains
            self.Node = Node(domains)
            possible_values = self.Propagator.propagate(domains)

if __name__ == "main":
    start_domains = {}
    assigned_values = {}
    for var in vars_start_domains.keys():
        start_domains[f"{var}"] = domain_init(var, vars_start_domains[f"{var}"][0],
                                              vars_start_domains[f"{var}"][1])
    doms = Domains(start_domains)
    curr_domains = doms.domains
    # Input order heuristic
    target_var = next(iter(curr_domains))
    curr_node = Node(Domains, target_var)
    while True:
        while doms.get_domains(curr_node.domains[f"{target_var}"]):









