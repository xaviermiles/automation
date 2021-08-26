"""
For checking the consistency between Infoshare data and the equivalent data
pulled from the Stats NZ API

TODO: integrate the R script with this script
"""
import os

import numpy as np
import pandas as pd

import utils


def tourism1(save_dir):
    # For small test
    utils.get_infoshare_dataset(
        dataset_ref=(
            'Tourism',
            'International Travel and Migration - ITM',
            'Estimated migration by direction and country of citizenship, 12/16-month rule (Monthly)'
        ),
        title_to_options={
            'Travel Direction': ['Arrivals','Departures','Net'],
            'Citizenship': ['New Zealand'],
            'Estimate, 12/16-month rule': ['Estimate',
                                           'Seasonally adjusted',
                                           'Trend',
                                           'Standard error of estimate'],
            'Time': 'USE_LATEST_DATETIME<%YM%m>'
        },
        dataset_name="tourism1",
        save_dir=save_dir,
        show_status_flags=True
    )
    
    
def tourism_all(save_dir, dataset_name):
    # For entire dataset
    utils.get_infoshare_dataset(
        dataset_ref=(
            'Tourism',
            'International Travel and Migration - ITM',
            'Estimated migration by direction and country of citizenship, 12/16-month rule (Monthly)'
        ),
        title_to_options={
            'Travel Direction': 'ALL',
            'Citizenship': 'ALL',
            'Estimate, 12/16-month rule': 'ALL',
            'Time': 'ALL'
        },
        dataset_name="tourism-all",
        save_dir=save_dir,
        show_status_flags=True
    )
    

def compare(api_fpath, infoshare_fpath, infoshare_header_idxs):
    """
    *** WIP - Use R script instead ***
    """
    api_copy = pd.read_csv(api_fpath)
    infoshare_copy = pd.read_csv(infoshare_fpath, 
                                 index_col=0,
                                 header=infoshare_header_idxs)
    
    infoshare_long = infoshare_copy.melt(
        var_name=[f"Label{i+1}" for i in range(len(infoshare_copy.columns[0]))], 
        value_name='raw_Value',
        ignore_index=False
    ).reset_index(level=0).rename(columns={'index': 'Period'})
    mask = [' ' not in val_i for val_i in infoshare_long['raw_Value']]
    mask[0] = True
    print(infoshare_long[mask]['raw_Value'].str.split(' ', 1, expand=True))
    # infoshare_long[['Value','Status']] = infoshare_long['raw_Value'].str.split(
    #     ' ', 1, expand=True
    # )
    # infoshare_long['Value'] = [
    #     np.float64(val_i.replace(',', '')) if val_i != '..' else np.nan 
    #     for val_i in infoshare_long['Value']
    # ]
    infoshare_long['Status'] = [
        val_i.split(' ', 1)[1] if ' ' in val_i 
        else np.nan
        for val_i in infoshare_long['raw_Value']
    ]
    infoshare_long['Value'] = [
        val_i.split(' ', 1)[0] if val_i != '..'
        else np.nan
        for val_i in infoshare_long['raw_Value']
    ]
    infoshare_long = infoshare_long.drop(columns='raw_Value')
    
    # print(api_copy[infoshare_long.columns])
    # print(api_copy.info())
    print(infoshare_long.info())
    # print(infoshare_long[infoshare_long['Value'].isnull()])
    
    api_subset = api_copy[infoshare_long.columns]
    print(api_subset.info())


if __name__ == "__main__":
    save_dir = "data/api_checks"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # Download dataset
    tourism_all(save_dir, "tourism-all")
    
    # compare("data/api_checks/ITM441AA-All.csv", 
    #         "data/api_checks/tourism-all.csv",
    #         [1,2,3])
