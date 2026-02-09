import camelot
from pathlib import Path
import os
import pandas as pd

def import_results_pdf(local_filename, race, category):

    tables = camelot.read_pdf(local_filename, pages='1', flavor='stream')

    df = tables[0].df


    format = determine_format(race)

    if format == 'XC':
        # If you know the table always starts after row 5
        df = df.iloc[3:].reset_index(drop=True)

        # Set the first row of the remaining data as the header
        df.columns = df.iloc[0]
        df = df.drop(df.index[0])
        new_columns = ['Rank', 'Plate', 'Name']
        keep_columns = df.columns[3:]
        new_columns.extend(keep_columns)
        df.columns = new_columns
    elif format == 'Enduro':
        df = df.iloc[3:].reset_index(drop=True)
    else:
        raise(f'Error: Undefined format: {format}')
    df['Race'] = race
    df['Category'] = category
    df = df[['Race', 'Category', 'Rank', 'Plate', 'Name', 'Team', 'Time', 'Points']]

    for i, row in df.iterrows():
        if row['Plate'] == '':
            df.drop(i, inplace=True)

    cols_to_fix = ['Name', 'Team']

    # Replace literal \n with a space
    for col in cols_to_fix:
        df[col] = df[col].astype(str).str.replace(r'\\n', ' ').str.replace('\n', ' ')
    df.reset_index(drop=True, inplace=True)
    print(df)
    return df


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

if __name__ == "__main__":
    file_name = Path(__file__).parent.parent
    race = 'VTYC Ascutney - Aug 16th'
    category = 'F-CatA'
    filename = file_name / f'data/{race}/results-{category}.pdf'
    df = import_results_pdf(filename, race, category)