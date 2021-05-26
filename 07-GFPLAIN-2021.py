# -*- coding: utf-8 -*-
"""
Created on May 24 2021 | Tusday 18:00

This script runs the GFPLAIN algorithm multiple times using an iterative 
structure

This script loads a CSV file with  (a,b) pairs and IDs
and evaluate the GFPLAIN algorithnm for each one of them 

After evalauting the objective fucntion this script will evaluate floodplain
Performance metrics using a benchmark floodplain map previusly intrioruced as
an input.

The benchmark map needs to ahve the same pixel same and extent as the input DEM
The benchmark floodplain map needs to have flood ehight in meters

The files generated for each iteration will be stored in a folder
and the summary of the performance metrics will be saved in an excel file 


@author: uqgpere2
"""


###############################################################################
#%%               IMPORTANT REMARKS BEFORE RUNNING THIS SCRIPT
###############################################################################

# This script can only be run on Python 2.7 shell or under Spyder 3 using ArcGIS's
# Python 2.7 as interpreter:

#  C:\Python27\ArcGIS10.7\python.exe

# This script imports arcpy so you need to have ArcGIS installed and with license

# You need to compile the function "generate_floodplain()" before executing 
# this script 

# You better close ArcMap and any other GIS sofware that may be using files 
# produced or used by this script in order to avoid errors associated with 
# "lock" files

# You can't have names longer than 10 characters or this won't work

# You can't have names starting with special characters or this won't work

# the character to indicate file paths is : r"\"

# On the other hand, strings, even when marked as r"Raw strings", cannot end 
# with a "\", it means that if you want to concatenate file paths 
# you need to use this: "\\"

# Or better yet, use os.path.join() function: 
# fullPath = os.path.join(fodler_location, File_Name)

# A good introduction to phyton can be found here:
# https://docs.python.org/2/tutorial/introduction.html

# Before doing anything you need to make sure you have installed the 
# required packages in your machine.

# This script was modified form the original version of GFPLAIN found here:

# https://github.com/fnardi/GFPLAIN

###############################################################################
#%%  ^    ^     ^  IMPORTANT REMARKS BEFORE RUNNING THIS MODEL    ^    ^     ^  
###############################################################################



###############################################################################
#%%                        PACKAGES YOU NEED TO LOAD
###############################################################################

import sys
import string 
import os
import math
import traceback
import glob
import itertools

import arcpy
from arcpy.sa import *
from datetime import datetime

import openpyxl
from openpyxl import Workbook

import matplotlib.pyplot as plt
import numpy as np

import pandas as pd
from pandas import ExcelWriter

import itertools
from itertools import permutations  

import math
import random
from IPython.display import clear_output

import time

from __future__ import division

###############################################################################
#%%  ^  ^  ^  ^  ^  ^  ^   PACKAGES YOU NEED TO LOAD       ^  ^  ^  ^  ^  ^  ^ 
###############################################################################

###############################################################################
# %%                            CHECK license
###############################################################################

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")

# Allow output to overwrite...
arcpy.env.overwriteOutput = True

###############################################################################
# %% ^  ^  ^  ^  ^  ^  ^         CHECK license  ^  ^  ^  ^  ^  ^  ^  
###############################################################################


###############################################################################
#%%                            Input parameters
###############################################################################

# Input terrain data:----------------------------------------------------------

# All have the same extension:
#input_DEM_filename= r'co_burned'     # ALOS PALSAR 12_m rivers Burned intercomparisson extend   
#input_DEM_filename= r'cop_alos12m'   # ALOS PALSAR 12_m RAW intercomparisson extenT (CROPPED)
#input_DEM_filename= r'co_csiro'      # SRTM 30m rivers burned by CSIRO intercomparisson extend

input_DEM_filename= r'co_alp_12m'     # ALOS PALSAR 12_m Entire Copiapo River Basin 


# Code for naming resuults:---------------------------------------------------

# Short Name of the Basin (It cannot be more than 2 characters )
Code= 'co'                                             


# Accumulation threshold area:-------------------------------------------------

# The definition of contributing area thresholds (bl_tresh) for extracting 
# river networks is highly dependent on DTM resolution (McMaster 2002).

# for a DEM of 10 m resolution you should ideally used 10 Km2
# for a 30 m resolution you shoudl used at least 50 km2

# for more information about this parameter read Annis et al 2019 (pag 6)
# https://doi.org/10.1080/02626667.2019.1591623

# threshold area [Square kilometers] for stream network
# [sqkm]       [m2]     [ha]
#  0.1 =     100 000    10   
#  1   =   1 000 000    100  
#  10  =  10 000 000    1000 
bl_tresh = r'1'                                                
print ('The threshold area for flow accumulation is: [Sqkm]', bl_tresh)



# Flood extent observation extent ---------------------------------------------

# This is a bianry raster with the observed extent of the flood event taht will be sue
# to benchmark of calibrate the model. 

# This file is a bianry ratsr with:
# 1 values indicating flooded areas  
# 0 values indicating dry areas

# this raster nees to have the same extent and the same cell size as the resutls 
# that will be obtaiend by GFPALIN

obs_raster_name= r'fpl_SWIFT_2015_APE.tif'


# Obserbation points shp:------------------------------------------------------ 

obs_points_shapefile_name=r'calibration_points_GFPLAIN.shp'
obs_points_attribute_table_name=r'calibration_points_GFPLAIN.dbf'
file_name_excel_table_obs_points=r'calibration_points_GFPLAIN.xlsx'

# Shapefile with interest area (modelling extent/ mask region)-----------------

# nornally the observed flood extent has geoemtrical bodudanries (limited) and
# therefore the performance statistiscs are cosntrain lto the same extent 
# this shapefile represent this boudnaries so the calcualtion of the performance 
# metrics is limited to this locations

# This is the mask feature of the interest area -------------------------------
mask_shape_name= r'extent_paper_GFPLAIN_Vs_SWIFT.shp'


# File with list of simualtions  ----------------------------------------------

sim_list_file_name= r'GFPLAIN_simulations_paper_SWIFT_Vs_GFPLAIN.xlsx'

###############################################################################
#%%    ^  ^  ^  ^  ^  ^  ^    Input parameters    ^  ^  ^  ^  ^  ^  ^  ^  ^  ^  ^  
###############################################################################


###############################################################################
# %%                      DEFINITION OF FILE LOCATIONS
###############################################################################

# Path of the main folder for the simulations
current_working_directory=r'C:\00-C-GPM_INFO\04-C-RDM\04-C-02-Python\04-C-02-01-GFPLAIN'    

# FOLDER NAMES----------------------------------------------------------------

# Folder name with inputs files
Input_files_folder_name= r'04-Inputs-files'

# Folder name with input rasters
Input_rasters_folder_name= r'05-Inputs-rasters'

# Folder name with input shapefiles
Input_shapes_folder_name= r'06-Inputs-shapes'

# the outputs of hydrobase and pre-processing
Output_preprocessing_folder_name= r'07-Results-preprocessing'

# the output files folder
Output_files_folder_name= r'08-Result-files'

# Folder name with output rasters
Output_shapes_folder_name= r'10-Results-shapes'

# Folder name with output shapefiles
Output_rasters_folder_name= r'09-Results-rasters'

# Folder Name for Hydrobase results
HB_Folder_name = "HYDROBASE"                  

# Folder Name for PP results
Pre_Procesing_Folder_name = 'PREPROCESSING'    

# Folder Name for Floodpain results
Flood_Height_Folder_name = "FLOOD_HEIGHT"         

# Folder Name for Floodpain extent
Flood_Plain_Folder_name = "FLOODPLAIN_EXTENT"         

# Folder with the points for model evaluations
Obs_points_folder_name = "FLOW_DEPTH_OBS_POINTS"   

# Folder name with hit missed rasters
Output_folder_ce_rasters= r'CROSSED_ERROR_RASTERS'

# Folder Names for contegency tables
CE_table_folder_name= 'CROSSED_ERROR_TABLES'

# FOLDER PATHS-----------------------------------------------------------------

#  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #
#                                                                        Inputs
#  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #

# Path to input files:
Inputpath_files= os.path.join(current_working_directory,Input_files_folder_name)

# Path to input shapes:
Inputpath_shapes= os.path.join(current_working_directory,Input_shapes_folder_name)

# Path to input rasters:
Inputpath_rasters= os.path.join(current_working_directory,Input_rasters_folder_name)

# Path to files results:
OutPath_files= os.path.join(current_working_directory,Output_files_folder_name)

#  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #
#                                                                       Outputs
#  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #

# Path to files shapes:
OutPath_files= os.path.join(current_working_directory,Output_files_folder_name)

# Path to raster results:
OutPath_rasters= os.path.join(current_working_directory,Output_rasters_folder_name)

# Path to shapefile results:
OutPath_shapes= os.path.join(current_working_directory,Output_shapes_folder_name)


# Path to pre processing results:
OutPath_PP= os.path.join(current_working_directory,Output_preprocessing_folder_name)

# HYDROBASE folder location: 
OutPath_hydrobase= os.path.join(OutPath_PP, HB_Folder_name)

# HYDROBASE folder location: 
hydrobase_folder_path= os.path.join(OutPath_PP, HB_Folder_name)

# PREPROCESSING folder locations:
preprocessing_folder_path= os.path.join(OutPath_PP, Pre_Procesing_Folder_name) 

# FLOODPLAIN locations

OutPath_flood_height_ras= os.path.join(OutPath_rasters,Flood_Height_Folder_name) 

OutPath_floodplain_ras= os.path.join(OutPath_rasters,Flood_Plain_Folder_name) 

OutPath_floodplain_shp=os.path.join(OutPath_shapes,Flood_Plain_Folder_name) 

# Points observed FH:
OutPath_obs_points=os.path.join(OutPath_shapes,Obs_points_folder_name) 


# Path to folder with hit missed rasters:
ce_rasters_path=os.path.join(OutPath_rasters,Output_folder_ce_rasters)

# Path to contengency tables:
ce_table_path= os.path.join(OutPath_files,CE_table_folder_name)

# FILE PATHS-------------------------------------------------------------------

# Floodplain benchmark:

obs_raster_path= os.path.join(Inputpath_rasters,obs_raster_name)

# Observation points:
# Here you create a file path for the shapefile with the observation points for RMSE :

obs_points_shp_path=os.path.join(Inputpath_shapes,obs_points_shapefile_name)

# Here you create a path to the attribute table of obs points
obs_points_table_path=os.path.join(Inputpath_shapes,obs_points_attribute_table_name)

# Here you create a path to the table with the Flow Height for calibration points
excel_table_with_obs=os.path.join(Inputpath_files,file_name_excel_table_obs_points)

# Here you create a path to the input file with the description of the simualtions:
sim_list_file_path=os.path.join(Inputpath_files,sim_list_file_name)

# Mask regions:
# here you crete the path to the shaoefile with the masking region:
mask_shape_path= os.path.join(Inputpath_shapes,mask_shape_name)

###############################################################################
#%% ^  ^  ^  ^  ^  ^  ^  DEFINITION OF FILE LOCATIONS ^  ^  ^  ^  ^  ^  ^  ^  ^
###############################################################################

###############################################################################
#%%                            EXECUTION ARGUMENTS
###############################################################################

# create output folder for Flood Height Rasters  
if not os.path.exists(OutPath_flood_height_ras):
    os.makedirs(OutPath_flood_height_ras)
    print("Output folder didn't exist and was created")

# create output folder for Floodplain Rasters  
if not os.path.exists(OutPath_floodplain_ras):
    os.makedirs(OutPath_floodplain_ras)
    print("Output folder didn't exist and was created")

# create output folder for observations 
if not os.path.exists(OutPath_obs_points):
    os.makedirs(OutPath_obs_points)
    print("Output folder didn't exist and was created")

# create output folder for crossed error rasters:
if not os.path.exists(ce_rasters_path):
    os.makedirs(ce_rasters_path)
    print("Output folder didn't exist and was created")

# create output folder for crossed error tables:
if not os.path.exists(ce_table_path):
    os.makedirs(ce_table_path)
    print("Output folder for CE tables didn't exist and was created")

#Suffix for naming stream order layers
sfx =  bl_tresh
if "." in bl_tresh:
    sfx = sfx.replace(".","")

#here you convert the treshold area to square meters [m2]
#1 sqkm = 1 000 000 sqm  =   10 ha
bl_tresh = float(bl_tresh) * 1000000

# setting up the Working directory--------------------------------------------
default_path = os.getcwd()
os.chdir(current_working_directory)

#DEM folder path--------------------------------------------------------------
DEM_folder_path=os.path.join(current_working_directory, Inputpath_rasters)

#VEriufication of input rerrain data location:
print ('The location of the input DEM (raw) is:', DEM_folder_path)
print('The name of the input DEM file is:', input_DEM_filename)

#Get initial time
Init_Time=datetime.now()

###############################################################################
#%%                            EXECUTION ARGUMENTS
###############################################################################


###############################################################################
#%%                                                            Nested fucntions
###############################################################################

#******************************************************************************
# FloodPLAIN mapping using a geomorphic algorithm 
# ESRI-based GIS plugin
#-------------------
#version                : 1.0
#authors                : Fernando Nardi, Antonio Annis
#contact                : fernando.nardi@unistrapg.it; antonio.annis@unistrapg.it 
#Research group website : http://www.gistar.org
#******************************************************************************
#    
#/*****************************************************************************
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU General Public License as published by  *
#*   the Free Software Foundation; either version 2 of the License, or     *
#*   (at your option) any later version.                                   *
#*                                                                         *
#******************************************************************************

def generate_floodplain(a,b,suff,preprocessing_folder_path,OutPath_floodplain_ras,OutPath_floodplain_shp,OutPath_files):
    
    #Import system modules
    import sys, string, os, arcpy, math, traceback, glob
    from arcpy.sa import *
    from datetime import datetime
    
    import time
    
    print(' ')
    print('-----------------------------------------')
    print('                   FLOODPLAIN DELINEATION')
    print(' ')


    # Allow output to overwrite...
    arcpy.env.overwriteOutput = True
    
    # Check out the ArcGIS Spatial Analyst extension license
    arcpy.CheckOutExtension("Spatial")
    
    
    #Set up preprocessing folder to extract code name
    os.chdir(preprocessing_folder_path)
    
    #extract the area code:
    Code = glob.glob("*acc")[0][:-4]
    
    # CREATING PREPROCESSING RASTER NAMES--------------------------------------
    
    # These are the neccesary input files:
    # FACC     = Flow accumualtion raster
    # FD       = Flow direction raster 
    # DEM      = Hydrologically filled DEM
    # ACC_BLC  = Contributing area of the stream network
    # DEM_DIFF = Difference between hillsope elevation and the hydrologically connected stream elevation
        
    FACC     = preprocessing_folder_path + "\\"+ Code + "_acc"
    FD       = preprocessing_folder_path + "\\"+ Code + "_dir"
    FILL     = preprocessing_folder_path + "\\"+ Code + "_fill"
    ACC_BLC  = preprocessing_folder_path + "\\"+ Code + "_accblc"
    DEM_DIFF = preprocessing_folder_path + "\\"+ Code + "_diff"
    WAT_SORD = preprocessing_folder_path + "\\"+ Code + "_wsord.shp"

    print("loaded files:")
    print(FACC)      # Raster with Flow accumulation raster
    print(FD)        # Raster with Flow direction raster
    print(FILL)      # Raster with Hydrologically filled DEM
    print(ACC_BLC)   # Raster with Contributive area  for the stream network
    print(DEM_DIFF)  # Raster with Difference between hillsope elevation and the hydrologically connected stream elevation
    print(WAT_SORD)  # Polygon with Watersheds per stream orders
    
    #Getting DEM pixelsize
    pixelsize_ob = arcpy.GetRasterProperties_management (FILL, "CELLSIZEX")
    pixelsize = float( pixelsize_ob.getOutput(0) )
    #calculate the cell area in sqm
    cellarea = pixelsize ** 2                            
    
    # CREATE OUTPUT FILES FOLDER ----------------------------------------------
    
    # create output folder for Floodplain:
    if not os.path.exists(OutPath_floodplain_ras):
        os.makedirs(OutPath_floodplain_ras)
        print("Output folder didn't exist and was created")
    
    if not os.path.exists(OutPath_floodplain_shp):
        os.makedirs(OutPath_floodplain_shp)
        print("Output folder didn't exist and was created")
    
    print("files will be saved at:")
    print(OutPath_floodplain_ras)
    print(OutPath_floodplain_shp)
    print(OutPath_files)
        
    # CREATING OUTPUT FILES NAMES--------------------------------------------------

    # these are the files that will be created
    # Remember that the name lenght for GRID files cannot be more than 10 characters
    # Code is already 2 characters long
    
    #TIFF raster files
    FLOOD_HEIGHT = OutPath_floodplain_ras + "\\"+ Code + r'_'+ suff + "_dep.tif" 
    #ADF raster files    
    WAT_FL    = OutPath_floodplain_ras + "\\"+ Code + "_watfl"
    WAT_HGD   = OutPath_floodplain_ras + "\\"+ Code + "_wathgd"
    FPL_GRD   = OutPath_floodplain_ras + "\\"+ Code + "_fpl"
    FPL_DEPTH = OutPath_floodplain_ras + "\\"+ Code + r'_'+ suff + "_dep" 
    # shapefiles
    FPL1      = OutPath_floodplain_shp + "\\"+ Code + "_fpl1" + suff + ".shp"
    FPL2      = OutPath_floodplain_shp + "\\"+ Code + "_fp2"  + suff + ".shp"
    FPL       = OutPath_floodplain_shp + "\\"+ Code + "_fpl"  + suff + ".shp"
    FPL_ORD   = OutPath_floodplain_shp + "\\"+ Code + "_fpl"  + suff + "_ord.shp"
    
    #txt files
    RES       = OutPath_files + "\\"+ Code + "_"     + suff +'_FPL_Report.txt'   #RESULTS
    
    
    
    print("Files that are gonna be created permanently:")
    
    print(FPL_GRD)   # Raster with terrain elevations for each watershed. Each watershed corresponds to a different Flood Height Value
    print(WAT_FL)    # Raster with  Flood Height Values in cm
    print(WAT_HGD)   # Raster with watersheds for the different Flood Height Values along the stream-network
    
    print(FPL)       # shapefile with the total floodplain area
    print(FPL_ORD)   # shapefile with floodplain polygons divided for each stream order
    
    print(FPL_DEPTH)    # This is the raster with flow heights in adf format
    print(FLOOD_HEIGHT) # This is the raster with flow heights in Tif format
    
    print(RES)       # Txt file with the report of the simulation

    #-----------------------------------------------------------------------------
    #                                                                       START
    #-----------------------------------------------------------------------------
    
    
    print('- Computing water energy levels for each stream network cell...')
    
    # HSR relationship:
    # Flow Height = a * (Drainage_Area)^b
    
    # ACC_BLC = Flow accumulation areas along the stream network cells
    #           ACC_BLC  is a raster in square meters
    # outF =   raster with water levels in centimeters if a and b paramters were callibrated in meters  
    
    # WAT_FL = WATER ENERGY LEVEL in cm  -> co_watfl
    
    outF = a* (Raster(ACC_BLC)**b)*100
    outF.save(WAT_FL)
    
    print('- Generating raster with watersheds for each Flood Height ...')

    # Here you assign the same water level to each hydrologically connected pixel
    # The fucntion Watershed() has a numeric limitation because it can only delineate catchments for integer values
    # for this reason the input is introduce in [cm] so it can represent better the water height variation
    
    #  FD     = Raster with Flow directions
    #  WAT_FL = Raster with Water energy levels in cm
    
    #WAT_HGD  = Raster with watersheds for the different Flood Height Values along the stream-network
    #WAT_HGD -> co_wathgd
    
    outW = Watershed(FD, WAT_FL,  "VALUE")
    outW.save(WAT_HGD)
       
    print('- Calculating floodplain water height...')
    
    #Subtracting the terrain elevation from the water energy levels
    #DEM_DIFF  = Raster with Difference between hillsope elevation and the hydrologically connected stream elevation in cm
    #WAT_HGD   = Raster with watersheds for the different Flood Height Values along the stream-network
    
    #FPL_GRD   = Raster with terrain elevations for each watershed. Each watershed corresponds to a different Flood Height Values
    #FPL_GRD   = This is a mask raster with the floodplain delineation
    
    # When co_diff <= co_wathgd --> 1 otherwise 0
    #FPL_GRD  -> co_fpl
    
    outCon = Con(Raster(DEM_DIFF)<= Raster(WAT_HGD) ,1 )
    outCon.save(FPL_GRD)
        
    #Filter positive values
    #DEM_DIFF   = Raster with Difference between hillsope elevation and the hydrologically connected stream elevation in cm
    #WAT_HGD    = Raster with watersheds for the different Flood Height Values along the stream-network in centimeters
    #WAT_HGD    -> co_wathgd
    
    # When co_diff <= co_wathgd --> (co_wathgd-co_diff) otherwise NaN
    # FPL_DEPTH  = This is the final resutls a.k.a Floodplain raster
    # FPL_DEPTH -> co_sXX_dep
    # There is a numeric problem when converting to meters and therefore this will be saved in centimeters
    outCon = Con(Raster(DEM_DIFF)<= Raster(WAT_HGD) ,Raster(WAT_HGD)-Raster(DEM_DIFF))
    outCon.save(FPL_DEPTH)
    
    # here you save the reuslt as a TIFF file to be able to open it in other 
    # paltforms
    arcpy.CopyRaster_management(FPL_DEPTH, FLOOD_HEIGHT)
    
    print('- Creating floodplain polygon based on raster...')

    #Creating the polyogon from the raster
    arcpy.RasterToPolygon_conversion(FPL_GRD, FPL1,"SIMPLIFY")
    arcpy.EliminatePolygonPart_management(FPL1, FPL2, "AREA", cellarea*10000, "", "CONTAINED_ONLY")
    arcpy.Dissolve_management(FPL2, FPL)
       
    print('- Assigning the Leopold parameters to floodplain polygon...')
    #Assigning the Leopold parameters
    arcpy.AddField_management(FPL, "AREA", "float")
    arcpy.CalculateField_management(FPL, "AREA", "!shape.area@squaremeters!", "PYTHON")
    arcpy.AddField_management(FPL, "a", "float")
    arcpy.CalculateField_management(FPL, "a", "%f" %a, "PYTHON")
    arcpy.AddField_management(FPL, "b", "float")
    arcpy.CalculateField_management(FPL, "b", "%f" %b, "PYTHON")
    
    print('- Splitting the floodplain polygon for each stream order...')
    #Splitting the floodplain poligon for each stream order
    arcpy.Clip_analysis(WAT_SORD, FPL, FPL_ORD)
    arcpy.AddField_management(FPL_ORD, "AREA", "float")
    arcpy.CalculateField_management(FPL_ORD, "AREA", "!shape.area@squaremeters!", "PYTHON")
    
    # Deliting intermediate results    
    arcpy.Delete_management(FPL1)
    arcpy.Delete_management(FPL2)
       
    print('- Writing results log file...')
    print(RES)
    R = open(RES, 'w')    
    R.write("{: <25} {: <20}\n".format("DEM name:", Code))
    R.write("{: <25} {: <20}\n".format("a Leopold parameter", "%.6f" %a))
    R.write("{: <25} {: <20}\n".format("b Leopold parameter", "%.4f" %b))
    R.write("{: <25} {: <20}\n".format("Resolution [m]:", "%.2f" %pixelsize))
    R.close()
        
    print(' ')
    print('-----------------------------------------')
    print('        FLOODPLAIN DELINEATION COMPLETED!')
      
#------------------------------------------------------------------------------
    
def transform_flow_depth_raster_from_cm_to_m(Input_raster_filepath):
      
    #Import system modules
    import arcpy
    import os
    import ntpath
    from arcpy.sa import *
    from datetime import datetime
    
    # Allow output to overwrite...
    arcpy.env.overwriteOutput = True
    
    # Check out the ArcGIS Spatial Analyst extension license
    arcpy.CheckOutExtension("Spatial")
    
    # get input raster name, extension and location
    filename, file_extension = os.path.splitext(Input_raster_filepath)
    file_path_name=filename
    filepath= '\\'.join(Input_raster_filepath.split('\\')[0:-1])
    filename=ntpath.basename(file_path_name)
    
    Input_raster=Raster(Input_raster_filepath)
    
    raster_meters=arcpy.sa.Float(Input_raster)
    raster_meters=raster_meters/100
    
    new_raster_name=filename + r'_m' +file_extension
    new_raster_path=os.path.join(filepath,new_raster_name)
    
    #save the result in a new file
    raster_meters.save(new_raster_path)
    
    print('raster trasnformed to meters succesfully !!')
    
#------------------------------------------------------------------------------
# raster file with flood height predictions 
# shp with points with obs

# Warning !
# This fucntion need the flood height raster to be in cms !
# This only works for GFPLAIN results    
    
def find_RMSE_GFPLAIN_results(raster_filepath,points_filepath):
    print(' ')
    print('       finding RMSE...')
    print(' ')
    
    #Import system modules
    import sys
    import string
    import os
    import math
    import traceback
    import glob
    import pandas as pd
    import numpy as np
    
    import arcpy
    from arcpy.sa import *

    # Allow output to overwrite...
    arcpy.env.overwriteOutput = True
    
    # Check out the ArcGIS Spatial Analyst extension license
    arcpy.CheckOutExtension("Spatial")
    
    #create a temp file to hold the extraction
    RESULT_PATH = '\\'.join(points_filepath.split('\\')[0:-1])
    RESULT_name= r'points_with_values.shp'
    RESULT= os.path.join(RESULT_PATH,RESULT_name)
    
    # here you use the function extract to points from arcgis
    ExtractValuesToPoints(points_filepath,raster_filepath,RESULT,"INTERPOLATE","VALUE_ONLY")
    
    #load the attribute table as a pandas dataframe
    arr = arcpy.da.TableToNumPyArray(RESULT, ('text_ID','FH','RASTERVALU'))
    extraction_df = pd.DataFrame(arr) 
    
    # Deleting the file you don't need anymore  
    arcpy.Delete_management(RESULT)
    
    # Here you repalce the nans for 0
    extraction_df.replace(-9999, 0, inplace=True)   
    
    # Here you convert the Raster values from cm to meters
    extraction_df['RASTERVALU']=extraction_df['RASTERVALU']/100
    
    #Here you add a new column with the value error^2 for each observation
    extraction_df['SE']= (extraction_df['RASTERVALU']-extraction_df['FH'])**2
    
    # Here you fin the sum of all the SE values:
    sumSE= (extraction_df.sum(axis = 0, skipna = True))[3] 
    
    #find the number of observations:
    number_of_observations=len(extraction_df.text_ID)
    
    #here you find  the root mean squared error
    RMSE= np.sqrt(sumSE/number_of_observations)
    print('RMSE value calculated sucessfully !')
    return RMSE
    
#------------------------------------------------------------------------------

def delete_floodplain_files(suff,preprocessing_folder_path,OutPath_floodplain_ras,OutPath_floodplain_shp,OutPath_files):
    
    import shutil
    import sys, string, os, arcpy, math, traceback, glob
    from arcpy.sa import *
    from datetime import datetime
    
    # Allow output to overwrite...
    arcpy.env.overwriteOutput = True
    
    # Check out the ArcGIS Spatial Analyst extension license
    arcpy.CheckOutExtension("Spatial")
    
    #Set up preprocessing folder to extract code name
    os.chdir(preprocessing_folder_path)
    
    #extract the area code:
    Code = glob.glob("*acc")[0][:-4]
    

    # CREATING  FILES NAMES--------------------------------------------------

    # these are the files that will be deleted
    # Remember that the name lenght for GRID files cannot be more than 10 characters
    # Code is already 2 characters long
    
    #TIFF raster files
    FLOOD_HEIGHT = OutPath_floodplain_ras + "\\"+ Code + r'_'+ suff + "_dep.tif" 
    #ADF raster files    
    WAT_FL    = OutPath_floodplain_ras + "\\"+ Code + "_watfl"
    WAT_HGD   = OutPath_floodplain_ras + "\\"+ Code + "_wathgd"
    FPL_GRD   = OutPath_floodplain_ras + "\\"+ Code + "_fpl"
    FPL_DEPTH = OutPath_floodplain_ras + "\\"+ Code + r'_'+ suff + "_dep" 
    # shapefiles
    FPL       = OutPath_floodplain_shp + "\\"+ Code + "_fpl"  + suff + ".shp"
    FPL_ORD   = OutPath_floodplain_shp + "\\"+ Code + "_fpl"  + suff + "_ord.shp"
    
    #Others:
    tfw= OutPath_floodplain_ras + "\\"+ Code + r'_'+ suff + "_dep.tfw"
    auxxml=OutPath_floodplain_ras + "\\"+ Code + r'_'+ suff + "_dep.tif.aux.xml"
    ovr = OutPath_floodplain_ras + "\\"+ Code + r'_'+ suff + "_dep.tif.ovr"
    cpg = OutPath_floodplain_ras + "\\"+ Code + r'_'+ suff + "_dep.tif.vat.cpg"
    dbf = OutPath_floodplain_ras + "\\"+ Code + r'_'+ suff + "_dep.tif.vat.dbf"
    xml = OutPath_floodplain_ras + "\\"+ Code + r'_'+ suff + "_dep.tif.xml"
    
    #Directories
    
    info_dir = OutPath_floodplain_ras + "\\"+ r'info'

    #Files that are gonna be deleted permanently:
    
    #FPL_GRD   # Raster with terrain elevations for each watershed. Each watershed corresponds to a different Flood Height Value
    #WAT_FL    # Raster with  Flood Height Values in cm
    #WAT_HGD   # Raster with watersheds for the different Flood Height Values along the stream-network
    
    #FPL       # shapefile with the total floodplain area
    #FPL_ORD   # shapefile with floodplain polygons divided for each stream order
    
    #FPL_DEPTH    # This is the raster with flow heights in adf format
    #FLOOD_HEIGHT # This is the raster with flow heights in Tif format
    

    #txt file with report
    RES = OutPath_files + "\\"+ Code + "_"     + suff +'_FPL_Report.txt'   #RESULTS
    
    #-----------------------------------------------------------------------------
    #                                                                       START
    #-----------------------------------------------------------------------------
    
    # Deleting Shapefiles     
    arcpy.Delete_management(FPL)
    arcpy.Delete_management(FPL_ORD)
        
    # Deleting rasters GRID/ ADF format
    arcpy.Delete_management(WAT_FL)
    arcpy.Delete_management(WAT_HGD)
    arcpy.Delete_management(FPL_GRD) 
    arcpy.Delete_management(FPL_DEPTH)
    
    #DEleteing directories
    shutil.rmtree(info_dir)
    
    #Files
    
    os.remove(tfw)
    os.remove(auxxml)
    os.remove(ovr)
    
    try:
        os.remove(xml)
    except:
        print("The xml file does not exits !")
    try:
        os.remove(cpg)
    except:
        print("The cpg file does not exits !")
    try:
        os.remove(dbf)
    except:
        print("The .tif.vat.dbf file does not exits !")
    
    os.remove(RES)
    
    print('        DELETION COMPLETED !')
        

#------------------------------------------------------------------------------

# fucntion to generate a  binary raster based on a flood height reaster
    
def create_binary_raster_flood_extent(input_raster_filepath,output_raster_filepath):
        
    # Load raster
    flood_depth_raster= arcpy.sa.Raster(input_raster_filepath)
    
    binary_raster = arcpy.sa.Con(flood_depth_raster >0,1)
    
    binary_raster.save(output_raster_filepath)
    
#------------------------------------------------------------------------------


###############################################################################
#%% Nested functions  ^   ^   ^   ^   ^   ^   ^   ^   ^   ^   ^   ^   ^   ^   ^
###############################################################################

###############################################################################
#%%                       GENERATE  HYDROBASE RASTERS 
###############################################################################
print('')
print('-----------------------------------------')
print('                    HYDROBASE CALCULATION')
print(' ')

print('Time before execution')
print(Init_Time)
time_before_execution = time.time()



# DEM format must be ARCGIS grid
DEM = os.path.join(DEM_folder_path, input_DEM_filename)  

DEM_name = os.path.basename(DEM).split('.')[0] #Name of DEM
DEM_path = os.path.dirname(DEM)                #Path of DEM

# create output folder for Hydrobase:
if not os.path.exists(OutPath_hydrobase):
    os.makedirs(OutPath_hydrobase)
    print("Output folder didn't exist and was created")

print("files will be saved at:")
print(OutPath_hydrobase)
   
# CREATING OUTPUT FILES NAMES--------------------------------------------------

#file names Hydrobase
FILL = OutPath_hydrobase + "\\" +  r'fill'                     #DEM FILLED GRID
FDIR = OutPath_hydrobase + "\\" +  r'dir'                  #FLOW DIRECTION GRID
FACC = OutPath_hydrobase + "\\" +  r'acc'                    #FLOW ACCUMULATION
CONA = OutPath_hydrobase + "\\" +  r'ca'                #CONTRIBUTING AREA GRID
SORD = OutPath_hydrobase + "\\" +  r'So_' + sfx              #STREAM ORDER GRID
SLIN = OutPath_hydrobase + "\\" +  r'Str_l' + sfx +  r'.shp'   #STREAM LINE SHP
#RESULTS LOG
RES =  OutPath_hydrobase + "\\" +  r'_Thresh' + sfx + r'_HB_Results.txt'  #RESULTS

STREAM = OutPath_hydrobase+ "\\"+  r'stream'      #stream network without order

print("Outputs will be saved under the following names:")
print(FILL)
print(FDIR)
print(FACC)
print(CONA)
print(SORD)
print(SLIN)
print(RES)
print(STREAM)

#---------------------------------------------------CREATING OUTPUT FILES NAMES

#-------------------------------------------------------------> HYDROBASE START

arcpy.env.extent = DEM
arcpy.env.mask = DEM
# DEM extent
ext = arcpy.Describe(DEM).extent
# DEM extent area in [km^2]
area_inskm = (ext.width * ext.height)/1000000

#get the cellsize of DEM grid
pixelsize = float( arcpy.GetRasterProperties_management (DEM, "CELLSIZEX").getOutput(0) )
cellarea = pixelsize ** 2
# define cell size and extension for raster calculator
arcpy.env.cellSize = pixelsize
        
#fill the raw DEM
if not arcpy.Exists(FILL):
    print(' - Computing DEM Filling...')
    outFill = Fill (DEM)
    outFill.save(FILL)
    print(' - Computing Flow Direction...')
    
    #calculate the new FLOW DIRECTION
    outFD = FlowDirection(FILL) 
    outFD.save(FDIR)
    elapsed_time = (time.time() - time_before_execution) 
    print('Execution time: ' + str(round(elapsed_time/3600)) + ' hours ' + str(round(elapsed_time/60)%60)+ ' minutes ' + str(round(elapsed_time%60))+' seconds')
    print(' -Flow Direction completed successfully...')                 

    print(' - Computing Flow Accumulation...')
    outFac = FlowAccumulation(FDIR)
    outFac.save(FACC)
    elapsed_time = (time.time() - time_before_execution) 
    print('Execution time: ' + str(round(elapsed_time/3600)) + ' hours ' + str(round(elapsed_time/60)%60)+ ' minutes ' + str(round(elapsed_time%60))+' seconds')
    print(' -Flow Accumulation completed successfully...')                 

  
#calculate the CONTRIBUTING AREA
if not arcpy.Exists(CONA):
    outAA = Raster(FACC) * cellarea 
    outAA.save(CONA)
    
# Extracting stream network
print(' - Computing Stream Network...')
if not arcpy.Exists(SORD):
    outSN = SetNull (CONA, 1,  "VALUE < %f" % bl_tresh )
    outSN.save(STREAM)
    # Calculating stream order grid
    print(' - Computing Stream Order...')
    outSO = StreamOrder(STREAM, FDIR)
    outSO.save(SORD)
    # calculation of stream network shape file
    print(' - Converting Stream to Feature...')
    StreamToFeature(SORD, FDIR, SLIN)
    elapsed_time = (time.time() - time_before_execution)
    print('Execution time: ' + str(round(elapsed_time/3600)) + ' hours ' + str(round(elapsed_time/60)%60)+ ' minutes ' + str(round(elapsed_time%60))+' seconds')
    print(' -Stream Network extracted successfully...')                 
   
# RES is the Txt file with the sumamry of the results
R = open(RES, 'w')    
R.write("{: <25} {: <20}\n".format("DEM name:", DEM_name))
R.write("{: <25} {: <20}\n".format("Threshold area [km^2]:", "%.2f" %(bl_tresh/1000000)))
R.write("{: <25} {: <20}\n".format("Resolution [m]:", "%.2f" %pixelsize))
R.write("{: <25} {: <20}\n".format("Extension [km^2]:", "%.2f" %area_inskm))
  
print(' ')
print('-----------------------------------------')
print('                     HYDROBASE COMPLETED!')

elapsed_time = (time.time() - time_before_execution) 
print('Execution time: ' + str(round(elapsed_time/3600)) + ' hours ' + str(round(elapsed_time/60)%60)+ ' minutes ' + str(round(elapsed_time%60))+' seconds')


###############################################################################
#%%    ^     ^    ^       GENERATE  HYDROBASE RASTERS    ^     ^    ^       ^ 
###############################################################################

###############################################################################
#%%                      GENERATE PREPROCCESING RASTERS
###############################################################################

print('')
print('-----------------------------------------')
print('GFPLAIN PREPROCESSING')
print(' ')

#Creating output folder for preprocessing results
if not os.path.exists(preprocessing_folder_path):
    os.makedirs(preprocessing_folder_path)
    print("Output folder didn't exist and was created")

print("files will be saved at:")
print(preprocessing_folder_path)


# CREATE COPIES OF INPUT RASTERS FROM HYDROBASE--------------------------------

Fd_hydrobase= Raster(FDIR)
Facc_hydrobase= Raster(FACC)
Fill_hydrobase= Raster(FILL)

FD        = preprocessing_folder_path + "\\"+ Code + "_dir"
FACC      = preprocessing_folder_path + "\\"+ Code + "_acc"
FILL      = preprocessing_folder_path + "\\"+ Code + "_fill"

Fd_hydrobase.save(FD)
Facc_hydrobase.save(FACC)
Fill_hydrobase.save(FILL)

# CREATING OUTPUT FILES NAMES--------------------------------------------------
    
#file names Hydrobase
DEM_BL    = preprocessing_folder_path + "\\"+ Code + "_bldem"
DEM_BLcm  = preprocessing_folder_path + "\\"+ Code + "_bldemc"
DEM_BLWAT = preprocessing_folder_path + "\\"+ Code + "_blwat"
DEM_DIFF  = preprocessing_folder_path + "\\"+ Code + "_diff"
ACC_BL    = preprocessing_folder_path + "\\"+ Code + "_accbl"
ACC_BLC   = preprocessing_folder_path + "\\"+ Code + "_accblc"
WAT_ORD   = preprocessing_folder_path + "\\"+ Code + "_word"
WAT_SORD  = preprocessing_folder_path + "\\"+ Code + "_wsord.shp"

#RESULTS LOG
RES       = preprocessing_folder_path + "\\"+ Code + "_Thresh" + sfx +'_FPL_PRE_Results.txt'   


print("Files to be created:")
print(FD)
print(FACC)
print(FILL)
print(DEM_BL)
print(DEM_BLcm)
print(DEM_BLWAT)
print(DEM_DIFF)
print(ACC_BL)
print(ACC_BLC)
print(WAT_ORD)
print(WAT_SORD)
print(RES)


print(' - Computing Flow Accumulation on the stream network...')

# Generates the flow accumulation raster for the stream network
# the treshold criteria needs to be translated to a number of accumulated pixels
# This helpt to celan the FAcc raster because it deletes all the cells with accumualtion values < threshold

# ACC_BL = raster with Flow accumualtion value salong  the  streams >= Treshold value
# ACC_BL-> co_accbl

outA = SetNull (FACC, FACC,  "VALUE < %f" % (bl_tresh/cellarea) )
outA.save(ACC_BL)

print(' - Calculating Contributing Area for all the pixels of  the stream network...')

#Generates a raster with the contributing area of the stream network in sqm 

#ACC_BLC -> co_accblc

outAC = Raster(ACC_BL)*cellarea
outAC.save(ACC_BLC)

print(' - Calculating elevation of the stream network...')

#Generates a raster with elevation values for the stream network in m.a.s.l.
#This is basically a raster conditional to replicate the functionality of "extarct by mask" operation

#Area treshold in m^2
#pixel area in m^2

#DEM_BL = Raster with elevation values in [m.a.s.l]
# DEM_BL ->  co_bldem

outBD = SetNull (FACC, FILL,  "VALUE < %f" % (bl_tresh/cellarea) )
outBD.save(DEM_BL)

#Converts the DEM of the stream network from m.a.s.l to  cm.a.s.l.

#DEM_BLcm -> co_bldemc

outBDc = Raster(DEM_BL) * 100
outBDc.save(DEM_BLcm)

# Generates a raster with different Watersheds for each elevation value of the stream networks in cm.a.s.l.
# The fucntion Watershed() has a numeric limitation because it can only delineate catchments for integer ID values
# for this reason the input is introduce in [cm] so it can represent better topographic variation

# DEM_BLWAT -> co_blwat

outW = Watershed(FDIR, DEM_BLcm,  "VALUE")
outW.save(DEM_BLWAT)

print(' - Calcualting the difference between hillsope elevation and the hydrologically connected stream elevation...')

elapsed_time = (time.time() - time_before_execution) 
print('Execution time: ' + str(round(elapsed_time/3600)) + ' hours ' + str(round(elapsed_time/60)%60)+ ' minutes ' + str(round(elapsed_time%60))+' seconds')

# This is the most important outcome from the Geomorphologic perspective !!!!!
# This raster contains the information neccesary to derivate the shape of the river floodplain
# This raster is the numeric difference between hillsope elevation and the hydrologically connected pixels

#FILL      = hydro-DEM filled
#DEM_BLWAT = Raster with elevation values for hydrologically connected pixels in [cm]

# DEM_DIFF = Raster with the floodplain delineation in [cm]
#            This raster is an absolute distance in [cm]
# DEM_DIFF -> co_diff

outD = Raster(FILL)*100 - Raster(DEM_BLWAT)  # This raster is in cm
outD.save(DEM_DIFF)

print(' - Dividing watershed per stream orders...')

#Watershed divided per stream orders
outW = Watershed(FDIR, SORD,  "VALUE")
outW.save(WAT_ORD)

arcpy.RasterToPolygon_conversion(WAT_ORD, WAT_SORD)

print('- Writing results log file...')
print(RES)

R = open(RES, 'w')    
R.write("{: <25} {: <20}\n".format("DEM name:", Code))
R.write("{: <25} {: <20}\n".format("Threshold area [km^2]:", "%.2f" %(bl_tresh/1000000)))
R.write("{: <25} {: <20}\n".format("Resolution [m]:", "%.2f" %pixelsize))
R.write("{: <25} {: <20}\n".format("Extension [km^2]:", "%.2f" %area_inskm))
R.close()

print(' ')
print('-----------------------------------------')
print('        GFPLAIN PREPROCESSING  COMPLETED!')

elapsed_time = (time.time() - time_before_execution) 
print('Execution time: ' + str(round(elapsed_time/3600)) + ' hours ' + str(round(elapsed_time/60)%60)+ ' minutes ' + str(round(elapsed_time%60))+' seconds')



###############################################################################
#%%     ^     ^    ^    GENERATE PREPROCCESING RASTERS      ^     ^    ^    ^
###############################################################################

###############################################################################
#%%                                                                       Start
############################################################################### 

# Here you load the table with the list of rasters
df_file_list=pd.read_excel(sim_list_file_path)

number_of_simulations=len(df_file_list.ID)

#%%
#
###
########
########### Main Loop  

#Here you initilize the df with the results:

column_names = ["Sim_ID","a", "b", "RMSE","CSI","HR","BIAS","FAR"]
df_results= pd.DataFrame(columns = column_names)

# In this loop you create the floodplain for each pair of (a,b) values and 
# then you extract the flow depth for the calibration points "gauges" 
time_before_execution = time.time()

for x in range(31,number_of_simulations,1):
    
    print('----------------------------------------------------------------------------------')
    # Generate Floodplain------------------------------------------------------
    
    Current_ID=str(df_file_list['ID'][x])
    a= df_file_list['a'][x]
    b= df_file_list['b'][x]
    suff= r's'+str(x+1)
    print(suff + ': ' + Current_ID)
    print('Generating floodplain raster please wait....')
    # a     =   Leopold a parameter
    # b     =   Leopold b parameter
    # suff  =   Suffix of the simulation
                             
    # preprocessing_folder_path   =  Folder Name for Pre-Processing results
    # OutPath_floodplain_ras      =  Folder Name for Floodpain results raster
    # OutPath_floodplain_shp      =  Folder Name for Floodpain results shape
    # OutPath_files               =  Folder Name for simualtions details
    
    generate_floodplain(a,b,suff,preprocessing_folder_path,OutPath_flood_height_ras,OutPath_floodplain_shp,OutPath_files)
          
    #Set up preprocessing folder to extract code name
    os.chdir(preprocessing_folder_path)
        
    #extract the area code:
    Code = glob.glob("*acc")[0][:-4]
    
    #Go back to main directory
    os.chdir(current_working_directory)       
    
    # Here you crete a copy of the flood height raster 
    
    fpl_ras_name = OutPath_flood_height_ras + "\\"+ Code + r'_'+ suff + "_dep.tif" 
    
    raster_filepath=os.path.join(OutPath_flood_height_ras,fpl_ras_name)
    
    # Calculate flood height performance metrics -----------------------------
    
    RMSE=find_RMSE_GFPLAIN_results(raster_filepath,obs_points_shp_path)
    print('RMSE: ' + str(RMSE))
    
    # delete all FILES except FOR flow depth to release memory !
    delete_floodplain_files(suff,preprocessing_folder_path,OutPath_flood_height_ras,OutPath_floodplain_shp,OutPath_files)
    
    # Here you rename the raster with the Flood Height of theentire River Basin
    
    old_name=raster_filepath
    
    new_name=  Current_ID + r'_ERB.tif'
    new_name= os.path.join(OutPath_flood_height_ras,new_name)
    
    os.rename(old_name, new_name)
    
    # Generate flood height raster  in meters ---------------------------------

    # here you crop the raster to the modelling extent and convert the flood 
    # height values to meters 
        
    FH_raster_cm=arcpy.sa.Float(new_name)
    FH_raster_meters=FH_raster_cm/100
    
    # Here you mask the raster to the modelling domain:
    
    GFPLAIN_file_name= Current_ID + r'.tif'
    GFPLAIN_file_path= os.path.join(OutPath_flood_height_ras,GFPLAIN_file_name)
    
    GFPLAIN_raster_meters = ExtractByMask(FH_raster_meters, mask_shape_path)
    
    # save the result in a new file
    GFPLAIN_raster_meters.save(GFPLAIN_file_path)
    
    # Generate binary raster with flood extent---------------------------------
    
    pred_raster_name= Current_ID + r'_fpl.tif'
    pred_raster_path= os.path.join(OutPath_floodplain_ras,pred_raster_name)
    
    create_binary_raster_flood_extent(GFPLAIN_file_path,pred_raster_path)
    
    # Calculate Flood Extent performance metrics------------------------------
        
    # Load the two rasters:
    obs= arcpy.sa.Raster(obs_raster_path)
    pred= arcpy.sa.Raster(pred_raster_path)
    
    #flood hit:     obs = 1  && prediction = 1  ->0 | hit | A
    #flood missed:  obs = 1  && prediction = 0  ->2 | False negative | C
    #dry missed:    obs = 0  && prediction = 1  ->3 | False positive | B
    #dry hit:       obs = 0  && prediction = 0  ->1 | hit | D
    
    
    # Pre-processing :
        
    obs_dry=arcpy.sa.IsNull(obs) # create raster with dry areas OBS
    obs_no_null=obs_dry+1
        
    pred_dry=arcpy.sa.IsNull(pred) # create raster with dry areas PRED
    pred_no_null=pred_dry+1
    
    # analysis
    flood_hit=arcpy.sa.Con(obs == pred,1)
    flood_hit_no_null=arcpy.sa.IsNull(flood_hit)
    
    
    dry_hit=arcpy.sa.Con(obs_no_null == pred_no_null,1)
    dry_hit_no_null=arcpy.sa.IsNull(dry_hit)
    
    dry_missed=pred_no_null-flood_hit_no_null
    dry_missed=arcpy.sa.Con(dry_missed == 1,1)
    dry_missed=arcpy.sa.IsNull(dry_missed)
    
    ce_raster=dry_hit_no_null+flood_hit_no_null+dry_missed
        
    # Here you implement the following crossed error scheme using the 
    # Crossed error raster with 0 | 1 |2| 3 values 
    
    #     c1 | c2
    # r1| A  | B  | Total dry pixels according to prediction: dry_pixels
    # r2| C  | D  | Total flooded pixels according to prediction : flooded_pixels
    #    hits      
    #    missed 
    
    frequencyFields = ["COUNT"]
    summaryFields = ["VALUE"]
    
    out_table=  Current_ID + r'_CE.dbf'
    out_xls= Current_ID + r'_CE.xls'
    
    stats_path=os.path.join(ce_table_path,out_table)
    ce_stats_xls_path=os.path.join(ce_table_path,out_xls)
    
    arcpy.Frequency_analysis(ce_raster,stats_path,frequencyFields, summaryFields)
    arcpy.TableToExcel_conversion(stats_path, ce_stats_xls_path)
       
    df_stats=pd.read_excel(ce_stats_xls_path)
    
    try:
        A= int((df_stats.loc[df_stats['Value'] == 0]).Count)
        B= int((df_stats.loc[df_stats['Value'] == 3]).Count)
        C= int((df_stats.loc[df_stats['Value'] == 2]).Count)
        D= int((df_stats.loc[df_stats['Value'] == 1]).Count)
    except Exception:
        A= int((df_stats.loc[df_stats['VALUE'] == 0]).COUNT)
        B= int((df_stats.loc[df_stats['VALUE'] == 3]).COUNT)
        C= int((df_stats.loc[df_stats['VALUE'] == 2]).COUNT)
        D= int((df_stats.loc[df_stats['VALUE'] == 1]).COUNT)
    
    #print('0 = Flood hit      | A')
    #print('1 = Dry hit        | D')
    #print('2 = false negative | C')
    #print('3 = false positive | B')
    
    # Here you calculate the performance metrics:
    
    CSI=A/(A+B+C)
    HR= (A+D)/(A+B+C+D)
    BIAS=(A+B)/(A+C)
    FAR= B/(A+B)
    
    print('Flood extent performance: ')
    print('CSI: '+str(CSI))
    print('HR: '+str(HR))
    print('BIAS: '+str(BIAS))
    print('FAR: '+str(FAR))
    

    #--------------------------------------------------------------------------
    
    column_names = ["Sim_ID","a", "b", "RMSE","CSI","HR","BIAS","FAR"]
    
    # Here you add the values to the master dataframe:
    df_results=df_results.append({'Sim_ID': Current_ID,
                                  'a': a, 
                                  'b': b,
                                  'RMSE':RMSE,
                                  'CSI':CSI,
                                  'HR':HR,
                                  'BIAS':BIAS,
                                  'FAR':FAR}, ignore_index=True)

    #--------------------------------------------------------------------------
    
    # Here you save the results as an excel file:

    results_file_name= r'results_performance_metrics.csv'

    df_performance_metrics_path=os.path.join(OutPath_files,results_file_name)
    
    df_results.to_csv(df_performance_metrics_path, index=False, encoding='utf-8')

    #--------------------------------------------------------------------------
    
    elapsed_time = (time.time() - time_before_execution) 
    print('Execution time: ' + str(round(elapsed_time/3600)) + ' hours ' + str(round(elapsed_time/60)%60)+ ' minutes ' + str(round(elapsed_time%60))+' seconds')


########### Main Loop 
########
###
##
#%%
    
print(df_results)  
    