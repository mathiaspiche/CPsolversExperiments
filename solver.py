
vars_start_domains = { # to be specified by user
    "x" : [2,3],
    "y" : [1,4],
    "z" : [1]
}

constraints = {
    "c1": {
        "vars": ("x", "y"),
        "func": lambda x, y: x + y >= 2
    },

    "c2": {
        "vars": ("x", "z"),
        "func": lambda x, z: x + z >= 2
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

class Node :
    def __init__(self, domains, target_var):
        self.domains = domains
        self.target_var = target_var
        self.popped = []
    def next(self):
        target_var_dom = self.domains[f"{self.target_var}"]
        if target_var_dom == 0 :
            return 0
        elif target_var_dom == 1 :
            return 1
        else :
            self.domains[f"{self.target_var}"] = target_var_dom[0]
            return self.domains

class Propagator:
    def __init__(self, constraints, domains, target_var, assigned_values):
        self.constraints_of_var = constraints_of_var
        self.constraints = constraints
        self.target_var  = target_var
        self.domains = domains
        self.node = Node(domains, target_var)
        self.assigned_values = assigned_values

    def propagate(self):
        domains = self.node.next()
        possible_values, valid = self.constraint_respect(domains)
        if valid :
            self.assigned_values.target_var = domains[f"{self.target_var}"]
        else :
            self.domains[f"{self.target_var}"].pop()
        return possible_values

    def constraint_respect(self, domains):
        new_domains = {}
        possible_values = {}
        valid = False
        for var in domains.keys():
            if var in self.constraints_of_var:
                for i in range(new_domains[f"{var}"]):
                    new_domains["var"] = domains["var"][i]
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
    def __init__(self):
        self.vars = []
        self.props = []

    def new_int_var(self, name, lb, ub):
        v = IntVar(name, lb, ub)
        self.vars.append(v)
        return v

    def add(self, prop):
        self.props.append(prop)

if __name__ == "main":
    start_domains = {}
    assigned_values = {}
    for var in vars_start_domains.keys():
        start_domains[f"{var}"] = domain_init(var, vars_start_domains[f"{var}"][0],
                                              vars_start_domains[f"{var}"][1])




