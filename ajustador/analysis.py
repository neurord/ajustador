def _scan_params_job(settings):
    return Simulation(single=True, **settings)

def scan_params(dir, IVs, **params):
    values = [np.atleast_1d(p) for p in params.values()]
    res = np.empty(tuple(p.size for p in values), dtype=object)
    jobs = [dict(zip(params, comb)) for comb in itertools.product(*values)]
    for job in jobs:
        job['dir'] = dir
        job['currents'] = IVs

    ans = exe_map()(_scan_params_job, jobs)
    res.flat = ans
    return res

def scan_missing(dir, group):
    IVs = group[0].injection
    params = group[0].params.keys()
    values, _ = convert_to_values(group, None, None, *params)
    missing = utilities.find_missing(values)
    res = np.empty((values.shape[0],), dtype=object)
    jobs = [dict(zip(params, comb)) for comb in missing]
    for job in jobs:
        job['dir'] = dir
        job['currents'] = IVs

    ans = exe_map()(_scan_params_job, jobs)
    res.flat = ans
    return res
