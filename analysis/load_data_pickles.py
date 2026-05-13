import pickle as pickle
import os
# import analysis data
data_path = os.path.join(os.path.dirname(__file__), '..', 'data') + '/'


# N = 11 subject data
with open(data_path +'HCPS097_107_data.pkl', 'rb') as file:
    G_parameters, Gs, Hs, Ds, UHs, UGs, Ys, ds, uhs, ugs, ys, errors,Gs_base, Hs_base, Ds_base, UHs_base, UGs_base, Ys_base, ds_base, uhs_base, ugs_base, ys_base, errors_base = pickle.load(file)

subject_num = Gs.shape[0]
condition_num = Gs.shape[1]
trial_num = Gs.shape[2]


# # freqeuncy domain signal 
# print(Gs.shape) # interface transfer function (subjects x condition x trials x stim frequencies)
# print(Hs.shape) # human transfer function (subjects x condition x trials x stim frequencies)
# print(Ds.shape) # disturbances (subjects x condition x trials x number of frequencies)
# print(UHs.shape) # human inputs (subjects x condition x trials x number of frequencies)
# print(UGs.shape) # interface inputs (subjects x condition x trials x number of frequencies)
# print(Ys.shape) # output (subjects x condition x trials x number of frequencies)
# print('\n')

# # time domain signals 
# print(ds.shape) # disturbances (subjects x condition x trials x number of time points)
# print(uhs.shape) # human inputs (subjects x condition x trials x number of time points)
# print(ugs.shape) # interface inputs (subjects x condition x trials x number of time points)
# print(ys.shape) # output (subjects x condition x trials x number of time points)
# print(errors.shape) # errors (subjects x condition x trials)

trial_num_base = Gs_base.shape[1]
# print(Gs_base.shape) # interface transfer function (subjects x trials x stim frequencies)


# load interface parameters (initial interfaces)
exp_path = os.path.join(os.path.dirname(__file__), '..') + '/'
with open(exp_path + 'protocols/global_search_interfaces_2norm_cost.pkl', 'rb') as file:
    # global_search_interfaces = [G_star0, G_star1, G_star2, zero_order_Gs, first_order_Gs, second_order_Gs]
    G_star0, G_star1, G_star2, zero_order_Gs, first_order_Gs, second_order_Gs = pickle.load(file)

def get_G_find(order):
    if order == 'zero':
        return zero_order_Gs
    elif order == 'first':
        return first_order_Gs
    elif order == 'second':
        return second_order_Gs
    else:
        raise ValueError('order must be zero, first, or second')
    
def get_G_star(order): # I_init (I*)
    if order == 'zero':
        return G_star0
    elif order == 'first':
        return G_star1
    elif order == 'second':
        return G_star2
    else:
        raise ValueError('order must be zero, first, or second')