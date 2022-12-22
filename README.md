# mvic-calculator

py script for calibrating load cell data and calculating maximal voluntary isometric force (MVIC). 

## Step 1: Importing calibration file 

The cal_file_import function takes a string input that should be a file path to a csv of calibration data from a load cell consisting of two columns: one column of voltage data, and one column of corresponding loads in Newtons. Produces a dataframe of this data to be used later. 

## Step 2: Importing force file

The force_file_import function takes a string input that should be a file path to a csv of collected isometric force data. Produces a dataframe of the raw force-time series. 

## Step 3: Force file conversion

The force_file_conversion takes two dataframes as inputs: the raw force-time curve and the dataframe of calibration data. The offset of the force is calculated over 4,000 samples and used for offset correction. The above-defined lowpass_filter function is then used to filter the offset-corrected force data using a 4th order low-pass Butterworth filter with a default cutoff frequency of 15 Hz. The filtered force data in volts is then converted to force in Newtons using a linear regression model trained on the calibration data. The original force-time curve dataframe is then returned as an output with offset-corrected and fully processed data added as columns. 

## Step 4: Calculating MVIC

The mvic_calculation function accepts the force-time curve as a dataframe input along with other default arguments to calculate the average force in a 500ms moving window between five and 10 seconds, returning the highest average value as the MVIC. The output is a dataframe containing the MVIC in Volts as well as Newtons in addition to the timing/index values over which the calculation occurred. 

## Step 5: Batch processing

The import_list and final_analysis_code functions are optional functions that allow for batch processing of multiple files at once. Import_list is used to identify file paths within a folder that will be used for analysis. The list of file paths are stored as an output which is then used in the final_analysis_code function. The final_analysis_code function will iterate over all of the files in the paths folder, completing steps 2 - 4 and appending the output values to a list. Following the completion of the for loop within the function, the final outputs are converted to a formatted dataframe that can  be exported to a csv.
