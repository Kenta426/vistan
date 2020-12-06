import functools
import autograd
import vi_families as families
import objectives 
import utilities as utils

# from utilities.result_helper import (save_results_parameters)

def update_hyper_params(model, hyper_params):
    hyper_params['latent_dim'] = model.zlen

    hyper_params['num_copies_training'] = (hyper_params['per_iter_sample_budget']//
                                hyper_params['M_training'])

    hyper_params['step_size'] = hyper_params['step_size_base']/\
                                (hyper_params['step_size_scale']**hyper_params['step_size_exp'])

    hyper_params['step_size'] = hyper_params['step_size']/hyper_params['latent_dim']

import interface

def inference(code, data, model_name = None, method = None):
    Model = interface.Model(code, data, model_name)




def vi_on_stan_model(model, hyper_params):
    print("Printing the Hyper-param configuration file...")
    update_hyper_params(model, hyper_params)
    print_dict(hyper_params)

    var_dist = families.get_var_dist(hyper_params)
    init_params = var_dist.initial_params()
    if hyper_params['LI_use'] == 1:
        assert "gaussian" in hyper_params['vi_family'] 
        init_params = utils.get_laplaces_init (log_p = model.logp, 
                                        z_len = hyper_params['latent_dim'], 
                                        num_epochs = hyper_params['LI_num_epochs'], 
                                        ε = hyper_params['LI_epsilon'],
                                        model_name = model_name)

    log_p = functools.partial(utils.stan_model_batch_logp, log_p = model.logp, 
                    z_len = hyper_params['latent_dim'])
    log_q = var_dist.log_prob
    sample_q = var_dist.sample

    objective, eval_function = objectives.get_objective_eval_fn(log_p, 
                                                    var_dist, 
                                                    hyper_params)

    objective_grad = autograd.grad(objective) 

    optimizer = utils.get_optimizer(hyper_params)

    callback = utils.get_callback(hyper_params)

    results, optimized_params = utils.optimization_handler(objective_grad = objective_grad,
                                                    eval_function = eval_function,
                                                    init_params = init_params,
                                                    optimizer = optimizer,
                                                    num_epochs = hyper_params['num_epochs'],
                                                    step_size = utils.get_step_size(hyper_params),
                                                    callback = functools.partial(callback,
                                                                    model = model, 
                                                                    eval_function = eval_function, 
                                                                    hyper_params = hyper_params),
                                                    hyper_params = hyper_params,
                                                    advi_use = hyper_params['advi_use'],
                                                    adapt_step_size = hyper_params['advi_adapt_step_size'])

    posterior = get_posterior(M_sampling = hyper_params['M_sampling'],
                                log_p = log_p, 
                                log_q = log_q,
                                sample_q = sample_q)

    return posterior