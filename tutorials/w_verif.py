#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 27 23:28:58 2021

@author: ghiggi
"""
##----------------------------------------------------------------------------.
import pygsp as pg
import cartopy.crs as ccrs
data_dir = "/home/ghiggi/Projects/DeepSphere/ToyData/Healpix_400km"

ds = xr.open_zarr(os.path.join(data_dir,"Dataset","dynamic.zarr"))
ds = ds.isel(time=slice(0,10))
ds = ds.load()

ds1 = ds.copy()
ds1 = ds + 0.15

pred = ds1
obs = ds
# check when same ... 0 issues 
exclude_dim = "leadtime"
exclude_dim = frozenset({})
aggregating_dims = ('time')
thr = 0.0000001
 
##----------------------------------------------------------------------------.
# Compute deterministic metric (at each node, each leadtime)
ds_skill = deterministic(pred, obs, 
                         forecast_type="continuous",
                         aggregating_dims=aggregating_dims,
                         exclude_dim=exclude_dim)

# Add information related to mesh area
ds_skill = ds_skill.sphere.add_nodes_from_pygsp(pygsp_graph=pg.graphs.SphereHealpix(subdivisions=16, k=20, nest=False))
ds_skill = ds_skill.sphere.add_SphericalVoronoiMesh(x='lon', y='lat')

# Compute skill summary statics    
ds_global_skill = global_summary(ds_skill, area_coords="area")
ds_latitudinal_skill = latitudinal_summary(ds_skill, lat_dim='lat', lon_dim='lon', lat_res=5) 
ds_longitudinal_skill = longitudinal_summary(ds_skill, lat_dim='lat', lon_dim='lon', lon_res=5) 

# Example
ds_skill['t850'].to_dataset('skill') 
ds_global_skill['t850'].to_dataset('skill') # TODO check with same data ... NSE wrong? 
ds_latitudinal_skill['t850'].to_dataset('skill') 
ds_longitudinal_skill['t850'].to_dataset('skill') 

##----------------------------------------------------------------------------.
## Spatial skill maps  (long-term)
plot_skill_maps(ds_skill,  
                figs_dir,
                crs_proj = ccrs.Robinson(),
                suffix="",
                prefix="")

## TODO: 
# - Add for the other skills too ... skills as function argument ... 
# - MonthlySkills 

##----------------------------------------------------------------------------.
## Global skill stats vs. leadtime 
# - Line plots 
skills = ['BIAS','RMSE','rSD','pearson_R2']
ds_global_skill.to_array().sel(skill=skills).plot(col='variable', row='skill')

# - Boxplots

##----------------------------------------------------------------------------.
### Animation (12 animation ... for each month)(for each variable separately)
## Obs , Forecast, Error  
## Obs Anom , Forecast Anom , Error Anom 

##----------------------------------------------------------------------------.