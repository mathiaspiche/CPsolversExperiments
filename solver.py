import math
import copy
import time
import sys
import itertools
import inspect
from collections import deque
from userInputs import vars_start_domains, constraints, constraints_of_var, obj_func, minimize


def domain_init(var, bounds, domains):
    lb = bounds[0]
    ub = bounds[1] if len(bounds) == 2 else bounds[0]
    domains[var] = list(range(lb, ub + 1))

def evaluate_sol(values):
    args = [values[v] for v in obj_func["vars"]]
    return obj_func["func"](*args)

def build_arc_queue():
    queue = deque()
    for c_key, c in constraints.items():
        vars = c["vars"]
        for i, v in enumerate(vars):
            for other in vars:
                if other != v:
                    queue.append((v, other, c_key))
    return queue

def revise(domains, xi, c_key):

    c = constraints[c_key]
    c_vars = c["vars"]
    if xi not in c_vars:
        return False

    other_vars = [v for v in c_vars if v != xi]
    revised = False

    for val in list(domains[xi]):
        other_domains = [domains[v] for v in other_vars]
        has_support = False
        for combo in itertools.product(*other_domains):
            assignment = {v: combo[i] for i, v in enumerate(other_vars)}
            assignment[xi] = val
            args = [assignment[v] for v in c_vars]
            if c["func"](*args):
                has_support = True
                break
        if not has_support:
            domains[xi].remove(val)
            revised = True

    return revised

def ac3(domains, branch_var = None):
    if branch_var not in constraints_of_var:
        return True

    queue = deque()
    for c_key in constraints_of_var[branch_var]:
        c = constraints[c_key]
        for v in c["vars"]:
            if v != branch_var:
                queue.append((v, c_key))       # no xj, just xi and constraint

    while queue:
        xi, c_key = queue.popleft()
        if revise(domains, xi, c_key):
            if not domains[xi]:
                return False
            for c_key2 in constraints_of_var[xi]:
                c = constraints[c_key2]
                for xk in c["vars"]:
                    if xk != xi:
                        queue.append((xk, c_key2))
    return True


class Propagator:
    def __init__(self):
        self.best_sol = math.inf if minimize else -math.inf
        self.best_assignment = {}

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
        if not self.propagator.best_assignment:
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

            if ac3(domains):
                self.btrack(domains)

            domains.clear()
            domains.update(saved)

def display_problem(vars_start_domains, constraints, obj_func, minimize):
    W = 50
    div = "─" * W

    direction = "min" if minimize else "max"
    src = inspect.getsource(obj_func["func"]).strip()
    func_str = src.split("lambda")[1].split(":")[-1].strip().rstrip(",")

    print("┌" + div + "┐")
    print("│" + f"  {direction}  {func_str}".ljust(W) + "│")
    print("├" + div + "┤")
    for var, bounds in vars_start_domains.items():
        lb = bounds[0]
        ub = bounds[1] if len(bounds) == 2 else bounds[0]
        print("│" + f"  {var}  ∈  [{lb}, {ub}]".ljust(W) + "│")
    print("├" + div + "┤")
    print("│" + "  s.t.".ljust(W) + "│")
    for c_key, c in constraints.items():
        src = inspect.getsource(c["func"]).strip()
        c_str = src.split("lambda")[1].split(":")[-1].strip().rstrip(",")
        print("│" + f"  {c_key}:  {c_str}".ljust(W) + "│")
    print("└" + div + "┘")

def display_sol(sol, time_elapsed, best_val, minimize):
    W = 50
    div = "─" * W

    direction = "min" if minimize else "max"

    print("┌" + div + "┐")
    print("│" + "  solution".ljust(W) + "│")
    print("├" + div + "┤")
    for var, val in sol.items():
        print("│" + f"  {var}  =  {val}".ljust(W) + "│")
    print("├" + div + "┤")
    print("│" + f"  {direction} f  =  {best_val}".ljust(W) + "│")
    print("│" + f"  time      =  {time_elapsed:.6f} s".ljust(W) + "│")
    print("└" + div + "┘")

if __name__ == "__main__":
    display_problem(vars_start_domains, constraints, obj_func, minimize)
    start_time = time.perf_counter()
    start_domains = {}
    for var, bounds in vars_start_domains.items():
        domain_init(var, bounds, start_domains)
    if not ac3(start_domains):
        sys.exit("Infeasible before search even starts.")
    solver = Solver(start_domains)
    best_assignment, best_val = solver.solve()
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    display_sol(best_assignment, elapsed, best_val, minimize)










