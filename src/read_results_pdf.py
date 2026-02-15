import camelot
from pathlib import Path
import os
import pandas as pd
root_dir = Path(__file__).parent.parent


def determine_format(race):
    # race format could be determined by the format of the race results
    #  but that's not really worth doing. So hardcode the format
    format_dict = {'Ascutney': 'XC',
                   'Cochrans': 'Enduro',
                   'Craftsbury': 'XC',
                   'Kingdom Trails': 'XC',
                   'Woodstock': 'Enduro'}

    format = 'unknown'

    for k, v in format_dict.items():
        if k in race:
            format = format_dict.get(k)
            break

    return format


def import_results_pdf(local_filename, race, gender, category):

    tables = camelot.read_pdf(local_filename, pages='1', flavor='stream')

    df = tables[0].df


    format = determine_format(race)

    if format == 'XC':
        # If you know the table always starts after row 5
        df = df.iloc[3:].reset_index(drop=True)

        # Set the first row of the remaining data as the header
        df.columns = df.iloc[0]
        df = df.drop(df.index[0])
        new_columns = ['rank', 'plate', 'name']
        keep_columns = df.columns[3:]
        new_columns.extend(keep_columns)
        df.columns = [x.lower() for x in new_columns]
    elif format == 'Enduro':
        df = df.iloc[3:].reset_index(drop=True)
    else:
        raise(f'Error: Undefined format: {format}')
    df['race'] = race
    df['category'] = category
    df['gender'] = gender
    df['full_cat'] = f'{gender}-{category}'
    df = df[['race', 'full_cat', 'gender', 'category', 'rank', 'plate', 'name', 'team', 'time', 'points']]

    for i, row in df.iterrows():
        if row['plate'] == '':
            df.drop(i, inplace=True)

    cols_to_fix = ['name', 'team']

    # Replace literal \n with a space
    for col in cols_to_fix:
        df[col] = df[col].astype(str).str.replace(r'\\n', ' ').str.replace('\n', ' ')
    df.reset_index(drop=True, inplace=True)
    return df


def collect_all_category_results(race):
    dir = root_dir / f'data/{race}'
    os.chdir(dir)
    files = os.listdir(dir)
    df = pd.DataFrame()
    for filename in files:
        no_extension = filename.split('.')[0]
        gender = no_extension.split('-')[1]
        cat = no_extension.split('-')[2]
        df = pd.concat([df,import_results_pdf(filename, race, gender, cat)], ignore_index=True)
    return df




if __name__ == "__main__":
    race = 'VTYC Ascutney - Aug 16th'  # test XC race
    race = 'VTYC Cochrans - Sept 13th' # test Enduro race
    df = collect_all_category_results(race)
