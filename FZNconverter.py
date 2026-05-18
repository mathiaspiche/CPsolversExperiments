import re
import sys
import os
import itertools



def clean(src: str) -> list[str]:
    """Strip comments, split on ';'."""
    src = re.sub(r'%.*', '', src)
    src = re.sub(r'\s+', ' ', src).strip()
    return [s.strip() for s in src.split(';') if s.strip()]


def parse_array(src: str, arrays: dict) -> bool:
    """array [1..N] of int: NAME = [v1,v2,...];"""
    m = re.match(r'array\s*\[.*?\]\s*of\s*int\s*:\s*(\w+)\s*(?:::\S+\s*)*=\s*\[([^\]]+)\]', src)
    if not m:
        return False
    name = m.group(1)
    vals = [v.strip() for v in m.group(2).split(',')]
    try:
        arrays[name] = [int(v) for v in vals]
    except ValueError:
        arrays[name] = vals   # variable references, not ints
    return True


def parse_var_array(src: str, var_arrays: dict) -> bool:
    """array [1..N] of var int: NAME = [v1,v2,...];"""
    m = re.match(r'array\s*\[.*?\]\s*of\s*var\s*int\s*:\s*(\w+)\s*(?:::\S+\s*)*=\s*\[([^\]]+)\]', src)
    if not m:
        return False
    name = m.group(1)
    refs = [v.strip() for v in m.group(2).split(',')]
    var_arrays[name] = refs
    return True


def extract_var_list(token: str, var_arrays: dict) -> list[str]:
    """Resolve [v1,v2,...] or ARRAY_NAME to a list of variable names."""
    token = token.strip()
    if token.startswith('['):
        return [v.strip() for v in token[1:-1].split(',')]
    elif token in var_arrays:
        return var_arrays[token]
    return [token]



def convert(fzn_path: str, out_path: str = 'userInputs.py'):
    with open(fzn_path, 'r') as f:
        src = f.read()

    stmts = clean(src)
    print(f"Total statements found: {len(stmts)}")
    print("First 5 statements:")
    for s in stmts[:5]:
        print(f"  [{s[:80]}]")
    vars_start_domains = {}   # var_name -> [lb, ub]
    arrays            = {}    # int array constants
    var_arrays        = {}    # var array aliases
    constraints       = {}
    constraints_of_var= {}
    minimize          = True
    obj_var           = None
    solve_type        = 'satisfy'
    c_index           = 1

    for stmt in stmts:
        # skip predicate declarations
        if stmt.startswith('predicate'):
            continue

        # int array constant: array [..] of int: NAME = [...]
        if re.match(r'array\s*\[.*?\]\s*of\s*int\s*:', stmt):
            parse_array(stmt, arrays)
            continue

        # var array alias: array [..] of var int: NAME = [...]
        if re.match(r'array\s*\[.*?\]\s*of\s*var\s*int\s*:', stmt):
            parse_var_array(stmt, var_arrays)
            continue

        # scalar var: var lb..ub: NAME
        m = re.match(r'var\s+(\-?\d+)\.\.(\-?\d+)\s*:\s*(\w+)', stmt)
        if m:
            lb, ub, name = int(m.group(1)), int(m.group(2)), m.group(3)
            vars_start_domains[name] = [lb, ub]
            continue

        # solve
        m = re.match(r'solve\s+(.*)', stmt)
        if m:
            rest = m.group(1).strip()
            # strip search annotations
            rest = re.sub(r'::\s*int_search\(.*', '', rest).strip()
            if rest.startswith('minimize'):
                solve_type = 'minimize'
                obj_var = rest.replace('minimize', '').strip()
            elif rest.startswith('maximize'):
                solve_type = 'maximize'
                obj_var = rest.replace('maximize', '').strip()
            else:
                solve_type = 'satisfy'
            continue

    for stmt in stmts:
        if not stmt.startswith('constraint'):
            continue
        body = stmt[len('constraint'):].strip()

        m = re.match(r'fzn_all_different_int\(\s*(\w+|\[[^\]]+\])\s*\)', body)
        if m:
            var_list = extract_var_list(m.group(1), var_arrays)
            # expand to pairwise != constraints
            for i, j in itertools.combinations(range(len(var_list)), 2):
                vi, vj = var_list[i], var_list[j]
                if vi not in vars_start_domains or vj not in vars_start_domains:
                    continue
                c_key = f"c{c_index}"
                constraints[c_key] = {
                    "vars": (vi, vj),
                    "func_str": f"lambda {vi}, {vj}: {vi} != {vj}",
                }
                constraints_of_var.setdefault(vi, []).append(c_key)
                constraints_of_var.setdefault(vj, []).append(c_key)
                c_index += 1
            continue

        m = re.match(r'int_lin_(eq|le|lt|ge|gt|ne)\(\s*(\w+|\[[^\]]+\])\s*,\s*(\w+|\[[^\]]+\])\s*,\s*(\-?\d+)\s*\)', body)
        if m:
            op_map = {'eq': '==', 'le': '<=', 'lt': '<', 'ge': '>=', 'gt': '>', 'ne': '!='}
            op       = op_map[m.group(1)]
            coeff_token = m.group(2)
            var_token   = m.group(3)
            total    = int(m.group(4))

            # resolve coefficients
            if coeff_token.startswith('['):
                coeffs = [int(v.strip()) for v in coeff_token[1:-1].split(',')]
            elif coeff_token in arrays:
                coeffs = arrays[coeff_token]
            else:
                continue

            var_list = extract_var_list(var_token, var_arrays)
            # filter to only known decision variables
            pairs = [(c, v) for c, v in zip(coeffs, var_list) if v in vars_start_domains]
            if not pairs:
                continue

            coeffs_f, vars_f = zip(*pairs)
            args    = ', '.join(vars_f)
            terms   = ' + '.join(
                f"{c}*{v}" if c != 1 else str(v)
                for c, v in zip(coeffs_f, vars_f)
            )
            c_key = f"c{c_index}"
            constraints[c_key] = {
                "vars": tuple(vars_f),
                "func_str": f"lambda {args}: {terms} {op} {total}",
            }
            for v in vars_f:
                constraints_of_var.setdefault(v, []).append(c_key)
            c_index += 1
            continue

    if obj_var and obj_var in vars_start_domains:
        obj_vars    = [obj_var]
        obj_func_str = f"lambda {obj_var}: {obj_var}"
    else:
        obj_vars    = list(vars_start_domains.keys())[:1]
        obj_func_str = f"lambda {obj_vars[0]}: 0"

    minimize_bool = (solve_type != 'maximize')

    lines = []
    lines.append(f'# Source: {os.path.basename(fzn_path)}')
    lines.append('')

    lines.append('vars_start_domains = {')
    for var, bounds in vars_start_domains.items():
        lines.append(f'    "{var}": {bounds},')
    lines.append('}')
    lines.append('')

    lines.append('constraints = {')
    for c_key, c in constraints.items():
        lines.append(f'    "{c_key}": {{')
        lines.append(f'        "vars": {c["vars"]},')
        lines.append(f'        "func": {c["func_str"]},')
        lines.append(f'    }},')
    lines.append('}')
    lines.append('')

    lines.append('constraints_of_var = {')
    for var, cs in constraints_of_var.items():
        lines.append(f'    "{var}": {cs},')
    lines.append('}')
    lines.append('')

    lines.append('obj_func = {')
    lines.append(f'    "vars": {tuple(obj_vars)},')
    lines.append(f'    "func": {obj_func_str},')
    lines.append('}')
    lines.append('')

    lines.append(f'minimize = {minimize_bool}')
    lines.append('')

    with open(out_path, 'w') as f:
        f.write('\n'.join(lines))

    print(f"Written to {out_path}")
    print(f"  {len(vars_start_domains)} variables")
    print(f"  {len(constraints)} constraints")
    print(f"  solve: {solve_type}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python fzn_to_userinputs.py <problem.fzn> [output.py]")
        sys.exit(1)
    fzn_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else 'userInputs.py'
    convert(fzn_path, out_path)