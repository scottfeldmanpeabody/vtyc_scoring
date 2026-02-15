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


def parse_enduro_stages(df, race, category):
    times = df.iloc[:, -1]
    stage_names = df.columns.to_list()[-1]

    stage_names = stage_names.replace(r'\\n', ' ').replace('\n', ' ')

    short_race = next((item for item in ['Cochrans', 'Woodstock'] if item in race), None)

    # some spacing in the stage names make it hard to parse
    # hardcode the stage names for now
    # TODO do this better and remove hardcode
    stages = {'Cochrans': {'CatA': ['Rooster', 'Ravine', 'R and R', 'Skullys'],
                           'CatB': ['Rooster', 'Ravine', 'R and R'],
                           'CatC': ['Rooster', 'Ravine', 'R and R'],
                           'Grades56': ['Rooster', 'Ravine', 'R and R']},
              'Woodstock': {'CatA': ['Red Line', 'Red Line 2', 'Hard Style', 'Cloud Drop', 'Schist Creek'],
                            'CatB': ['Red Line', 'Red Line 2', 'Hard Style', 'Cloud Drop'],
                            'CatC': ['Red Line', 'Red Line 2', 'Hard Style', 'Cloud Drop'],
                            'Grades56': ['Red Line', 'Red Line 2', 'Cloud Drop']}
              }

    stage_names = stages[short_race][category]
    stage_count = len(stage_names)

    stage_results = []
    for i, time in enumerate(times):
        try:
            time = time.split(' ')
            if len(time) < stage_count:
                raise('Not enought times to parse')
            result = {}
            for j, stage in enumerate(stage_names):
                result[stage] = time[j]
            stage_results.append(result)
        except Exception as e:
            print(f"Error with time {time}: {e}")
            print('row:')
            print(df.iloc[i])

    stage_results = pd.DataFrame(stage_results)
    df = df.merge(stage_results, left_index=True, right_index=True, how='inner')

    return df, stage_names

def import_results_pdf(local_filename, race, gender, category):

    tables = camelot.read_pdf(local_filename, pages='1', flavor='stream')

    df = tables[0].df

    format = determine_format(race)

    if format not in ['XC', 'Enduro']:
        raise(f'Error: Undefined format: {format}')

    df = df.iloc[3:].reset_index(drop=True)

    # Set the first row of the remaining data as the header
    df.columns = df.iloc[0]
    df = df.drop(df.index[0])

    if format == 'Enduro':
        df, stages = parse_enduro_stages(df, race, category)

    new_columns = ['rank', 'plate', 'name']
    keep_columns = df.columns[3:]
    new_columns.extend(keep_columns)
    df.columns = [x.lower() for x in new_columns]

    df['race'] = race
    df['category'] = category
    df['gender'] = gender
    df['full_cat'] = f'{gender}-{category}'

    for i, row in df.iterrows():
        if row['plate'] == '':
            df.drop(i, inplace=True)

    if format == 'Enduro':
        try:
            df.rename(columns={'name': 'team', 'plate': 'plate_name'}, inplace=True)
            df[['plate', 'name']] = df['plate_name'].str.split(' ', n=1, expand=True)
        except Exception as e:
            print(f"Error fixing names for {race} {gender}-{category}: {e}")


    cols_to_fix = ['name', 'team', 'plate_name']

    # Replace literal \n with a space
    for col in cols_to_fix:
        try:
            df[col] = df[col].astype(str).str.replace(r'\\n', ' ').str.replace('\n', ' ')
        except:
            pass
    df.reset_index(drop=True, inplace=True)

    column_list = ['race', 'full_cat', 'gender', 'category', 'rank', 'plate', 'name', 'team']
    if format == 'Enduro':
        column_list.extend([x.lower() for x in stages])

    try:
        df = df[column_list]
    except Exception as e:
        print(f"Error reordering columns for {race} {gender}-{category}: {e}")

    return df


def collect_all_category_results(race):
    dir = root_dir / f'data/{race}'
    os.chdir(dir)
    files = os.listdir(dir)
    all_cats = pd.DataFrame()
    errors = []
    for filename in files:
        print(f'Processing {filename} ...')
        try:
            if 'startlist' in filename:
                print(f'start list detected. ending.')
                continue
            no_extension = filename.split('.')[0]
            gender = no_extension.split('-')[1]
            cat = no_extension.split('-')[2]
            this_cat = import_results_pdf(filename, race, gender, cat)
            all_cats = pd.concat([all_cats, this_cat], ignore_index=True)
        except Exception as e:
            print(f"Error with filename {filename}: {e}")
    return all_cats


def process_all_races(race_list):
    for race in race_list:
        try:
            short_race = race.split(' ')[1]
            print(f'Processing {short_race} ...')
            df = collect_all_category_results(race)
            df.to_csv(root_dir / f'data/{short_race}.csv', index=False)
            print(f'{short_race} complete.')
        except Exception as e:
            print(f"Error with race {race}: {e}")



if __name__ == "__main__":
    race_list = ['VTYC Ascutney - Aug 16th', 'VTYC Cochrans - Sept 13', 'VTYC Kingdom Trails - Sept 28th',
                 'VTYC Woodstock - Oct 12th', 'VTYC Craftsbury - Oct 19th']
    process_all_races(race_list)
