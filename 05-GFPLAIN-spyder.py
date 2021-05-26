# -*- coding: utf-8 -*-
"""
Created on Thu Sep 24 14:29:30 2020

@author: uqgpere2

# this scripts run GFPLAIN algorithm to delineate a river floodplain based on a DEM
"""

###############################################################################
# %%                       PACKAGES YOU NEED TO LOAD
###############################################################################

import sys
import string
import os
import arcpy
import math
import traceback
import glob
from arcpy.sa import *
from datetime import datetime

###############################################################################
#%%  ^  ^  ^  ^  ^  ^  ^   PACKAGES YOU NEED TO LOAD       ^  ^  ^  ^  ^  ^  ^ 
###############################################################################

###############################################################################
#%%                             CHECK license
###############################################################################

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")

# Allow output to overwrite...
arcpy.env.overwriteOutput = True

###############################################################################
#%%  ^  ^  ^  ^  ^  ^  ^         CHECK license  ^  ^  ^  ^  ^  ^  ^  
###############################################################################

###############################################################################
# %%                                                           Input parameters
###############################################################################


# threshold area [Square kilometers] for stream network
bl_tresh = r'0.1'                                                
print ('The threshold area for flow accumulation is: [Sqkm]', bl_tresh)


#                                HSR calibration:
# R fitted
a     =  float(0.0003)                                   # Leopold a parameter
b     =  float(0.3721)                                   # Leopold b parameter
                       
suff  =  r'T100'                                    # suffix of the simulation

###############################################################################
#%%    ^  ^  ^  ^  ^  ^  ^    Input parameters    ^  ^  ^  ^  ^  ^  ^  ^  ^  ^  ^  
###############################################################################

###############################################################################
#%%                       DEFINITION OF FILE LOCATIONS
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
Flood_Plain_Folder_name = "FLOODPLAIN"         

# FOLDER PATHS-----------------------------------------------------------------

#  #  #  #  #
#  Inputs
# #  #  #  #

# Path to input files:
Inputpath_files= os.path.join(current_working_directory,Input_files_folder_name)

# Path to input shapes:
Inputpath_shapes= os.path.join(current_working_directory,Input_shapes_folder_name)

# Path to input rasters:
Inputpath_rasters= os.path.join(current_working_directory,Input_rasters_folder_name)

# Path to files results:
OutPath_files= os.path.join(current_working_directory,Output_files_folder_name)

#  #  #  #  #
#  Outputs
# #  #  #  #

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

# PREPROCESSING folder locations:
OutPath_Preprocessing= os.path.join(OutPath_PP, Pre_Procesing_Folder_name) 

# FLOODPLAIN locations

OutPath_floodplain_ras= os.path.join(OutPath_rasters,Flood_Plain_Folder_name) 

OutPath_floodplain_shp=os.path.join(OutPath_shapes,Flood_Plain_Folder_name) 

###############################################################################
# ^  ^  ^  ^  ^  ^  ^  DEFINITION OF FILE LOCATIONS ^  ^  ^  ^  ^  ^  ^  ^  ^
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


#------------------------------------------------------------------------------

def pre_proecess_DEM(bl_tresh,current_working_directory,loading_folder_name,saving_folder_name,input_raster_filename):


    print('')
    print('-----------------------------------------')
    print('HYDROBASE CALCULATION')
    print(' ')
    
    
    HB_Folder_name = "HYDROBASE"   # Folder Name for HYDROBASE results
    
    #  PREAPRING INPUTS FOR HYDROBASE ---------------------------------------------
    
    os.chdir(current_working_directory)
    loading_folder_path=os.path.join(current_working_directory, loading_folder_name)
    saving_folder_path=os.path.join(current_working_directory, saving_folder_name)
    
    print ('The location of the input DEM (raw) is:', loading_folder_path)
    print('The name of the input DEM file is:', input_raster_filename)
    
    # DEM route input format must be grid
    DEM = os.path.join(loading_folder_path, input_raster_filename)  
    
    #Get initial time
    Init_Time=datetime.now()
    print(Init_Time)
    print(DEM)
    #Suffix for stream order layer
    sfx =  bl_tresh
    if "." in bl_tresh:
        sfx = sfx.replace(".","")
    #  PREAPRING INPUTS FOR HYDROBASE ---------------------------------------------    
        
    # CREATING THE FOLDER FOR THE OUTPUTS------------------------------------------ 
    DEM_name = os.path.basename(DEM).split('.')[0] #Name of DEM
    DEM_path = os.path.dirname(DEM)                #Path of DEM
    
    print(DEM_name)
    print(DEM_path)
    
    OutPath =   os.path.join(saving_folder_path,HB_Folder_name)
    
    if not os.path.exists(OutPath):
        os.makedirs(OutPath)
        print("Output folder didn't exist and was created")
    # CREATING THE FOLDER FOR THE OUTPUTS-----------------------------------------
       
    # OUTPUT FILES NAME------------------------------------------------------------
    
    #Permanent files   
    FILL = OutPath + "\\" +  r'fill'                        #DEM FILLED GRID
    FDIR = OutPath + "\\" +  r'dir'                     #FLOW DIRECTION GRID
    FACC = OutPath + "\\" +  r'acc'                       #FLOW ACCUMULATION
    CONA = OutPath + "\\" +  r'ca'                   #CONTRIBUTING AREA GRID
    SORD = OutPath + "\\" +  r'So_' + sfx                 #STREAM ORDER GRID
    SLIN = OutPath + "\\" +  r'Str_l' + sfx +  r'.shp'      #STREAM LINE SHP
    RES =  OutPath + "\\" +  r'_Thresh' + sfx + r'_HB_Results.txt'  #RESULTS
    #temporary file names
    STREAM = OutPath+ "\\"+  r'stream'           #stream network without order
    print("Outputs will be saved under the following names:")
    print(FILL)
    print(FDIR)
    print(FACC)
    print(CONA)
    print(SORD)
    print(SLIN)
    print(RES)
    
    
    # OUTPUT FILES NAME------------------------------------------------------------
    
    #-------------------------------------------------------------------------START
    
    arcpy.env.extent = DEM
    arcpy.env.mask = DEM
    
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
        print(' - Computing Flow Accumulation...')
        outFac = FlowAccumulation(FDIR)
        outFac.save(FACC)               
    
    #calculate the CONTRIBUTING AREA
    if not arcpy.Exists(CONA):
        outTimes = Raster(FACC) * cellarea 
        outTimes.save(CONA)
    # treshold area in m^2
    bl_tresh = float(bl_tresh) * 1000000
    
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
       
    arcpy.Delete_management(STREAM)
    #arcpy.Delete_management(CONA)
    
    Fin_Time=datetime.now()
    
    
    ext = arcpy.Describe(DEM).extent
    area = (ext.width * ext.height)/1000000
    IT= Init_Time.strftime('%Y-%m-%d %H:%M:%S')
    FT= Fin_Time.strftime('%Y-%m-%d %H:%M:%S')
    Sim_Time = (Fin_Time - Init_Time)
    import datetime
    Sim_Time = Sim_Time-datetime.timedelta(microseconds=Sim_Time.microseconds)
    print('Start time:', IT)
    print('End time:', FT)
    
    R = open(RES, 'w')    
    R.write("{: <25} {: <20}\n".format("DEM name:", DEM_name))
    R.write("{: <25} {: <20}\n".format("Threshold area [km^2]:", "%.2f" %(bl_tresh/1000000)))
    R.write("{: <25} {: <20}\n".format("Resolution [m]:", "%.2f" %pixelsize))
    R.write("{: <25} {: <20}\n".format("Extension [km^2]:", "%.2f" %area))
    R.write("{: <25} {: <20}\n".format("Initial simulation time:", IT))
    R.write("{: <25} {: <20}\n".format("Final simulation time:", FT))
    R.write("{: <25} {: <20}\n".format("Simulation time:", Sim_Time))
    R.close()
            
    print(' ')
    print('HYDROBASE COMPLETED!')
    
#-----------------------------------------------------------------------------

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

    time_before_execution = time.time()
    
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
    
    elapsed_time = (time.time() - time_before_execution) 
    print('Execution time floodplain delineation: ' + str(round(elapsed_time/3600)) + ' hours ' + str(round(elapsed_time/60)%60)+ ' minutes ' + str(round(elapsed_time%60))+' seconds')
    
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
    
    elapsed_time = (time.time() - time_before_execution) 
    print('Execution time floodplain delineation: ' + str(round(elapsed_time/3600)) + ' hours ' + str(round(elapsed_time/60)%60)+ ' minutes ' + str(round(elapsed_time%60))+' seconds')
    
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
    
    elapsed_time = (time.time() - time_before_execution) 
    print('Execution time floodplain delineation: ' + str(round(elapsed_time/3600)) + ' hours ' + str(round(elapsed_time/60)%60)+ ' minutes ' + str(round(elapsed_time%60))+' seconds')
    
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
    elapsed_time = (time.time() - time_before_execution) 
    print('Execution time floodplain delineation: ' + str(round(elapsed_time/3600)) + ' hours ' + str(round(elapsed_time/60)%60)+ ' minutes ' + str(round(elapsed_time%60))+' seconds')
    
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
    
    elapsed_time = (time.time() - time_before_execution) 
    print('Execution time floodplain delineation: ' + str(round(elapsed_time/3600)) + ' hours ' + str(round(elapsed_time/60)%60)+ ' minutes ' + str(round(elapsed_time%60))+' seconds') 
    
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
    
def find_RMSE_GFPLAIN_results(raster_filepath,points_filepath):
    print(' ')
    print('       finding RSME...')
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
    
    # here you use the fucntion extract to points from arcgis
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
    RSME= np.sqrt(sumSE/number_of_observations)
    print('RSME value calulated sucessfully')
    return RSME
    
#------------------------------------------------------------------------------
    
###############################################################################
#%% Nested fucntions  ^   ^   ^   ^   ^   ^   ^   ^   ^   ^   ^   ^   ^   ^   ^
###############################################################################

###############################################################################
#%%                    DELINEATE FLOODPLAIN USING GFPLAIN
###############################################################################

# This function delineates the floodplain based on the following parameters

# a     =   Leopold a parameter
# b     =   Leopold b parameter
# suff  =   Suffix of the simulation
                         
# OutPath_Preprocessing   =  Folder Name for Pre-Processing results
# OutPath_floodplain      =  Folder Name for Floodpain results

generate_floodplain(a,b,suff,OutPath_Preprocessing,OutPath_floodplain_ras,OutPath_floodplain_shp,OutPath_files)
 
#extract the area code:
Code = glob.glob("*acc")[0][:-4]

fpl_ras_name = OutPath_floodplain_ras + "\\"+ Code + r'_'+ suff + "_dep.tif" 

raster_filepath=os.path.join(OutPath_floodplain_ras,fpl_ras_name)

transform_flow_depth_raster_from_cm_to_m(raster_filepath)

# delete_floodplain_files(suff,OutPath_Preprocessing,OutPath_floodplain_ras,OutPath_floodplain_shp,OutPath_files)
###############################################################################
#%%      ^     ^    ^   DELINEATE FLOODPLAIN USING GFPLAIN     ^     ^    ^    ^
###############################################################################

###############################################################################
#%%                      FIND RMSE for the group of points
###############################################################################

points_namefile=r'calibration_points_GFPLAIN.shp'
points_filepath=os.path.join(Inputpath_shapes,points_namefile)

#Set up preprocessing folder to extract code name
os.chdir(OutPath_Preprocessing)
   
RSME=find_RMSE_GFPLAIN_results(raster_filepath,points_filepath)

#Go back to main directory
os.chdir(current_working_directory)       

print(RSME)
###############################################################################
#   ^  ^  ^  ^  ^FIND RMSE for the group of points^   ^  ^  ^  ^ 
###############################################################################