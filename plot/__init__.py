# -*- coding: utf-8 -*-
from typing import List, Set, Dict, Tuple, Optional, ClassVar
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joslib.stats

__version__ = "0.1.0"
__all__ = ['is_outlier', 'regression_plot', 'plot_groups_with_different_colors', 'plot_percentiles']

def plot_percentiles(df:pd.DataFrame, columns, how_many=10, logy=False, figsize:Tuple[float]=(15.0,15.0)) -> None:
    '''
    break dataframe into how_many n'ciles and plot the specified columns as x,y
    scatter. 

    df       - our data
    columns  - columns we want broken down
    how_many - number of bins to break data into
    logy     - ploy y dimension in log space if true

    returns a     cut framed 
    '''
    def make_percentiles(how_many):
        return [n/how_many for n in range(how_many)]
    x = df[columns].describe(percentiles=make_percentiles(how_many))
    x[4:].plot(logy=logy, figsize=figsize)


def plot_groups_with_different_colors(
        grouped_df:pd.core.groupby.generic.DataFrameGroupBy,
        x_name:str, 
        y_name:str,
        figsize:Tuple[float]=(10.0,10.0),
        ax=None,
        legend:bool=True, 
        logplot:bool=False,
        max_groups:int=None,
        title=None,
        marker='.') -> None:
    """
    given a DataFrameGroupBy scatter plot the content coloring each group differently
    
    x_name - column name for x dimension
    y_name - column name for y dimension
    
    figsize - set size of plot, default is pretty big
    legend  - show legend if true
    logplot - plot in log space if true
    max_groups - show ownly this many groups, default is all
    marker  - change the point representation, default is "." == "point", "o" = circle "," = pixel
    

    NOTE: there are only 10 colors so more than 10 groups is no bueno
    NOTE: no null/nan values allowed in the x or y columns

    TODO: make sure types check out in param list, the implied optionals might hurt
    """
    if not ax:
        fig, ax = plt.subplots(figsize=figsize)
    if title:
        ax.set_title(title)
    ax.margins(0.05) # Optional, just adds 5% padding to the autoscaling
    if logplot:
        ax.set_yscale('log')
        ax.set_xscale('log')
    group_count = 0
    for name, group in grouped_df:
        ax.plot(group[x_name], group[y_name], marker=marker, linestyle='', ms=12, label=name)
        group_count += 1
        if max_groups and group_count == max_groups:
            break
    if legend:
        ax.legend()

        
def plot_groups_with_different_colors(
        grouped_df:pd.core.groupby.generic.DataFrameGroupBy,
        x_name:str, 
        y_name:str,
        figsize:Tuple[float]=(10.0,10.0),
        ax=None,
        legend:bool=True, 
        logplot:bool=False,
        max_groups:int=None,
        title=None) -> None:
    """
    given a DataFrameGroupBy scatter plot the content coloring each group differently
    
    x_name - column name for x dimension
    y_name - column name for y dimension
    
    figsize - set size of plot, default is pretty big
    legend  - show legend if true
    logplot - plot in log space if true
    max_groups - show ownly this many groups, default is all

    NOTE: there are only 10 colors so more than 10 groups is no bueno
    NOTE: no null/nan values allowed in the x or y columns

    TODO: make sure types check out in param list, the implied optionals might hurt
    """
    if not ax:
        fig, ax = plt.subplots(figsize=figsize)
    ax.margins(0.05) # Optional, just adds 5% padding to the autoscaling
    if logplot:
        ax.set_yscale('log')
        ax.set_xscale('log')
    group_count = 0
    for name, group in grouped_df:
        #ax.plot(group[x_name], group[y_name], marker='o', linestyle='', ms=12, label=name)
        ax.plot(group[x_name], group[y_name], marker='.', linestyle='', ms=12, label=name)
        group_count += 1
        if max_groups and group_count == max_groups:
            break
    if legend:
        ax.legend()


def regression_plot(data_frame:pd.DataFrame,
                    x_column_name:str,
                    y_column_name:str,
                    figsize:Tuple[float]=(20.0,10.0)) -> None:
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
    fig, axes = plt.subplots(figsize=figsize, nrows=1, ncols=2)

    # Plot the original data and model
    data.plot(kind='scatter', color='Blue', x=x_column_name, y=y_column_name, ax=axes[0], title='Normal Space')
    lm_original_plot.plot(kind='line', color='Red', x=x_column_name, y=y_column_name, ax=axes[0])

    # Plot the log transformed data and model
    data_log.plot(kind='scatter', color='Blue', x=x_column_name, y=y_column_name, ax=axes[1], title='Log Space')
    lm_log_plot.plot(kind='line', color='Red', x=x_column_name, y=y_column_name, ax=axes[1])

    plt.show()

    
