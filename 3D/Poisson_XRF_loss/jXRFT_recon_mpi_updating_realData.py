#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import numpy as np
import torch as tc
import xraylib as xlib
from XRF_tomography_mpi_updating_realData import reconstruct_jXRFT_tomography
from mpi4py import MPI

import warnings

comm = MPI.COMM_WORLD
n_ranks = comm.Get_size()
rank = comm.Get_rank()
warnings.filterwarnings("ignore")

#========================================================
# Set the device
#========================================================
# stdout_options = {'output_folder': recon_path, 'save_stdout': False, 'print_terminal': True}
gpu_index = rank % 2
if tc.cuda.is_available():  
    dev = tc.device('cuda:{}'.format(gpu_index))
    print("Process ", rank, "running on", dev)
    sys.stdout.flush()
else:  
    dev = "cpu"
    print("Process", rank, "running on CPU")
    sys.stdout.flush()


fl = {"K": np.array([xlib.KA1_LINE, xlib.KA2_LINE, xlib.KA3_LINE, xlib.KB1_LINE, xlib.KB2_LINE,
                 xlib.KB3_LINE, xlib.KB4_LINE, xlib.KB5_LINE]),
      "L": np.array([xlib.LA1_LINE, xlib.LA2_LINE, xlib.LB1_LINE, xlib.LB2_LINE, xlib.LB3_LINE,
                 xlib.LB4_LINE, xlib.LB5_LINE, xlib.LB6_LINE, xlib.LB7_LINE, xlib.LB9_LINE,
                 xlib.LB10_LINE, xlib.LB15_LINE, xlib.LB17_LINE]),              
      "M": np.array([xlib.MA1_LINE, xlib.MA2_LINE, xlib.MB_LINE])               
     }


params_3d_test_sample8_64_64_64 = {'recon_idx': 0,
                              'f_recon_parameters': 'recon_parameters.txt',  # The txt file that will save the reconstruction parameters
                              'dev': dev,
                              'selfAb': False,
                              'cont_from_check_point': False,
                              'use_saved_initial_guess': False,
                              'ini_kind': 'const',  # choose from 'const', 'rand' or 'randn'
                              'init_const': 0.5,
                              'ini_rand_amp': 0.1,
                              'recon_path': './data/sample_8_size_64_test_recon_woSelfAb',
                              'f_initial_guess': 'initialized_grid_concentration',
                              'f_recon_grid': 'grid_concentration',
                              'data_path': './data/sample_8_size_64_test',    # the folder where the data file is in
                              'f_XRF_data': 'test8_xrf',    # the aligned channel data file output from XRFtomo                  
                              'f_XRT_data': 'test8_xrt',         # the aligned scaler data file output from XRFtomo
                              'photon_counts_us_ic_dataset_idx':1,
                              'photon_counts_ds_ic_dataset_idx':2,
                              'XRT_ratio_dataset_idx':3,                # the index in the scalers dataset that stores the ratio of the transmitted photon counts
                              'theta_ls_dataset_idx': 'exchange/theta', # the dataset in the channel data file that stores the object angle
                              'channel_names': 'exchange/elements',     # the dataset in the channel data file that stores the cahnnel names
                              'this_aN_dic': {"Ca": 20, "Sc": 21},
                              'element_lines_roi': np.array([['Ca', 'K'], ['Ca', 'L'], ['Sc', 'K'], ['Sc', 'L']]),  # e.g. np.array([["Si", "K"], ["Ca", "K"]])
                              'n_line_group_each_element': np.array([2, 2]),
                              'solid_angle_adjustment_factor': 1.0,  # because the detector is made up of 4 sensors with spacing in between(for 2-ID-E XRF), this factor is used to account for the loss of the total amount of photon counts
                              'sample_size_n': 64, 
                              'sample_height_n': 64,
                              'sample_size_cm': 0.01,                                    
                              'probe_energy': np.array([20.0]),                            
                              'n_epoch': 40,
                              'minibatch_size': 64,
                              'b': 1.56E-5,  # the regulizer coefficient of the XRT loss
                              'lr': 1.0E-3,                          
                              'det_size_cm': 0.9, # The estimated diameter of the sensor
                              'det_from_sample_cm': 1.6, # The estimated spacing between the sample and the detector
                              'det_ds_spacing_cm': 0.4, # Set this value to the value of det_size_cm divided by a number
                              'P_folder': 'data/P_array/sample_64_64_64/detSpacing_0.4_dpts_5/backup4',              
                              'f_P': 'Intersecting_Length_64_64_64',  # The output file name has det_size_cm and det_ds_spacing_cm and det_from_sample_cm 
                              'fl_K': fl["K"], # doesn't need to change 
                              'fl_L': fl["L"], # doesn't need to change                    
                              'fl_M': fl["M"]  # doesn't need to change
                             }


params_3d_44_44_20_xtal1_roi_plus = {'recon_idx': 0,  # if start from the checkpoint, set this number to the checkpoint index you want to reconstruct from
                              'f_recon_parameters': 'recon_parameters.txt',  # The txt file that will save the reconstruction parameters
                              'dev': dev,
                              'selfAb': True,
                              'cont_from_check_point': False,
                              'use_saved_initial_guess': True,
                              'ini_kind': 'const',  # choose from 'const', 'rand' or 'randn'
                              'init_const': 0.5,
                              'ini_rand_amp': 0.1,
                              'recon_path': './data/Xtal1_align1_adjusted3_ds4_recon/Ab_T_nEl_4_nDpts_4_b1_0.1_b2_25000_lr_1E-3_ini_1',
                              'f_initial_guess': 'initialized_grid_concentration',
                              'f_recon_grid': 'grid_concentration',
                              'data_path': './data/Xtal1_align1_adjusted3_ds4',    # the folder where the data file is in
                              'f_XRF_data': 'xtal1_xrf-roi-plus',    # the aligned channel data file output from XRFtomo                  
                              'f_XRT_data': 'xtal1_scalers',         # the aligned scaler data file output from XRFtomo
                              'photon_counts_us_ic_dataset_idx':1,
                              'photon_counts_ds_ic_dataset_idx':2,
                              'XRT_ratio_dataset_idx':3,                # the index in the scalers dataset that stores the ratio of the transmitted photon counts
                              'theta_ls_dataset_idx': 'exchange/theta', # the dataset in the channel data file that stores the object angle
                              'channel_names': 'exchange/elements',     # the dataset in the channel data file that stores the cahnnel names
                              'this_aN_dic': {"Al": 13, "Si": 14, "Fe": 26, "Cu": 29},
                              'element_lines_roi': np.array([['Al', 'K'], ['Si', 'K'], ['Fe', 'K'], ['Cu', 'K']]),  # np.array([["Si, K"], ["Ca, K"]])
                              'n_line_group_each_element': np.array([1, 1, 1, 1]),
                              'solid_angle_adjustment_factor': 1.0,  # because the detector is made up of 4 sensors with spacing in between(for 2-ID-E XRF), this factor is used to account for the loss of the total amount of photon counts
                              'sample_size_n': 44, 
                              'sample_height_n': 20,
                              'sample_size_cm': 0.007,                                    
                              'probe_energy': np.array([10.0]),                             
                              'n_epoch': 200,
                              'minibatch_size': 44,
                              'b1': 0.1,  # the regulizer coefficient of the XRT loss
                              'b2': 25000.,
                              'lr': 1.0E-3,                          
                              'det_size_cm': 2.4, # The estimated diameter of the sensor
                              'det_from_sample_cm': 2.0, # The estimated spacing between the sample and the detector
                              'manual_det_coord': True,
                              'set_det_coord_cm': np.array([[0.70, -2.0, 0.70], [0.70, -2.0, -0.70], [-0.70, -2.0, 0.70], [-0.70, -2.0, -0.70]]),
                              'det_on_which_side': "negative",                                 
                              'manual_det_area': True,
                              'set_det_area_cm2': 1.68,       
                              'det_ds_spacing_cm': 2.4/2.0, # Set this value to the value of det_size_cm divided by a number
                              'P_folder': 'data/P_array/sample_44_44_20_n/Dis_2.0_detSize_2.4_manual_dpts_4',              
                              'f_P': 'Intersecting_Length_44_44_20',  # The output file name has det_size_cm and det_ds_spacing_cm and det_from_sample_cm 
                              'fl_K': fl["K"], # doesn't need to change 
                              'fl_L': fl["L"], # doesn't need to change                    
                              'fl_M': fl["M"]  # doesn't need to change
                             }


params_3d_44_44_20_xtal1_roi_plus_2 = {'recon_idx': 0,
                              'f_recon_parameters': 'recon_parameters.txt',  # The txt file that will save the reconstruction parameters
                              'dev': dev,
                              'selfAb': True,
                              'cont_from_check_point': False,
                              'use_saved_initial_guess': True,
                              'ini_kind': 'const',  # choose from 'const', 'rand' or 'randn'
                              'init_const': 0.5,
                              'ini_rand_amp': 0.1,
                              'recon_path': './data/Xtal1_align1_adjusted3_ds4_recon/Ab_T_nEl_4_nDpts_16_b1_0.1_b2_25000_lr_1E-3_ini_1',
                              'f_initial_guess': 'initialized_grid_concentration',
                              'f_recon_grid': 'grid_concentration',
                              'data_path': './data/Xtal1_align1_adjusted3_ds4',    # the folder where the data file is in
                              'f_XRF_data': 'xtal1_xrf-roi-plus',    # the aligned channel data file output from XRFtomo                  
                              'f_XRT_data': 'xtal1_scalers',         # the aligned scaler data file output from XRFtomo
                              'photon_counts_us_ic_dataset_idx':1,
                              'photon_counts_ds_ic_dataset_idx':2,
                              'XRT_ratio_dataset_idx':3,                # the index in the scalers dataset that stores the ratio of the transmitted photon counts
                              'theta_ls_dataset_idx': 'exchange/theta', # the dataset in the channel data file that stores the object angle
                              'channel_names': 'exchange/elements',     # the dataset in the channel data file that stores the cahnnel names
                              'this_aN_dic': {"Al": 13, "Si": 14, "Fe": 26, "Cu": 29},
                              'element_lines_roi': np.array([['Al', 'K'], ['Si', 'K'], ['Fe', 'K'], ['Cu', 'K']]),  # np.array([["Si, K"], ["Ca, K"]])
                              'n_line_group_each_element': np.array([1, 1, 1, 1]),
                              'solid_angle_adjustment_factor': 1.0,  # because the detector is made up of 4 sensors with spacing in between(for 2-ID-E XRF), this factor is used to account for the loss of the total amount of photon counts
                              'sample_size_n': 44, 
                              'sample_height_n': 20,
                              'sample_size_cm': 0.007,                                    
                              'probe_energy': np.array([10.0]),                             
                              'n_epoch': 200,
                              'minibatch_size': 44,
                              'b1': 1.0E-1,  # the regulizer coefficient of the XRT loss
                              'b2': 25000.,        
                              'lr': 1.0E-3,                          
                              'det_size_cm': 2.4, # The estimated diameter of the sensor
                              'det_from_sample_cm': 2.0, # The estimated spacing between the sample and the detector
                              'manual_det_coord': True,
                              'set_det_coord_cm':np.array([[0.8, -2.0, 0.8], [0.8, -2.0, 0.6], [0.6, -2.0, 0.6], [0.60, -2.0, 0.8],
                                                           [0.8, -2.0, -0.6], [0.8, -2.0, -0.8], [0.6, -2.0, -0.8], [0.6, -2.0, -0.6],
                                                           [-0.6, -2.0, -0.6], [-0.6, -2.0, -0.8], [-0.8, -2.0, -0.8], [-0.8, -2.0, -0.6],                                       
                                                           [-0.6, -2.0, 0.8], [-0.6, -2.0, 0.6], [-0.8, -2.0, 0.6], [-0.8, -2.0, 0.8]]),   
                              'manual_det_area': True,
                              'set_det_area_cm2': 1.68,  
                              'det_on_which_side': "negative",
                              'det_ds_spacing_cm': 2.4/2.0, # Set this value to the value of det_size_cm divided by a number
                              'P_folder': 'data/P_array/sample_44_44_20_n/Dis_2.0_detSize_2.4_manual_dpts_16',              
                              'f_P': 'Intersecting_Length_44_44_20',  # The output file name has det_size_cm and det_ds_spacing_cm and det_from_sample_cm 
                              'fl_K': fl["K"], # doesn't need to change 
                              'fl_L': fl["L"], # doesn't need to change                    
                              'fl_M': fl["M"]  # doesn't need to change
                             }

params_3d_44_44_20_Al_xtal1_roi_plus = {'recon_idx': 0,
                              'f_recon_parameters': 'recon_parameters.txt',  # The txt file that will save the reconstruction parameters
                              'dev': dev,
                              'selfAb': False,
                              'cont_from_check_point': False,
                              'use_saved_initial_guess': False,
                              'ini_kind': 'const',  # choose from 'const', 'rand' or 'randn'
                              'init_const': 0.5,
                              'ini_rand_amp': 0.1,
                              'recon_path': './data/Xtal1_align1_adjusted2_ds4_recon/Ab_F_nEl_1_nDpts_4_b_0.0_lr_1.0E-3/Al',
                              'f_initial_guess': 'initialized_grid_concentration',
                              'f_recon_grid': 'grid_concentration',
                              'data_path': './data/Xtal1_align1_adjusted2_ds4',    # the folder where the data file is in
                              'f_XRF_data': 'xtal1_xrf-roi-plus',    # the aligned channel data file output from XRFtomo                  
                              'f_XRT_data': 'xtal1_scalers',         # the aligned scaler data file output from XRFtomo
                              'photon_counts_us_ic_dataset_idx':1,
                              'photon_counts_ds_ic_dataset_idx':2,
                              'XRT_ratio_dataset_idx':3,                # the index in the scalers dataset that stores the ratio of the transmitted photon counts
                              'theta_ls_dataset_idx': 'exchange/theta', # the dataset in the channel data file that stores the object angle
                              'channel_names': 'exchange/elements',     # the dataset in the channel data file that stores the cahnnel names
                              'this_aN_dic': {"Al": 13},
                              'element_lines_roi': np.array([['Al', 'K']]),  # np.array([["Si, K"], ["Ca, K"]])
                              'n_line_group_each_element': np.array([1]),
                              'solid_angle_adjustment_factor': 1.0,  # because the detector is made up of 4 sensors with spacing in between(for 2-ID-E XRF), this factor is used to account for the loss of the total amount of photon counts
                              'sample_size_n': 44, 
                              'sample_height_n': 20,
                              'sample_size_cm': 0.007,                                    
                              'probe_energy': np.array([10.0]),                             
                              'n_epoch': 40,
                              'minibatch_size': 44,
                              'b': 0.0,  # the regulizer coefficient of the XRT loss
                              'lr': 1.0E-3,                          
                              'det_size_cm': 2.4, # The estimated diameter of the sensor
                              'det_from_sample_cm': 2.0, # The estimated spacing between the sample and the detector
                              'manual_det_coord': True,
                              'set_det_coord_cm': np.array([[0.70, -2.0, 0.70], [0.70, -2.0, -0.70], [-0.70, -2.0, 0.70], [-0.70, -2.0, -0.70]]), 
                              'det_on_which_side': "negative",                            
                              'manual_det_area': True,
                              'set_det_area_cm2': 1.68,                                          
                              'det_ds_spacing_cm': 2.4/2.0, # Set this value to the value of det_size_cm divided by a number
                              'P_folder': 'data/P_array/sample_44_44_20_n/Dis_2.0_detSize_2.4_manual_dpts_4',              
                              'f_P': 'Intersecting_Length_44_44_20',  # The output file name has det_size_cm and det_ds_spacing_cm and det_from_sample_cm 
                              'fl_K': fl["K"], # doesn't need to change 
                              'fl_L': fl["L"], # doesn't need to change                    
                              'fl_M': fl["M"]  # doesn't need to change
                             }

params_3d_44_44_20_Si_xtal1_roi_plus = {'recon_idx': 0,
                              'f_recon_parameters': 'recon_parameters.txt',  # The txt file that will save the reconstruction parameters
                              'dev': dev,
                              'selfAb': False,
                              'cont_from_check_point': False,
                              'use_saved_initial_guess': False,
                              'ini_kind': 'const',  # choose from 'const', 'rand' or 'randn'
                              'init_const': 0.5,
                              'ini_rand_amp': 0.1,
                              'recon_path': './data/Xtal1_align1_adjusted2_ds4_recon/Ab_F_nEl_1_nDpts_4_b_0.0_lr_1E-3_test/Si',
                              'f_initial_guess': 'initialized_grid_concentration',
                              'f_recon_grid': 'grid_concentration',
                              'data_path': './data/Xtal1_align1_adjusted2_ds4',    # the folder where the data file is in
                              'f_XRF_data': 'xtal1_xrf-roi-plus',    # the aligned channel data file output from XRFtomo                  
                              'f_XRT_data': 'xtal1_scalers',         # the aligned scaler data file output from XRFtomo
                              'photon_counts_us_ic_dataset_idx':1,
                              'photon_counts_ds_ic_dataset_idx':2,
                              'XRT_ratio_dataset_idx':3,                # the index in the scalers dataset that stores the ratio of the transmitted photon counts
                              'theta_ls_dataset_idx': 'exchange/theta', # the dataset in the channel data file that stores the object angle
                              'channel_names': 'exchange/elements',     # the dataset in the channel data file that stores the cahnnel names
                              'this_aN_dic': {"Si": 14},
                              'element_lines_roi': np.array([['Si', 'K']]),  # np.array([["Si, K"], ["Ca, K"]])
                              'n_line_group_each_element': np.array([1]),
                              'solid_angle_adjustment_factor': 0.5,  # because the detector is made up of 4 sensors with spacing in between(for 2-ID-E XRF), this factor is used to account for the loss of the total amount of photon counts
                              'sample_size_n': 44, 
                              'sample_height_n': 20,
                              'sample_size_cm': 0.007,                                    
                              'probe_energy': np.array([10.0]),                             
                              'n_epoch': 40,
                              'minibatch_size': 44,
                              'b': 0.0,  # the regulizer coefficient of the XRT loss
                              'lr': 1.0E-3,                              
                              'det_size_cm': 2.4, # The estimated diameter of the sensor
                              'det_from_sample_cm': 2.0, # The estimated spacing between the sample and the detector
                              'manual_det_coord': True,
                              'set_det_coord_cm': np.array([[0.70, -2.0, 0.70], [0.70, -2.0, -0.70], [-0.70, -2.0, 0.70], [-0.70, -2.0, -0.70]]), 
                              'det_on_which_side': "negative",                            
                              'manual_det_area': True,
                              'set_det_area_cm2': 1.68,                                          
                              'det_ds_spacing_cm': 2.4/2.0, # Set this value to the value of det_size_cm divided by a number
                              'P_folder': 'data/P_array/sample_44_44_20_n/Dis_2.0_detSize_2.4_manual_dpts_4',              
                              'f_P': 'Intersecting_Length_44_44_20',  # The output file name has det_size_cm and det_ds_spacing_cm and det_from_sample_cm 
                              'fl_K': fl["K"], # doesn't need to change 
                              'fl_L': fl["L"], # doesn't need to change                    
                              'fl_M': fl["M"]  # doesn't need to change
                             }

params_3d_44_44_20_Fe_xtal1_roi_plus = {'recon_idx': 0,
                              'f_recon_parameters': 'recon_parameters.txt',  # The txt file that will save the reconstruction parameters
                              'dev': dev,
                              'selfAb': False,
                              'cont_from_check_point': False,
                              'use_saved_initial_guess': False,
                              'ini_kind': 'const',  # choose from 'const', 'rand' or 'randn'
                              'init_const': 0.5,
                              'ini_rand_amp': 0.1,
                              'recon_path': './data/Xtal1_align1_adjusted1_ds4_recon/Ab_F_nEl_1_nDpts_4_b_0.0_lr_1E-3/Fe',
                              'f_initial_guess': 'initialized_grid_concentration',
                              'f_recon_grid': 'grid_concentration',
                              'data_path': './data/Xtal1_align1_adjusted1_ds4',    # the folder where the data file is in
                              'f_XRF_data': 'xtal1_xrf-roi-plus',    # the aligned channel data file output from XRFtomo                  
                              'f_XRT_data': 'xtal1_scalers',         # the aligned scaler data file output from XRFtomo
                              'photon_counts_us_ic_dataset_idx':1,
                              'photon_counts_ds_ic_dataset_idx':2,
                              'XRT_ratio_dataset_idx':3,                # the index in the scalers dataset that stores the ratio of the transmitted photon counts
                              'theta_ls_dataset_idx': 'exchange/theta', # the dataset in the channel data file that stores the object angle
                              'channel_names': 'exchange/elements',     # the dataset in the channel data file that stores the cahnnel names
                              'this_aN_dic': {"Fe": 26},
                              'element_lines_roi': np.array([['Fe', 'K']]),  # np.array([["Si, K"], ["Ca, K"]])
                              'n_line_group_each_element': np.array([1]),
                              'solid_angle_adjustment_factor': 0.5,  # because the detector is made up of 4 sensors with spacing in between(for 2-ID-E XRF), this factor is used to account for the loss of the total amount of photon counts
                              'sample_size_n': 44, 
                              'sample_height_n': 20,
                              'sample_size_cm': 0.007,                                    
                              'probe_energy': np.array([10.0]),                             
                              'n_epoch': 40,
                              'minibatch_size': 44,
                              'b': 0.0E-4,  # the regulizer coefficient of the XRT loss
                              'lr': 1.0E-3,                             
                              'det_size_cm': 2.4, # The estimated diameter of the sensor
                              'det_from_sample_cm': 2.0, # The estimated spacing between the sample and the detector
                              'manual_det_coord': True,
                              'set_det_coord_cm': np.array([[0.70, -2.0, 0.70], [0.70, -2.0, -0.70], [-0.70, -2.0, 0.70], [-0.70, -2.0, -0.70]]), 
                              'det_on_which_side': "negative",                            
                              'manual_det_area': True,
                              'set_det_area_cm2': 1.68,                                          
                              'det_ds_spacing_cm': 2.4/2.0, # Set this value to the value of det_size_cm divided by a number
                              'P_folder': 'data/P_array/sample_44_44_20_n/Dis_2.0_detSize_2.4_manual_dpts_4',              
                              'f_P': 'Intersecting_Length_44_44_20',  # The output file name has det_size_cm and det_ds_spacing_cm and det_from_sample_cm 
                              'fl_K': fl["K"], # doesn't need to change 
                              'fl_L': fl["L"], # doesn't need to change                    
                              'fl_M': fl["M"]  # doesn't need to change
                             }


params_3d_44_44_20_Cu_xtal1_roi_plus = {'recon_idx': 0,
                              'f_recon_parameters': 'recon_parameters.txt',  # The txt file that will save the reconstruction parameters
                              'dev': dev,
                              'selfAb': False,
                              'cont_from_check_point': False,
                              'use_saved_initial_guess': False,
                              'ini_kind': 'const',  # choose from 'const', 'rand' or 'randn'
                              'init_const': 0.5,
                              'ini_rand_amp': 0.1,
                              'recon_path': './data/Xtal1_align1_adjusted1_ds4_recon/Ab_F_nEl_1_nDpts_4_b_0.0_lr_1E-3/Cu',
                              'f_initial_guess': 'initialized_grid_concentration',
                              'f_recon_grid': 'grid_concentration',
                              'data_path': './data/Xtal1_align1_adjusted1_ds4',    # the folder where the data file is in
                              'f_XRF_data': 'xtal1_xrf-roi-plus',    # the aligned channel data file output from XRFtomo                  
                              'f_XRT_data': 'xtal1_scalers',         # the aligned scaler data file output from XRFtomo
                              'photon_counts_us_ic_dataset_idx':1,
                              'photon_counts_ds_ic_dataset_idx':2,
                              'XRT_ratio_dataset_idx':3,                # the index in the scalers dataset that stores the ratio of the transmitted photon counts
                              'theta_ls_dataset_idx': 'exchange/theta', # the dataset in the channel data file that stores the object angle
                              'channel_names': 'exchange/elements',     # the dataset in the channel data file that stores the cahnnel names
                              'this_aN_dic': {"Cu": 29},
                              'element_lines_roi': np.array([['Cu', 'K']]),  # np.array([["Si, K"], ["Ca, K"]])
                              'n_line_group_each_element': np.array([1]),
                              'solid_angle_adjustment_factor': 0.5,  # because the detector is made up of 4 sensors with spacing in between(for 2-ID-E XRF), this factor is used to account for the loss of the total amount of photon counts
                              'sample_size_n': 44, 
                              'sample_height_n': 20,
                              'sample_size_cm': 0.007,                                    
                              'probe_energy': np.array([10.0]),                             
                              'n_epoch': 40,
                              'minibatch_size': 44,
                              'b': 0.0E-4,  # the regulizer coefficient of the XRT loss
                              'lr': 1.0E-3,                              
                              'det_size_cm': 2.4, # The estimated diameter of the sensor
                              'det_from_sample_cm': 2.0, # The estimated spacing between the sample and the detector
                              'manual_det_coord': True,
                              'set_det_coord_cm': np.array([[0.70, -2.0, 0.70], [0.70, -2.0, -0.70], [-0.70, -2.0, 0.70], [-0.70, -2.0, -0.70]]), 
                              'det_on_which_side': "negative",                            
                              'manual_det_area': True,
                              'set_det_area_cm2': 1.68,                                          
                              'det_ds_spacing_cm': 2.4/2.0, # Set this value to the value of det_size_cm divided by a number
                              'P_folder': 'data/P_array/sample_44_44_20_n/Dis_2.0_detSize_2.4_manual_dpts_4',              
                              'f_P': 'Intersecting_Length_44_44_20',  # The output file name has det_size_cm and det_ds_spacing_cm and det_from_sample_cm 
                              'fl_K': fl["K"], # doesn't need to change 
                              'fl_L': fl["L"], # doesn't need to change                    
                              'fl_M': fl["M"]  # doesn't need to change
                             }


params_3d_88_88_40_xtal1_roi_plus = {'recon_idx': 0,
                              'f_recon_parameters': 'recon_parameters.txt',  # The txt file that will save the reconstruction parameters
                              'dev': dev,
                              'selfAb': True,
                              'cont_from_check_point': False,
                              'use_saved_initial_guess': False,
                              'ini_kind': 'const',  # choose from 'const', 'rand' or 'randn'
                              'init_const': 0.5,
                              'ini_rand_amp': 0.1,
                              'recon_path': './data/Xtal1_align1_adjusted1_ds2_recon/Ab_T_nEl_4_nDpts_29_b_1E-4_lr_1E-3',
                              'f_initial_guess': 'initialized_grid_concentration',
                              'f_recon_grid': 'grid_concentration',
                              'data_path': './data/Xtal1_align1_adjusted1_ds2',    # the folder where the data file is in
                              'f_XRF_data': 'xtal1_xrf-roi-plus',    # the aligned channel data file output from XRFtomo                  
                              'f_XRT_data': 'xtal1_scalers',         # the aligned scaler data file output from XRFtomo
                              'photon_counts_us_ic_dataset_idx':1,
                              'photon_counts_ds_ic_dataset_idx':2,
                              'XRT_ratio_dataset_idx':3,                # the index in the scalers dataset that stores the ratio of the transmitted photon counts
                              'theta_ls_dataset_idx': 'exchange/theta', # the dataset in the channel data file that stores the object angle
                              'channel_names': 'exchange/elements',     # the dataset in the channel data file that stores the cahnnel names
                              'this_aN_dic': {"Al": 13, "Si": 14, "Fe": 26, "Cu": 29},
                              'element_lines_roi': np.array([['Al', 'K'], ['Si', 'K'], ['Fe', 'K'], ['Cu', 'K']]),  # np.array([["Si, K"], ["Ca, K"]])
                              'n_line_group_each_element': np.array([1, 1, 1, 1]),
                              'solid_angle_adjustment_factor': 0.5,  # because the detector is made up of 4 sensors with spacing in between(for 2-ID-E XRF), this factor is used to account for the loss of the total amount of photon counts
                              'sample_size_n': 88, 
                              'sample_height_n': 40,
                              'sample_size_cm': 0.007,                                    
                              'probe_energy': np.array([10.0]),                            
                              'n_epoch': 40,
                              'minibatch_size': 88,
                              'b': 0.0E-4,  # the regulizer coefficient of the XRT loss
                              'lr': 5.0E-4,                             
                              'det_size_cm': 2.4, # The estimated diameter of the sensor
                              'det_from_sample_cm': 3.0, # The estimated spacing between the sample and the detector
                              'manual_det_coord': True,
                              'set_det_coord_cm': np.array([[0.70, -2.0, 0.70], [0.70, -2.0, -0.70], [-0.70, -2.0, 0.70], [-0.70, -2.0, -0.70]]), 
                              'manual_det_area': True,
                              'set_det_area_cm2': 1.68,       
                              'det_on_which_side': "negative",                                        
                              'det_ds_spacing_cm': 2.4/2.0, # Set this value to the value of det_size_cm divided by a number
                              'P_folder': 'data/P_array/sample_44_44_20/Dis_2.0_detSize_2.4_detSpacing_1.2_dpts_5',              
                              'f_P': 'Intersecting_Length_44_44_20',  # The output file name has det_size_cm and det_ds_spacing_cm and det_from_sample_cm 
                              'fl_K': fl["K"], # doesn't need to change 
                              'fl_L': fl["L"], # doesn't need to change                    
                              'fl_M': fl["M"]  # doesn't need to change
                             }

params = params_3d_44_44_20_xtal1_roi_plus_2

if __name__ == "__main__": 
    
    reconstruct_jXRFT_tomography(**params)

    save_path = params["recon_path"]
    with open(os.path.join(save_path, 'ini_recon_parameters.txt'), "w") as recon_paras:
        print(str(params).replace(",", ",\n"), file=recon_paras, sep=',')



