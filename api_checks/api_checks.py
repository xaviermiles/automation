"""
For checking the consistency between Infoshare data and the equivalent data
pulled from the Stats NZ API.

This downloads the Infoshare versions but not the API versions, since the Stats
NZ UAT/nonprod API requires a Stats IP address.
"""
import os, subprocess
import json

import numpy as np
import pandas as pd

from infoshare import download


def tourism(save_dir):
    # Tourism
    print("Tourism")
    tourism_info = {
        'tourism-small': {
            'api_fname': 'ITM441AA.csv',
            'infoshare_fname': 'tourism1.csv'
        },
        'tourism-all': {
            'api_fname': 'ITM441-All.csv',
            'infoshare_fname': 'tourism-all.csv'
        }
    }
    print("\nComparisons:")
    compare_datasets(tourism_info, save_dir)
    
    download.get_infoshare_dataset(
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
    download.get_infoshare_dataset(
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
    

def hlfs(save_dir):
    """
    Coordinate checking for five HLFS datasets
    """
    api_name_to_dataset_name = {
        'HLF347801': "Persons Employed by Sex by Industry, ANZSIC06 (Qrtly-Mar/Jun/Sep/Dec)",
        'HLF348101': "Persons Employed by Sex by Occupation, ANZSCO (Qrtly-Mar/Jun/Sep/Dec)",
        'HLF435301': "Persons Employed by Employment Status by Industry, ANZSIC06 (Qrtly-Mar/Jun/Sep/Dec)",
        'HLF563101': "Multiple Job Holders by Sex by Occupation (Qrtly-Mar/Jun/Sep/Dec)",
        'HLF563201': "Multiple Job Holders by Industry (Qrtly-Mar/Jun/Sep/Dec)"
    }
    # Infoshare download
    # for api_name, dataset_name in api_name_to_dataset_name.items():
    #     download.get_infoshare_dataset(
    #         dataset_ref=(
    #             'Work income and spending',
    #             'Household Labour Force Survey - HLF',
    #             dataset_name
    #         ),
    #         title_to_options='ALL',
    #         dataset_name=f"{api_name}__infoshare",
    #         save_dir=save_dir,
    #         show_status_flags=True
    #     )
    # Compare
    full_info = {
        dataset_name: {
            'api_fname': f"{api_name}.csv",
            'infoshare_fname': f"{api_name}__infoshare.csv"
        }
        for api_name, dataset_name in api_name_to_dataset_name.items()
    }
    compare_datasets(full_info, save_dir)

    
def compare_datasets(datasets_info, data_folder):
    """
    datasets_info should be a dictionary which maps dataset names to an inner
    dictionary of the form:
        {'api_fname': ..., 'infoshare_fname': ...}
    """
    try:
        r = subprocess.check_output([
            "Rscript", "--vanilla", "compare.R",
            "--data_folder", data_folder,
            "--comparisons", json.dumps(datasets_info)
        ])
    except subprocess.CalledProcessError:
        return
    
    results = json.loads(r.decode())
    for dataset_name, info in results.items():
        print(dataset_name, '??', info['equivalent'])


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
    save_dir = "../data/api_checks"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        
    # tourism(save_dir)
    
    hlfs(save_dir)
