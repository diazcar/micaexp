import pandas as pd


def list_of_strings(arg):
    return arg.split(',')


def weekday_profile(
        data: pd.DataFrame,
        week_section: str,
):
    index = data.index.name
    data.reset_index(inplace=True)

    if week_section == 'workweek':
        days_data = data[data[index].dt.weekday < 5]
    if week_section == 'weekend':
        days_data = data[data[index].dt.weekday > 4]

    out_data = pd.DataFrame()
    for col in ['valeur_ref', 'value']:
        grouped_data = days_data[[index, col]].groupby(
            days_data[index].dt.time
            ).mean().drop([index], axis=1)
        out_data = pd.concat(
            [out_data, grouped_data],
            axis=1
        )

    out_data.index.name = 'heure'

    data.set_index(index, inplace=True)

    return out_data


def get_max_min(
        data1: pd.DataFrame,
        data2: pd.DataFrame,
        ):
    if data1.max() > data2.max():
        max = data1.max()
    else:
        max = data2.max()

    if data1.min() > data2.min():
        min = data1.min()
    else:
        min = data2.min()

    return min, max


def mask_duplicates(
    data: pd.DataFrame,
    site_name: str,
    poll_iso: str,
):

    if poll_iso == '24':
        data = data[data['id'].str.contains('PC')]
    if poll_iso == '39':
        data = data[data['id'].str.contains('P2')]
    if poll_iso == '68':
        for id in data.id.unique():
            if f'PM1{site_name[:2]}'.lower() in str(id).lower():
                data_out = data[data['id'].str.contains(f'PM1{site_name[:2]}')]
                break
            else:
                data_out = data[data['id'] == data['id'].unique()[0]]
    return data_out
