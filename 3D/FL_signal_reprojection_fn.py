#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 20 15:58:57 2020

@author: panpanhuang
"""

import os
import sys
import datetime
import numpy as np
import h5py
from mpi4py import MPI
import xraylib as xlib
import xraylib_np as xlib_np

import torch as tc
tc.set_default_tensor_type(tc.FloatTensor)
import time
from util import rotate, MakeFLlinesDictionary_manual, intersecting_length_fl_detectorlet_3d_mpi_write_h5_3_manual
from standard_calibration import calibrate_incident_probe_intensity
from misc import print_flush_root, print_flush_all
from forward_model import PPM
import warnings
warnings.filterwarnings("ignore")

    
def generate_reconstructed_FL_signal(dev, use_simulation_sample, simulation_probe_cts, probe_att,
                                     std_path, f_std, fitting_method, std_element_lines_roi, density_std_elements, 
                                     selfAb, recon_path, f_recon_grid, f_reconstructed_XRF_signal, f_reconstructed_XRT_signal,
                                     theta_st, theta_end, n_theta, cont_from_last_theta,
                                     this_theta_st_idx, this_theta_end_idx,
                                     data_path, f_XRT_data,
                                     this_aN_dic, element_lines_roi, n_line_group_each_element, 
                                     sample_size_n, sample_height_n, sample_size_cm, probe_energy,
                                     minibatch_size,
                                     manual_det_coord, set_det_coord_cm, det_on_which_side,
                                     manual_det_area, set_det_area_cm2, det_size_cm, det_from_sample_cm,
                                     det_ds_spacing_cm, signal_attenuation_factor,
                                     P_folder, f_P, fl_K, fl_L, fl_M):
    
    comm = MPI.COMM_WORLD
    n_ranks = comm.Get_size()
    rank = comm.Get_rank()
    
    dia_len_n = int(1.2 * (sample_height_n**2 + sample_size_n**2 + sample_size_n**2)**0.5) #dev
    n_voxel_batch = minibatch_size * sample_size_n #dev
    n_voxel = sample_height_n * sample_size_n**2 #dev

    ####----------------------------------------------------------------------------------####    
    
    #### Calculate the number of elements in the reconstructed object, list the atomic numbers ####
    n_element = len(this_aN_dic)
    aN_ls = np.array(list(this_aN_dic.values()))
    ####--------------------------------------------------------------####
    
    #### Make the lookup table of the fluorescence lines of interests ####
    fl_all_lines_dic = MakeFLlinesDictionary_manual(element_lines_roi,                           
                                                    n_line_group_each_element, probe_energy, 
                                                    sample_size_n, sample_size_cm,
                                                    fl_line_groups = np.array(["K", "L", "M"]), fl_K = fl_K, fl_L = fl_L, fl_M = fl_M) #cpu
    
    stdout_options = {'root':0, 'output_folder': recon_path, 'save_stdout': True, 'print_terminal': False}
    
    detected_fl_unit_concentration = tc.as_tensor(fl_all_lines_dic["detected_fl_unit_concentration"]).float().to(dev)
    FL_line_attCS_ls = tc.as_tensor(xlib_np.CS_Total(aN_ls, fl_all_lines_dic["fl_energy"])).float().to(dev) #dev
    
    n_line_group_each_element = tc.IntTensor(fl_all_lines_dic["n_line_group_each_element"]).to(dev)
    n_lines = fl_all_lines_dic["n_lines"] #scalar
    ####--------------------------------------------------------------####
    
    #### Calculate the MAC of probe ####
    probe_attCS_ls = tc.as_tensor(xlib_np.CS_Total(aN_ls, probe_energy).flatten()).to(dev)
    ####----------------------------####
    
    
    if use_simulation_sample == True:
#         theta_ls = tc.from_numpy(-np.linspace(theta_st, theta_end, n_theta+1)[:-1] * np.pi / 180).float()  #unit: rad #cpu

        y2_true_handle = h5py.File(os.path.join(data_path, f_XRT_data), 'r')  
        #### Load all object angles from the XRT data ####
        theta_ls = tc.from_numpy(y2_true_handle['exchange/theta'][...] * np.pi / 180).float()  #unit: rad #cpu
        n_theta = len(theta_ls) 
        #### Use the probe_cts from manually set simulation_probe_cts
        probe_cts = simulation_probe_cts
        
    else:
        y2_true_handle = h5py.File(os.path.join(data_path, f_XRT_data), 'r')  
        #### Load all object angles from the XRT data ####
        theta_ls = tc.from_numpy(y2_true_handle['exchange/theta'][...] * np.pi / 180).float()  #unit: rad #cpu
        n_theta = len(theta_ls) 
        #### Calculate the incident photon counts from the calibration data
        probe_cts = calibrate_incident_probe_intensity(std_path, f_std, fitting_method, std_element_lines_roi, density_std_elements, probe_energy) 
    
    theta_idx_ls = np.arange(this_theta_st_idx, this_theta_end_idx, 1)
    this_theta_ls = theta_ls[this_theta_st_idx: this_theta_end_idx]
    
    minibatch_ls_0 = tc.arange(n_ranks).to(dev) #dev
    n_batch = (sample_height_n * sample_size_n) // (n_ranks * minibatch_size) #scalar
     
    if manual_det_area == True:
#         det_solid_angle_ratio = det_area_cm2 / (4 * np.pi * det_from_sample_cm**2)
        det_solid_angle_ratio = 1.0
        signal_attenuation_factor = 1.0
        
    else:
        #### det_solid_angle_ratio is used only for simulated dataset (use_std_calibation: False, manual_det_area: False, manual_det_coord: False)
        #### in which the incident probe intensity is not calibrated with the axo_std file.
        #### The simulated collected XRF photon number is estimated by multiplying the generated
        #### fluorescence photon number by "det_solid_angle_ratio" to account for the limited solid angle and the detecting efficiency of the detector
        
#         #### Calculate the detecting solid angle covered by the area of the spherical cap covered by the detector #### 
#         #### OPTION A: estimate the solid angle by the curved surface
#         # The distance from the sample to the boundary of the detector
#         r = (det_from_sample_cm**2 + (det_dia_cm/2)**2)**0.5   
#         # The height of the cap
#         h =  r - det_from_sample_cm
#         # The area of the cap area
#         fl_sig_collecting_cap_area = np.pi*((det_dia_cm/2)**2 + h**2)
#         # The ratio of the detecting solid angle / full soilid angle
#         det_solid_angle_ratio = fl_sig_collecting_cap_area / (4*np.pi*r**2)

        #### OPTION B: estimate the solid angle by the flat surface
        det_solid_angle_ratio = (np.pi * (det_size_cm/2)**2) / (4*np.pi * det_from_sample_cm**2)
        
        
        #### signal_attenuation_factor is used to account for other factors that cause the attenuation of the XRF
        #### exept the limited solid angle and self-absorption
        signal_attenuation_factor = 1.0
    
    P_save_path = os.path.join(P_folder, f_P)   
    P_handle = h5py.File(P_save_path + ".h5", 'r')   
    
    if rank == 0:
        # Create the elements list using element_lines_roi
        channel_name_roi_ls = []
        for i, element_line_roi in enumerate(element_lines_roi):
            if element_line_roi[1] == "K":
                channel_name_roi = element_line_roi[0]
            else:
                channel_name_roi = element_line_roi[0] + "_" + element_line_roi[1]
            
            channel_name_roi_ls.append(channel_name_roi)
        channel_name_roi_ls = np.array(channel_name_roi_ls).astype("S5")       
        scaler_names = np.array(["place_holder", "us_dc", "ds_ic", "abs_ic"]).astype("S12")
        
        
        if not cont_from_last_theta: # need to create the file if the current simulation starts from the first angle
#             if use_simulation_sample == True:
#                 theta_ls_degree = -np.linspace(theta_st, theta_end, n_theta+1)[:-1]
#             else:
            theta_ls_degree = y2_true_handle['exchange/theta'][...]     
                    
            with h5py.File(os.path.join(recon_path, f_reconstructed_XRF_signal +'.h5'), 'w') as d:
                grp = d.create_group("exchange")
                data = grp.create_dataset("data", shape=(n_lines, n_theta, sample_height_n, sample_size_n), dtype="f4")
                elements = grp.create_dataset("elements", data = channel_name_roi_ls) 
                theta = grp.create_dataset("theta", data = theta_ls_degree)

            with h5py.File(os.path.join(recon_path, f_reconstructed_XRT_signal +'.h5'), 'w') as d:
                grp = d.create_group("exchange")
                data = grp.create_dataset("data", shape=(4, n_theta, sample_height_n, sample_size_n), dtype="f4")
                elements = grp.create_dataset("elements", data = scaler_names)
                theta = grp.create_dataset("theta", data = theta_ls_degree)
            
        with h5py.File(os.path.join(recon_path, f_reconstructed_XRT_signal +'.h5'), 'r+') as d:
            d["exchange/data"][0,:,:,:] = 0
            d["exchange/data"][1,:,:,:] = probe_cts
            
    comm.Barrier()
    
                                                                                     
    # Read X from hdf5 file
    with h5py.File(os.path.join(recon_path, f_recon_grid + ".h5"), "r") as s:
        X = s["sample/densities"][...].astype(np.float32)
    X = tc.from_numpy(X).float() #cpu       
    
    for theta_idx, theta in zip(theta_idx_ls ,this_theta_ls):
        stdout_options = {'root':0, 'output_folder': recon_path, 'save_stdout': False, 'print_terminal': True}
        timestr = str(datetime.datetime.today())     
        print_flush_root(rank, val=f"theta_idx: {theta_idx}, time: {timestr}", output_file='', **stdout_options)
        
        ## Calculate lac using the current X. lac (linear attenuation coefficient) has the dimension of [n_element, n_lines, n_voxel_minibatch, n_voxel]
        if selfAb == True:
            X_ap_rot = rotate(X, theta, dev) #dev
            lac = X_ap_rot.view(n_element, 1, 1, n_voxel) * FL_line_attCS_ls.view(n_element, n_lines, 1, 1) #dev
            lac = lac.expand(-1, -1, n_voxel_batch, -1).float() #dev

        else:
            lac = 0.
        
        for m in range(n_batch):                    
            minibatch_ls = n_ranks * m + minibatch_ls_0  #dev, e.g. [5,6,7,8]
            p = minibatch_ls[rank]
            
            if selfAb == True:
                P_minibatch = tc.from_numpy(P_handle['P_array'][:,:, p * dia_len_n * minibatch_size * sample_size_n: (p+1) * dia_len_n * minibatch_size * sample_size_n]).to(dev)
                n_det = P_minibatch.shape[0] 

            else:
                P_minibatch = 0
                n_det = 0
      
            model = PPM(dev, selfAb, lac, X, p, n_element, n_lines, FL_line_attCS_ls,
                         detected_fl_unit_concentration, n_line_group_each_element,
                         sample_height_n, minibatch_size, sample_size_n, sample_size_cm,
                         probe_energy, probe_cts, probe_att, probe_attCS_ls,
                         theta, signal_attenuation_factor,
                         n_det, P_minibatch, det_size_cm, det_from_sample_cm, det_solid_angle_ratio)
            
            y1_hat, y2_hat = model() #y1_hat dimension: (n_lines, minibatch_size); y2_hat dimension: (minibatch_size,)
            y1_hat = np.clip(y1_hat.detach().numpy(), 0, np.inf)
            y2_hat = np.exp(- y2_hat.detach().numpy())
            
            #### Use mpi to write the generated dataset to the hdf5 file
            with h5py.File(os.path.join(recon_path, f_reconstructed_XRF_signal +'.h5'), 'r+', driver='mpio', comm=comm) as d:
                d["exchange/data"][:, theta_idx, minibatch_size * p // sample_size_n: minibatch_size * (p + 1) // sample_size_n, :] = \
                np.reshape(y1_hat, (n_lines, minibatch_size // sample_size_n, -1)) 
                
            comm.Barrier()    
                ## shape of d["exchange/data"] = (n_lines, n_theta, sample_height_n, sample_size_n)
            
            with h5py.File(os.path.join(recon_path, f_reconstructed_XRT_signal +'.h5'), 'r+', driver='mpio', comm=comm) as d:
                d["exchange/data"][3, theta_idx, minibatch_size * p // sample_size_n: minibatch_size * (p + 1) // sample_size_n, :] = \
                np.reshape(y2_hat, (minibatch_size // sample_size_n, -1))
            
            comm.Barrier()
                ## shape of d["exchange/data"] = (4, n_theta, sample_height_n, sample_size_n)
            ####
        
        if rank == 0:
            with h5py.File(os.path.join(recon_path, f_reconstructed_XRT_signal +'.h5'), 'r+') as d:
                d["exchange/data"][2, theta_idx] = d["exchange/data"][1, theta_idx] * d["exchange/data"][3, theta_idx]
        comm.Barrier()

        del lac
        tc.cuda.empty_cache()
    
                              
    ## It's important to close the hdf5 file hadle in the end of the reconstruction.
    y2_true_handle.close()
    P_handle.close()       