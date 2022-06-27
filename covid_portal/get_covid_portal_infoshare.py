"""Scrape Infoshare for datasets from COVID-19 data portal

DEPRECATED:
This script is no longer used since we collect the data directly from TSM using the
stored procedures, which is way easier.
"""
import os

import pandas as pd

import utils
from infoshare import download


def get_air_cargo():
    fname_template = "air_cargo_{dataset}"
    dataset_to_obs = {
        'Exports': [
            'FOB (free on board) NZ$(000)',
            'Gross weight (tonnes)'
        ],
        'Imports': [
            'CIF (cost, insurance and freight) NZ$(000)',
            'Gross weight (tonnes)'
        ]
    }

    for dataset, observations in dataset_to_obs.items():
        download.get_infoshare_dataset(
            dataset_ref=(
                'Imports and exports',
                'Overseas Cargo Statistics - OSC',
                f'Total {dataset} by New Zealand Port (Monthly)'
            ),
            title_to_options={
                'New Zealand Port': ['Christchurch Airport', 'Auckland Airport'],
                'Observations': observations,
                'Time': '<2013M01>UNTIL_LATEST_DATETIME<%YM%m>'
            },
            dataset_name=fname_template.format(dataset=dataset),
            save_dir=SAVE_DIR
        )

    print("Merging air cargo")
    merged = None
    for dataset in dataset_to_obs.keys():
        fpath = os.path.join(
            SAVE_DIR, fname_template.format(dataset=dataset) + ".csv")
        df = pd.read_csv(fpath, header=1, index_col=0)
        df.index.names = ['Month']
        df.index = pd.to_datetime(
            df.index, format="%YM%m").strftime('%d/%m/%Y')
        df.columns = [f"{dataset}_{name}" for name in df.columns]

        if merged is not None:
            merged = pd.merge(merged, df, left_index=True, right_index=True)
        else:
            merged = df
        os.remove(fpath)
    out_fpath = os.path.join(
        SAVE_DIR, "COVID-19 - Christchurch Airport traffic statistics.csv"
    )
    merged.to_csv(out_fpath)


def get_sea_cargo():
    fname_template = "sea_cargo_{dataset}"
    dataset_to_obs = {
        'Exports': [
            'FOB (free on board) NZ$(000)',
            'Gross weight (tonnes)'
        ],
        'Imports': [
            'CIF (cost, insurance and freight) NZ$(000)',
            'Gross weight (tonnes)'
        ]
    }

    for dataset, observations in dataset_to_obs.items():
        download.get_infoshare_dataset(
            dataset_ref=(
                'Imports and exports',
                'Overseas Cargo Statistics - OSC',
                f'Total {dataset} by New Zealand Port (Monthly)'
            ),
            title_to_options={
                'New Zealand Port': [
                    'Auckland (sea)', 'Lyttelton (sea)', 'Napier (sea)',
                    'Port Chalmers (sea)', 'Tauranga (sea)', 'Wellington (sea)'
                ],
                'Observations': observations,
                'Time': '<2013M01>UNTIL_LATEST_DATETIME<%YM%m>'
            },
            dataset_name=fname_template.format(dataset=dataset),
            save_dir=SAVE_DIR
        )

    print("Merging sea cargo (and then splitting by port)")
    merged = None
    for dataset in dataset_to_obs.keys():
        fpath = os.path.join(
            SAVE_DIR, fname_template.format(dataset=dataset) + ".csv")
        df = pd.read_csv(fpath, header=[0, 1], index_col=0)
        df.index.names = ['Month']
        df.index = pd.to_datetime(
            df.index, format="%YM%m").strftime('%d/%m/%Y')
        df.columns.names = ['New Zealand Port', 'Observations']
        df = df.stack('New Zealand Port')
        df.columns = [f"{dataset}_{name}" for name in df.columns]

        if merged is not None:
            merged = pd.merge(merged, df, left_index=True, right_index=True)
        else:
            merged = df
        os.remove(fpath)

    ports = df.index.get_level_values('New Zealand Port').unique()
    for port in ports:
        port_mask = merged.index.get_level_values('New Zealand Port') == port
        merged_filt = merged.loc[port_mask, :].droplevel('New Zealand Port')
        out_fpath = os.path.join(
            SAVE_DIR, f"COVID-19 - Sea cargo {port.replace(' (sea)', '')}.csv"
        )
        merged_filt.to_csv(out_fpath)


def get_card_transaction_total_spend():
    fname_template = "ect_total_spend_{name}"
    dataset_to_obs = {
        'Exports': [
            'FOB (free on board) NZ$(000)',
            'Gross weight (tonnes)'
        ],
        'Imports': [
            'CIF (cost, insurance and freight) NZ$(000)',
            'Gross weight (tonnes)'
        ]
    }

    for dataset, observations in dataset_to_obs.items():
        download.get_infoshare_dataset(
            dataset_ref=(
                'Imports and exports',
                'Overseas Cargo Statistics - OSC',
                f'Total {dataset} by New Zealand Port (Monthly)'
            ),
            title_to_options={
                'New Zealand Port': [
                    'Auckland (sea)', 'Lyttelton (sea)', 'Napier (sea)',
                    'Port Chalmers (sea)', 'Tauranga (sea)', 'Wellington (sea)'
                ],
                'Observations': observations,
                'Time': '<2013M01>UNTIL_LATEST_DATETIME<%YM%m>'
            },
            dataset_name=fname_template.format(dataset=dataset),
            save_dir=SAVE_DIR
        )

    for treatment in ['Actual', 'Seasonally adjusted']:
        download.get_infoshare_dataset(
            dataset_ref=(
                'Economic indicators',
                'Electronic Card Transactions (ANZSIC06) - ECT',
                'Total values - Electronic card transactions A/S/T by division (Monthly)'
            ),
            title_to_options={
                'Actual/Seasonally Adjusted/Trend': [treatment],
                'Division': ['Total'],
                'Time': 'USE_LATEST_DATETIME<%YM%m>'
            },
            dataset_name=f"card_transaction_total_spend_values_{treatment}",
            save_dir=SAVE_DIR
        )

    download.get_infoshare_dataset(
        dataset_ref=(
            'Economic indicators',
            'Electronic Card Transactions (ANZSIC06) - ECT',
            'Number of electronic card transactions A/S/T by division (Monthly)'
        ),
        title_to_options={
            'Actual/Seasonally Adjusted/Trend': ['Actual'],
            'Division': ['Total'],
            'Time': 'USE_LATEST_DATETIME<%YM%m>'
        },
        dataset_name='card_transaction_total_spend_number_Actual',
        save_dir=SAVE_DIR
    )


def get_card_transaction_spend_by_industry():
    treatments = ['Actual', 'Seasonally adjusted']
    for treatment in treatments:
        download.get_infoshare_dataset(
            dataset_ref=(
                'Economic indicators',
                'Electronic Card Transactions (ANZSIC06) - ECT',
                'Total values - Electronic card transactions A/S/T by division (Monthly)'
            ),
            title_to_options={
                'Actual/Seasonally Adjusted/Trend': [treatment],
                'Division': ['RTS total industries'],
                'Time': 'USE_LATEST_DATETIME<%YM%m>'
            },
            dataset_name=f"card_transaction_spend_by_industry_total_{treatment}",
            save_dir=SAVE_DIR
        )

        industries = ['Services', 'Non-retail excl. services']
        for industry in industries:
            download.get_infoshare_dataset(
                dataset_ref=(
                    'Economic indicators',
                    'Electronic Card Transactions (ANZSIC06) - ECT',
                    'Values - Electronic card transactions A/S/T by industry group (Monthly)'
                ),
                title_to_options={
                    'Actual/Seasonally Adjusted/Trend': [treatment],
                    'Industry Group': [industry],
                    'Time': 'USE_LATEST_DATETIME<%YM%m>'
                },
                dataset_name=f"card_transaction_spend_by_industry_{industry}_{treatment}",
                save_dir=SAVE_DIR
            )


if __name__ == "__main__":
    SAVE_DIR = os.path.join(os.getcwd(), 'data', 'covid_portal_raw')
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    get_air_cargo()
    get_sea_cargo()
    get_card_transaction_total_spend()
    get_card_transaction_spend_by_industry()
