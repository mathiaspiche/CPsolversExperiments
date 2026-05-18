import math
import copy
import time
from userInputs import vars_start_domains, constraints, constraints_of_var, obj_func, minimize


def domain_init(var, bounds, domains):
    lb = bounds[0]
    ub = bounds[1] if len(bounds) == 2 else bounds[0]
    domains[var] = list(range(lb, ub + 1))

def evaluate_sol(values):
    args = [values[v] for v in obj_func["vars"]]
    return obj_func["func"](*args)

class Domains:
    def __init__(self, domains):
        self.domains = domains
    def remove_val(self, var, value):
        if value in self.domains[str(var)]:
            self.domains[str(var)].remove(value)
    def get_domains(self, var):
        return self.domains[str(var)]

class Node :
    def __init__(self, domains : dict):
        self.domains = copy.deepcopy(domains)

    def first_unassigned(self):
        for var, dom in self.domains.items():
            if len(dom) != 1:
                return var
        return None

    def candidate_values(self, var):
        return list(self.domains[var])

    def assign(self, var, value):
        self.domains[var] = [value]

    def is_fully_assigned(self):
        return all(len(dom) == 1 for dom in self.domains.values())

    def get_assigned(self):
        return {var: dom[0] for var, dom in self.domains.items()}

class Propagator:
    def __init__(self):
        self.best_sol = math.inf if minimize else -math.inf
        self.best_assignment = {}

    def propagate(self, domains: dict, assigned_var: str):
        if assigned_var not in constraints_of_var:
            return True
        for c_key in constraints_of_var[assigned_var]:
            c = constraints[c_key]
            needed_vars = c["vars"]

            assigned_vals = {v: domains[v][0] for v in needed_vars
                             if v in domains and len(domains[v]) == 1}
            for v in needed_vars:
                if v not in domains or len(domains[v]) == 1:
                    continue
                surviving = []
                for val in domains[v]:
                    trial = {**assigned_vals, v: val}
                    if all(k in trial for k in needed_vars):
                        args = [trial[k] for k in needed_vars]
                        if c["func"](*args):
                            surviving.append(val)
                domains[v] = surviving
                if not domains[v]:
                    return False
        return True

    def try_solution(self, assignment: dict):
        val = evaluate_sol(assignment)
        if minimize:
            if val < self.best_sol:
                print(f"New best solution: obj={val}  vars={assignment}")
                self.best_sol = val
                self.best_assignment = dict(assignment)
        else:
            if val > self.best_sol:
                print(f"New best solution: obj={val}  vars={assignment}")
                self.best_sol = val
                self.best_assignment = dict(assignment)

class Solver:
    def __init__(self, start_domains: dict):
        self.propagator = Propagator()
        self.start_domains = start_domains
    def solve(self):
        self.btrack(copy.deepcopy(self.start_domains))
        if self.propagator.best_assignment:
            print(f"\nOptimal solution: obj={self.propagator.best_sol}"
                  f"  vars={self.propagator.best_assignment}")
        else:
            print("No feasible solution found.")
        return self.propagator.best_assignment, self.propagator.best_sol

    def btrack(self, domains: dict):
        if all(len(d) == 1 for d in domains.values()):
            assignment = {v: d[0] for v, d in domains.items()}
            self.propagator.try_solution(assignment)
            return

        branch_var = next(v for v, d in domains.items() if len(d) != 1)

        for value in list(domains[branch_var]):

            saved = copy.deepcopy(domains)
            domains[branch_var] = [value]
            feasible = self.propagator.propagate(domains, branch_var)

            if feasible:
                self.btrack(domains)

            domains.clear()
            domains.update(saved)


if __name__ == "__main__":
    start_time = time.perf_counter()
    start_domains = {}
    for var, (lb, ub) in vars_start_domains.items():
        domain_init(var, [lb,ub], start_domains)
    solver = Solver(start_domains)
    best_assignment, best_val = solver.solve()
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    print(f"Executed in {elapsed:.6f} seconds")










