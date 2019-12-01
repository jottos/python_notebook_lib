# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

__version__ = "0.1.0"

__all__ = ['is_outlier', 'describe_with_percentiles']

def describe_with_percentiles(df:pd.DataFrame, columns, how_many=10) -> pd.DataFrame:
    '''
    break dataframe into how_many n'ciles

    df       - our data
    columns  - columns we want broken down
    how_many - number of bins to break data into

    returns a 

    '''
    def make_percentiles(how_many):
        return [n/how_many for n in range(how_many)]
    return df[columns].describe(percentiles=make_percentiles(how_many))


def is_outlier(points, thresh=3.5):
    """
    Returns a boolean array with True if points are outliers and False 
    otherwise.

    Parameters:
    -----------
        points : An numobservations by numdimensions array of observations
        thresh : The modified z-score to use as a threshold. Observations with
            a modified z-score (based on the median absolute deviation) greater
            than this value will be classified as outliers.

    Returns:
    --------
        mask : A numobservations-length boolean array.

    References:
    ----------
        Boris Iglewicz and David Hoaglin (1993), "Volume 16: How to Detect and
        Handle Outliers", The ASQC Basic References in Quality Control:
        Statistical Techniques, Edward F. Mykytka, Ph.D., Editor. 

    jos - snarfed this off the intertubes, lost the link
    """
    if len(points.shape) == 1:
        points = points[:,None]
    median = np.median(points, axis=0)
    diff = np.sum((points - median)**2, axis=-1)
    diff = np.sqrt(diff)
    med_abs_deviation = np.median(diff)

    modified_z_score = 0.6745 * diff / med_abs_deviation

    return modified_z_score > thresh        


## !!! Don't change this version, we are deprecated
## !!! new version is in joslib.stats

def regression_plot(data_frame, x_column_name, y_column_name):
    """
    given a data frame and two columns to use, create a scatter diagram and regression line
    do this in normal and log(10) space and plot
    
    data_frame    - pandas data frame with at least two columns that you want to do regression on
    x_column_name - (str) the name of the x column
    y_column_name - (str) the name of the y column

    NOTE: no null/nan values allowed in the x or y columns

    thanks to http://stamfordresearch.com/linear-regression-using-pandas-python/ for basics

    TODO:
    1) ENHANCEMENT: we would like to set the plot size
    2) ENHANCEMENT: report if there are any nan in df (and) remove them NAN will 
       break the regression
    """
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt

    # normal space
    data = data_frame[[x_column_name, y_column_name]]
    # log space
    data_log = np.log10(data)

    # get the linear models (lm) for normal (original) space
    lm_original = np.polyfit(data[x_column_name], data[y_column_name], 1)

    # calculate the y values based on the co-efficients from the model
    r_x, r_y = zip(*((i, i*lm_original[0] + lm_original[1]) for i in data[x_column_name]))

    # Put in to a data frame, to keep is all nice
    lm_original_plot = pd.DataFrame({
    x_column_name : r_x,
    y_column_name : r_y
    })


    # Get the linear models in log space
    lm_log = np.polyfit(data_log[x_column_name], data_log[y_column_name], 1)

    # calculate the y values based on the co-efficients from the model
    r_x, r_y = zip(*((i, i*lm_log[0] + lm_log[1]) for i in data_log[x_column_name]))

    # Put in to a data frame, to keep is all nice
    lm_log_plot = pd.DataFrame({
    x_column_name : r_x,
    y_column_name : r_y
    })


    # Plot stuff, setup to do supplots
    fig, axes = plt.subplots(nrows=1, ncols=2)

    # Plot the original data and model
    data.plot(kind='scatter', color='Blue', x=x_column_name, y=y_column_name, ax=axes[0], title='Normal Space')
    lm_original_plot.plot(kind='line', color='Red', x=x_column_name, y=y_column_name, ax=axes[0])

    # Plot the log transformed data and model
    data_log.plot(kind='scatter', color='Blue', x=x_column_name, y=y_column_name, ax=axes[1], title='Log Space')
    lm_log_plot.plot(kind='line', color='Red', x=x_column_name, y=y_column_name, ax=axes[1])

    plt.show()

