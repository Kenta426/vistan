from functools import partial 
from autograd.core import getval

import autograd.numpy as np
from autograd.scipy.special import logsumexp

from utilities import (softmax_matrix, callback, 
                        callback, 
                        advi_callback, 
                        stan_model_batch_logp)

def objective_utils(params, log_p, log_q, sample_q, \
                                        M_training, num_copies_training):

    samples_shape = (num_copies_training, M_training)  

    params_stopped = getval(params)

    z = sample_q(params, samples_shape)
    
    lp = log_p(z)
    
    lq = log_q(params, z)

    lq_stopped = log_q(params_stopped, z)

    return z, lp, lq, lq_stopped

def ELBO_cf_entropy(params, log_p, log_q, sample_q, entropy_q, \
                                                M_training, num_copies_training):

    _, lp, _, _ = objective_utils(params, log_p, log_q, sample_q, \
                                                M_training, num_copies_training)

    return np.mean(lp) + entropy_q(params)

def IWELBO(params, log_p, log_q, sample_q, M_training, num_copies_training):

    _, lp, lq, _ = objective_utils(params, log_p, log_q, sample_q,\
                                                 M_training, num_copies_training)

    return np.mean(logsumexp(lp - lq, -1)) - np.log(M_training)

def IWELBO_STL(params, log_p, log_q, sample_q, M_training, num_copies_training):

    _, lp, _, lq_stopped = objective_utils(params, log_p, log_q,\
                                     sample_q, M_training, num_copies_training)

    lR = lp - lq_stopped

    return np.mean(np.sum(softmax_matrix(lR)*lR, -1))

def IWELBO_DREG(params, log_p, log_q, sample_q,\
                                 M_training, num_copies_training):

    _, lp, _, lq_stopped = objective_utils(params, log_p,\
                             log_q, sample_q, M_training, num_copies_training)

    lR = lp - lq_stopped

    return np.mean(np.sum(np.power(softmax_matrix(lR), 2)*lR, -1))

def choose_objective_eval_fn(hyper_params):

    if hyper_params['grad_estimator_type'] == "IWAE":

        objective = IWELBO 

    elif hyper_params['grad_estimator_type'] == "IWAEDREG":

        objective = IWELBO_DREG  

    elif hyper_params['grad_estimator_type'] == "IWAESTL":

        objective = IWELBO_STL  

    elif hyper_params['grad_estimator_type'] == "closed-form-entropy":

        assert (hyper_params['M_training'] == 1)
        assert ("gaussian" in hyper_params['vi_family'])

        objective = ELBO_cf_entropy  

    evaluation_fn = IWELBO

    return objective, evaluation_fn

def modify_objective_eval_fn(objective, evaluation_fn,\
                                             log_p, var_dist, hyper_params):

    m_objective = partial(objective, 
                        log_p = log_p,
                        log_q = var_dist.log_prob, 
                        sample_q = var_dist.sample,
                        M_training = hyper_params['M_training'], 
                        num_copies_training = hyper_params['num_copies_training'])

    m_evaluation_fn = partial(evaluation_fn, 
                            log_p = log_p,
                            log_q = var_dist.log_prob, 
                            sample_q = var_dist.sample,
                            M_training = hyper_params['M_training'], 
                            num_copies_training = hyper_params['num_copies_training'])

    if hyper_params['grad_estimator_type'] == "closed-form-entropy":

        m_objective = partial(m_objective, entropy_q = var_dist.entropy)

    return lambda params,t : -m_objective(params), m_evaluation_fn


def get_objective_eval_fn(log_p, var_dist, hyper_params):

    objective, evaluation_fn = choose_objective_eval_fn(hyper_params)
    
    return  modify_objective_eval_fn(objective, 
                                    evaluation_fn,
                                    log_p, 
                                    var_dist,
                                    hyper_params) 

