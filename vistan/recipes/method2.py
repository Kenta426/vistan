recipe = {

    'advi_use': False,
    'vi_family': "gaussian",

    "full_step_search": True,
    "full_step_search_scaling": True,
    'step_size_exp': 0,
    'step_size_exp_range': [0, 1, 2, 3, 4],
    'step_size_base': 0.1,
    'step_size_scale': 4.0,
    'max_iters': 100,
    'optimizer': 'adam',
    'M_iw_train': 1,
    'M_iw_sample': -1,
    'grad_estimator': "STL",
    'per_iter_sample_budget': 100,

    'LI': True,
    "LI_max_iters": 2000,
    "LI_epsilon": 1e-6,

    'evaluation_fn': "IWELBO",

    'fix_sample_budget': True,

}
