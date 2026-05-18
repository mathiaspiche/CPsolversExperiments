obj_func = {
    "vars": ("x", "y", "z"),
    "func" : lambda x,y,z : x + y + z
}

vars_start_domains = { # to be specified by user
    "x" : [0,3],
    "y" : [1,4],
    "z" : [1,1]
}

constraints = {
    "c1": {
        "vars": ("x", "y"),
        "func": lambda x, y: x + y <= 2
    },

    "c2": {
        "vars": ("x", "z"),
        "func": lambda x, z: x + z <= 2
    },

    "c3": {
        "vars": ("x", "y", "z"),
        "func": lambda x, y, z: x + y + z >= 2
    }

}

constraints_of_var = {
    "x": ["c1", "c2"],
    "y": ["c1"],
    "z": ["c2"]
}

minimize = True


