# -*- coding: utf-8 -*-
"""
Created on Wed Jul  6 12:27:26 2022

@author: ncoker
"""

import numpy as np
import pandas as pd
from scipy.signal import filtfilt, butter
from pathlib import Path
from sklearn.linear_model import LinearRegression

def cal_file_import(cal_filename): #Defines function to import load cell calibration file
    '''

    Parameters
    ----------
    cal_filename : string
        file path where load cell calibration is stored.

    Returns
    -------
    cal_data : DataFrame
        returns calibration file that will be used to convert MVIC to newtons.

    '''
    cal_data = pd.read_csv(cal_filename,sep = ',',names=['volts','force'],header=0) #Read Load Cell Calibration.csv file as dataframe
    return cal_data #return cal data to use in force conversion

def force_file_import(force_filename): #Defines function to import MVIC file for calculation
    '''
    Parameters
    ----------
    force_filename : string
        file path where MVIC file to be analyzed is stored.

    Returns
    -------
    force_data : DataFrame
        Returns raw force-time curve in volts.

    '''
    force_data = pd.read_csv(force_filename,sep='\t',names=['time','force'],header=0) #Reads in .csv file of force-time data as dataframe
    return force_data #return force-time curve to use for MVIC calculation

def lowpass_filter(force_data, samplefreq = 2222, order = 4, cutoff = 15): #Defines low-pass filter function based on 2222 Hz sampling rate, 4th order, with 15Hz cutoff
    nyquist = samplefreq * 0.5 # Defines the nyquist frequency
    cut = cutoff / nyquist # Expresses cutoff relative to Nyquist frequency
    b,a = butter(order,cut,'lowpass',analog=False) # Generate Butterworth coefficients
    if 'offset_corrected' in force_data.columns: #if offset-corrected data are present, filter them
        force_data['filtered'] = filtfilt(b,a,force_data['offset_corrected']) # apply Butterworth filter to force data, generating filtered data
    else: # if offset-corrected data are not present, filter raw data
        force_data['filtered'] = filtfilt(b,a,force_data['force']) # apply Butterworth filter to raw force, generating filtered force
    return force_data

def force_file_conversion(force_data,cal_data): #define function for converting force from volts to Newtons
    '''
    Parameters
    ----------
    force_data : DataFrame
        force-time curve expressed in volts.
    cal_data : DataFrame
        calibration dataframe consisting of input voltages and weights in N.

    Returns
    -------
    force_data : dataFrame
        Predicts Force values in Newtons using linear regression applied to 
        cal file.

    '''
    force_data['offset_corrected'] = force_data.loc[:,'force'] - force_data.loc[1000:5000,'force'].mean() #offset correct force data based on average value over ~2 seconds
    force_data = lowpass_filter(force_data) # Apply 4th order low-pass Butterworth filter to force data with 15Hz cutoff
    calibration = LinearRegression() # Define linear regression for force prediction based on load cell voltage
    calibration.fit(cal_data['volts'].to_numpy().reshape(-1,1),cal_data['force'].to_numpy().reshape(-1,1)) # Create linear regression fitting cal force against cal voltage
    force_data['force_newtons'] = calibration.predict(force_data['filtered'].to_numpy().reshape(-1,1)) # Convert MVIC force-time curve from volts to Newtons based on cal_data regression
    return force_data

def mvic_calculation(force_data, samplefreq = 2222, calc_window = 0.5, start_time = 5.0, end_time = 10.0): # Define function for MVIC calculation
    '''
    Parameters
    ----------
    force_data : DataFrame
        Dataframe of converted force data from which MVIC will be calculated.
    samplefreq : int, optional
        sampling rate of load cell. The default is 2222.
    calc_window : float, optional
        interval over which force will be averaged for MVIC. The default is 0.5.
    start_time : float, optional
        first sample beyond which subject is contracting. The default is 5.0.
    end_time : float, optional
        End of interval over which subject should be contracting. 
        The default is 10.0.

    Returns
    -------
    mvic : DataFrame
        Dataframe consisting of start/end samples over which MVIC is calculated
        along with corresponding time values, as well as the MVIC in volts and 
        Newtons.

    '''
    i = force_data['time'].searchsorted(start_time,side='right') # Define first sample beyond onset of contraction
    end_sample = force_data['time'].searchsorted((end_time - calc_window),side='left') # Define last sample that could be used as a start point for MVIC calculation
    calc_samples = samplefreq * calc_window # Define the number of samples used for MVIC calculation
    mvic_calc = [] # Create empty list for appending
    while (i <= end_sample): # Begin while loop starting at contraction onset
        window_average = force_data.loc[i:(i+calc_samples),'force_newtons'].mean() # Calculate average force in Newtons over 500 ms from current index
        window_average_raw = force_data.loc[i:(i+calc_samples),'offset_corrected'].mean() # Repeat previous step in volts
        start_index = i #Record starting index for calculation window
        end_index = i + calc_samples #Record end index for calculation window
        start_time = force_data.loc[i,'time'] # Record timing information for starting index
        end_time = force_data.loc[i+calc_samples,'time'] # Record timing information for ending index
        mvic_calc.append([start_index,end_index,start_time,end_time,window_average_raw,window_average]) #append all values to MVIC list
        i += 1 #increase i and repeat until reaching end_sample
    mvic_calc = pd.DataFrame(mvic_calc,columns = ['start_index','end_index','start_time','end_time','mvic','mvic_newtons']) #Convert finalized list to dataframe with labeled columns
    mvic = mvic_calc.loc[mvic_calc['mvic_newtons'].idxmax(),:] # Return the values for the row corresponding to highest force value in Newtons
    return mvic

def import_list(base_path,folder): # Define function for storing all paths to MVIC files in a given subdirectory
    paths = [path for path in Path(base_path+folder).resolve().glob('**/*_MVIC_*.csv')] #Create variable paths, which stores all file paths that contain MVIC in name
    return paths

def final_analysis_code(base_path,folder,cal_path): # Defines function for batch processing of all MVIC files based on functions defined above. 
    cal_data = cal_file_import(cal_path) # import load cell calibration data
    paths = import_list(base_path,folder) # create file paths for all MVIC files in folder
    frame = [] # Generate empty list, frame, which will be used to store file/MVIC information
    for i in range(len(paths)): 
        data = force_file_import(paths[i]) #Import data contained within file "i"
        data = force_file_conversion(data,cal_data) #Convert/filter data contained within file "i" from volts to Newtons
        mvic = mvic_calculation(data) #Calculate MVIC value for file "i"
        frame.append([paths[i],mvic[0],mvic[1],mvic[2],mvic[3],mvic[4],mvic[5]]) # Append file path, start/end index, start/end time, and MVIC in volts/newtons to list
    df = pd.DataFrame(frame,columns=['file', # at end of for loop, convert full list of all analyzed data to dataframe that can be saved to a .csv file. 
                                     'start_index',
                                     'end_index',
                                     'start_time',
                                     'end_time',
                                     'mvic',
                                     'mvic_newtons'])
    return df  
        
