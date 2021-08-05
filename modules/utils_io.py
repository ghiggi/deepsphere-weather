#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 18 23:56:40 2021

@author: ghiggi
"""
import datetime
import numpy as np 
import xarray as xr

def is_dask_DataArray(da):
    """Check if data in the xarray DataArray are lazy loaded."""
    if da.chunks is not None:
        return True
    else: 
        return False

def _check_timesteps(timesteps):
    """Check timesteps object and return a numpy array."""
    if isinstance(timesteps, str): 
        timesteps = np.array([np.datetime64(timesteps)])
        return timesteps
    if timesteps is None: 
        raise ValueError("'timesteps' is None.")
    if len(timesteps) == 0: 
        raise ValueError("'timesteps' is empty.")
    elif isinstance(timesteps, (np.datetime64, datetime.datetime)):
        timesteps = np.array([timesteps])
        return timesteps 
    elif isinstance(timesteps, list): 
        if all([isinstance(v, (np.datetime64, datetime.datetime)) for v in timesteps]):
            timesteps = np.array(timesteps)
            return timesteps
        else: 
            raise ValueError("The list must contain np.datetime64 or datetime.datetime objects.")
    elif isinstance(timesteps, np.ndarray):
        if isinstance(timesteps[0], np.datetime64):
            return timesteps
        else:
            raise ValueError("The numpy array must contain datetime objects.")
    else: 
        raise ValueError("Unvalid timesteps specification.")
    
def _get_subset_timesteps_idxs(timesteps, subset_timesteps, strict_match=True):
    """Check subset_timesteps are within timesteps and return the matching indices."""
    subset_timesteps = _check_timesteps(subset_timesteps)
    timesteps = _check_timesteps(timesteps)
    subset_timesteps = subset_timesteps.astype(timesteps.dtype) # same precision required for comparison
    subset_idxs = np.array([idx for idx, v in enumerate(timesteps) if v in set(subset_timesteps)])  
    if subset_idxs.size == 0:
        raise ValueError("The 'subset_timesteps' are not within the available 'timesteps'.")
    if len(subset_idxs) != len(subset_timesteps):
        timesteps_not_in = subset_timesteps[np.isin(subset_timesteps, timesteps, invert=True)] 
        if strict_match:
            raise ValueError("The following 'subset_timesteps' are not within 'timesteps':", list(timesteps_not_in))       
        else:
            raise Warning("The following 'subset_timesteps' are not within 'timesteps':", list(timesteps_not_in))
    return subset_idxs

def check_no_missing_timesteps(timesteps, verbose=True):
    """Check if there are missing timesteps in a list or numpy datetime64 array."""
    timesteps = _check_timesteps(timesteps) 
    # Check if there are data
    if timesteps.size == 0: 
        raise ValueError("No data available !")
    # Check if missing timesteps 
    dt = np.diff(timesteps)
    dts, counts = np.unique(dt, return_counts=True)
    if verbose:
        print("  --> Starting at", timesteps[0])
        print("  --> Ending at", timesteps[-1])
    if (len(counts) > 1):
        print("Missing data between:")
        bad_dts = dts[counts != counts.max()] 
        for bad_dt in bad_dts:
            bad_idxs = np.where(dt == bad_dt)[0]
            bad_idxs = [b.tolist() for b in bad_idxs]
            for bad_idx in bad_idxs:
                tt_missings = timesteps[bad_idx:(bad_idx+2)]
                print("-", tt_missings[0], "and", tt_missings[1])
        raise ValueError("The process has been interrupted") 
    return 

def check_finite_Dataset(ds):
    """Check Dataset does not contain NaN and Inf values."""
    # Check is a Dataset
    if not isinstance(ds, xr.Dataset):
        raise TypeError("'ds' must be an xarray Dataset.")
    # Check no NaN values
    ds_isnan = xr.ufuncs.isnan(ds)  
    list_vars_with_nan = []
    flag_raise_error = False
    for var in list(ds_isnan.data_vars.keys()):
        if ds_isnan[var].sum().values != 0:
            list_vars_with_nan.append(var)
            flag_raise_error = True
    if flag_raise_error: 
        raise ValueError('The variables {} contain NaN values'.format(list_vars_with_nan))
    # Check no Inf values
    ds_isinf = xr.ufuncs.isinf(ds)  
    list_vars_with_inf = []
    flag_raise_error = False
    for var in list(ds_isinf.data_vars.keys()):
        if ds_isinf[var].sum().values != 0:
            list_vars_with_inf.append(var)
            flag_raise_error = True
    if flag_raise_error: 
        raise ValueError('The variables {} contain Inf values.'.format(list_vars_with_inf))
        
def check_dimnames_DataArray(da, required_dimnames, da_name):
    """Check dimnames are dimensions of the DataArray."""
    if not isinstance(da_name, str): 
        raise TypeError("'da_name' must be a string.")
    if not isinstance(da, xr.DataArray):
        raise TypeError("'da' must be an xarray DataArray")
    if not isinstance(required_dimnames, list):
        raise TypeError("'required_dimnames' must be a list")
    # Retrieve DataArray dimension names 
    da_dims = list(da.dims)
    # Identify which dimension are missing 
    missing_dims = np.array(required_dimnames)[np.isin(required_dimnames, da_dims, invert=True)]
    # If missing, raise an error
    if len(missing_dims) > 0: 
        raise ValueError("The {} must have also the '{}' dimension".format(da_name, missing_dims))

def check_dimnames_Dataset(ds, required_dimnames, ds_name):
    """Check dimnames are dimensions of the Dataset."""
    if not isinstance(ds_name, str): 
        raise TypeError("'ds_name' must be a string.")
    if not isinstance(ds, xr.Dataset):
        raise TypeError("'ds' must be an xarray Dataset")
    if not isinstance(required_dimnames, list):
        raise TypeError("'required_dimnames' must be a list")
    # Retrieve Dataset dimension names 
    ds_dims = list(ds.dims.keys())    
    # Identify which dimension are missing 
    missing_dims = np.array(required_dimnames)[np.isin(required_dimnames, ds_dims, invert=True)]
    # If missing, raise an error
    if len(missing_dims) > 0: 
        raise ValueError("The {} must have also the '{}' dimension".format(ds_name, missing_dims))
        
#-----------------------------------------------------------------------------.
def _check_AR_DataArray_dimnames(da_dynamic = None,
                                 da_bc = None, 
                                 da_static = None):
    """Check the dimension names of DataArray required for AR training and predictions."""
    # Required dimensions (names)
    time_dim='time'
    node_dim='node'
    variable_dim='feature'
    # Check for dimensions of the dynamic DataArray
    if da_dynamic is not None: 
        check_dimnames_DataArray(da = da_dynamic, da_name = "dynamic DataArray",
                                 required_dimnames=[time_dim, node_dim, variable_dim])
   
    # Check for dimensions of the boundary conditions DataArray           
    if da_static is not None: 
        check_dimnames_DataArray(da = da_static, da_name = "static DataArray",
                                 required_dimnames=[node_dim, variable_dim])
   
    # Check for dimension of the static DataArray      
    if da_bc is not None: 
        check_dimnames_DataArray(da = da_bc, da_name = "bc DataArray",
                                 required_dimnames=[time_dim, node_dim, variable_dim])

def check_AR_DataArrays(da_training_dynamic,
                        da_validation_dynamic = None, 
                        da_training_bc = None,
                        da_validation_bc = None, 
                        da_static = None,
                        verbose = False):
    """Check DataArrays required for AR training and predictions."""
    ##------------------------------------------------------------------------.
    # Check da_dynamic is provided 
    if not isinstance(da_training_dynamic, xr.DataArray):   
        raise ValueError("The dynamic DataArray is necessary for AR models.")
    if da_validation_bc is not None and not isinstance(da_validation_dynamic, xr.DataArray):   
        raise ValueError("The validation dynamic DataArray is necessary for AR models.")
    ##------------------------------------------------------------------------.
    # Check dimension names 
    _check_AR_DataArray_dimnames(da_dynamic=da_training_dynamic,
                                 da_bc=da_training_bc,
                                 da_static=da_static)
    _check_AR_DataArray_dimnames(da_dynamic=da_validation_dynamic,
                                 da_bc=da_validation_bc,
                                 da_static=da_static)
    ##------------------------------------------------------------------------.
    # Check that the required DataArrays are provided 
    if da_validation_dynamic is not None: 
        if ((da_training_bc is not None) and (da_validation_bc is None)):  
            raise ValueError("If boundary conditions data are provided for the training, must be provided also for validation!")
    ##------------------------------------------------------------------------.
    # Check no missing timesteps 
    if verbose: 
        print("- Data time period")
    check_no_missing_timesteps(da_training_dynamic['time'].values, verbose=verbose)
    if da_validation_dynamic is not None: 
        if verbose: 
            print("- Validation Data time period")
        check_no_missing_timesteps(da_validation_dynamic['time'].values, verbose=verbose)
    if da_training_bc is not None: 
        check_no_missing_timesteps(da_training_bc['time'].values, verbose=False)
    if da_validation_bc is not None: 
        check_no_missing_timesteps(da_validation_bc['time'].values, verbose=False)
    ##------------------------------------------------------------------------.
    # Check time alignment of training and validation DataArray
    if da_training_bc is not None: 
        all_same_timesteps = np.all(da_training_dynamic['time'].values == da_training_bc['time'].values)
        if not all_same_timesteps:
            raise ValueError("The training dynamic DataArray and the training boundary conditions DataArray does not have the same timesteps!")
    if ((da_validation_dynamic is not None) and (da_validation_bc is not None)): 
        all_same_timesteps = np.all(da_validation_dynamic['time'].values == da_validation_bc['time'].values)
        if not all_same_timesteps:
            raise ValueError("The validation dynamic DataArray and the validation boundary conditions DataArray does not have the same timesteps!")
    ##------------------------------------------------------------------------.
    ## Check dimension order coincide between training and validation
    if da_validation_dynamic is not None:
        dim_info_training = get_AR_model_diminfo(da_dynamic = da_training_dynamic, 
                                                 da_bc = da_training_bc,
                                                 da_static = da_static)
        dim_info_validation = get_AR_model_diminfo(da_dynamic = da_validation_dynamic, 
                                                   da_bc = da_validation_bc,
                                                   da_static = da_static)
        if not dim_info_training == dim_info_validation:
            raise ValueError("The dimension order of training and validation DataArrays do not coincide!")
            
#-----------------------------------------------------------------------------.
# #############################
### Checks for AR Datasets ####
# #############################    
def _check_AR_Dataset_dimnames(ds_dynamic = None,
                               ds_bc = None, 
                               ds_static = None):
    """Check the dimension names of Datasets required for AR training and predictions."""
    # Required dimensions (names)
    time_dim='time'
    node_dim='node'
    ##------------------------------------------------------------------------.
    # Check for dimensions of the dynamic Dataset
    if ds_dynamic is not None: 
        check_dimnames_Dataset(ds = ds_dynamic, ds_name = "dynamic Dataset",
                               required_dimnames=[time_dim, node_dim])
   
    # Check for dimensions of the static Dataset              
    if ds_static is not None: 
        check_dimnames_Dataset(ds = ds_static, ds_name = "static Dataset",
                               required_dimnames=[node_dim])
   
    # Check for dimension of the boundary conditions Dataset     
    if ds_bc is not None: 
        check_dimnames_Dataset(ds = ds_bc, ds_name = "bc Dataset",
                               required_dimnames=[time_dim, node_dim])   
 

##----------------------------------------------------------------------------.
def check_AR_Datasets(ds_training_dynamic,
                      ds_validation_dynamic = None,
                      ds_static = None,              
                      ds_training_bc = None,         
                      ds_validation_bc = None,
                      verbose=False):
    """Check Datasets required for AR training and predictions."""
    # Check dimension names 
    _check_AR_Dataset_dimnames(ds_dynamic=ds_training_dynamic,
                               ds_bc=ds_training_bc,
                               ds_static=ds_static)
    _check_AR_Dataset_dimnames(ds_dynamic=ds_validation_dynamic,
                               ds_bc=ds_validation_bc,
                               ds_static=ds_static)
    ##------------------------------------------------------------------------.
    # Check that the required Datasets are provided 
    if ds_validation_dynamic is not None: 
        if ((ds_training_bc is not None) and (ds_validation_bc is None)):  
            raise ValueError("If boundary conditions data are provided for the training, must be provided also for validation!")
    ##------------------------------------------------------------------------.
    # Check no missing timesteps 
    if verbose: 
        print("Data")
    check_no_missing_timesteps(ds_training_dynamic['time'].values, verbose=verbose)
    if ds_validation_dynamic is not None: 
        if verbose: 
            print("Validation Data")
        check_no_missing_timesteps(ds_validation_dynamic['time'].values, verbose=verbose)
    if ds_training_bc is not None: 
        check_no_missing_timesteps(ds_training_bc['time'].values, verbose=False)
    if ds_validation_bc is not None: 
        check_no_missing_timesteps(ds_validation_bc['time'].values, verbose=False)
    ##------------------------------------------------------------------------.
    # Check time alignment of training and validation dataset
    if ds_training_bc is not None: 
        same_timesteps = ds_training_dynamic['time'].values == ds_training_bc['time'].values
        if not all(same_timesteps):
            raise ValueError("The training dynamic Dataset and the training boundary conditions Dataset does not have the same timesteps!")
    if ((ds_validation_dynamic is not None) and (ds_validation_bc is not None)): 
        same_timesteps = ds_validation_dynamic['time'].values == ds_validation_bc['time'].values
        if not all(same_timesteps):
            raise ValueError("The validation dynamic Dataset and the validation boundary conditions Dataset does not have the same timesteps!")
    ##------------------------------------------------------------------------.

#-----------------------------------------------------------------------------.   
# Retrieve input-output dims 
def get_AR_model_diminfo(da_dynamic, da_static=None, da_bc=None, AR_settings=None):
    """Retrieve dimension information for AR DeepSphere models.""" 
    ##------------------------------------------------------------------------.
    # Required dimensions
    time_dim='time'
    node_dim='node'
    variable_dim='feature'
    ##------------------------------------------------------------------------.
    if not isinstance(da_dynamic, xr.DataArray): 
        raise ValueError("The dynamic DataArray is necessary for AR models.")
    ##------------------------------------------------------------------------.
    # Dynamic variables 
    check_dimnames_DataArray(da = da_dynamic, da_name = "dynamic DataArray",
                             required_dimnames=[time_dim, node_dim, variable_dim])
    dynamic_variables = da_dynamic[variable_dim].values.tolist()
    n_dynamic_variables = len(dynamic_variables)
    dims_dynamic = list(da_dynamic.dims)
    # Static variables 
    if da_static is not None:
        check_dimnames_DataArray(da = da_static, da_name = "static DataArray",
                                 required_dimnames=[node_dim, variable_dim])
        dims_static = list(da_static.dims)
        static_variables = da_static[variable_dim].values.tolist()
        n_static_variables = len(static_variables)
    else:
        dims_static = None
        static_variables = []
        n_static_variables = 0
        
    # Boundary condition variables     
    if da_bc is not None:
        check_dimnames_DataArray(da = da_bc, da_name = "bc DataArray",
                                 required_dimnames=[time_dim, node_dim, variable_dim])
        dims_bc = list(da_bc.dims)
        bc_variables = da_bc[variable_dim].values.tolist()
        n_bc_variables = len(bc_variables)
    else: 
        dims_bc = None
        bc_variables = []
        n_bc_variables = 0
    ##-------------------------------------------------------------------------.
    # Check dims_bc order is the same as dims_dynamic
    if dims_bc is not None:
        if not np.array_equal(dims_dynamic, dims_bc):
            raise ValueError("Dimension order of dynamic and bc DataArrays must be equal.")
      
    ##------------------------------------------------------------------------. 
    # Define feature dimensions 
    input_feature_dim = n_static_variables + n_bc_variables + n_dynamic_variables 
    output_feature_dim = n_dynamic_variables
    input_features = static_variables + bc_variables + dynamic_variables                     
    output_features = dynamic_variables
    ##------------------------------------------------------------------------. 
    # Define number of nodes 
    input_node_dim = len(da_dynamic['node'])
    output_node_dim = len(da_dynamic['node'])
    ##------------------------------------------------------------------------. 
    # Define dimension order
    dim_order = ['sample'] + list(da_dynamic.dims) # Here I force batch_dim to be the first dimension (for all code)! 
    ##------------------------------------------------------------------------. 
    # Define time dimensions
    if AR_settings is not None:
        input_time_dim = len(AR_settings['input_k']) 
        output_time_dim = len(AR_settings['output_k']) 
    ##------------------------------------------------------------------------. 
    # Define input-ouput tensor shape 
    if AR_settings is not None:
        dim_input = {}
        dim_input['node'] = input_node_dim
        dim_input['time'] = input_time_dim
        dim_input['feature'] = input_feature_dim
        input_shape = tuple([dim_input[k] for k in dim_order[1:]])
        
        dim_output = {}
        dim_output['node'] = output_node_dim
        dim_output['time'] = output_time_dim
        dim_output['feature'] = output_feature_dim
        output_shape = tuple([dim_input[k] for k in dim_order[1:]])
    ##------------------------------------------------------------------------.
    # Define time dimension 
    if AR_settings is not None:
        # Create dictionary with dimension infos 
        dim_info = {'input_feature_dim': input_feature_dim,
                    'output_feature_dim': output_feature_dim,
                    'input_features': input_features,
                    'output_features': output_features,
                    'input_time_dim': input_time_dim,
                    'output_time_dim': output_time_dim,
                    'input_node_dim': input_node_dim,
                    'output_node_dim': output_node_dim,
                    'dim_order': dim_order,
                    'input_shape': input_shape,
                    'output_shape': output_shape,
                    }
    else:
        # Create dictionary with dimension infos (without time)
        dim_info = {'input_feature_dim': input_feature_dim,
                    'output_feature_dim': output_feature_dim,
                    'input_features': input_features,
                    'output_features': output_features,
                    'input_node_dim': input_node_dim,
                    'output_node_dim': output_node_dim,
                    'dim_order': dim_order,
                    }    
    ##------------------------------------------------------------------------. 
    return dim_info 
