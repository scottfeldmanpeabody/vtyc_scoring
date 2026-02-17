import pandas as pd
from pathlib import Path
import numpy as np
root_dir = Path(__file__).parent.parent

def _determine_series_category(previous_race):
    previous_race_path = root_dir / f'data/{previous_race}.csv'
    previous_race_df = pd.read_csv(previous_race_path)
    series_category_dict = dict(zip(previous_race_df['name'], previous_race_df['category']))
    return series_category_dict


def determine_series_rank(race, series_category_dict):
    race_path = root_dir / f'data/{race}.csv'
    race_df = pd.read_csv(race_path)
    race_df['series_category'] = race_df['name'].map(series_category_dict)
    race_df.loc[pd.isna(race_df['series_category']), 'series_category'] = race_df['category']
    race_df['category_change'] = np.where(race_df['series_category'] == race_df['category'], False, True)
    race_df['series_gender_category'] = race_df['gender'] + '-' + race_df['series_category']

    changed_category = race_df[race_df['category_change']]['name'].to_list()
    print(f"{len(changed_category)} rider(s) changed categories: {'| '.join(changed_category)}")



    categories = race_df['series_gender_category'].unique()

    series_results = pd.DataFrame()

    # TODO do this better and remove hardcode
    #  maybe reference a single stage dict at least and store as json
    stages = {'Cochrans': {'CatA': ['Rooster', 'Ravine', 'R and R', 'Skullys'],
                           'CatB': ['Rooster', 'Ravine', 'R and R'],
                           'CatC': ['Rooster', 'Ravine', 'R and R'],
                           'Grades56': ['Rooster', 'Ravine', 'R and R']},
              'Woodstock': {'CatA': ['Red Line', 'Hard Style', 'Cloud Drop', 'Schist Creek'],
                            'CatC': ['Red Line', 'Hard Style', 'Cloud Drop'],
                            'CatB': ['Red Line', 'Hard Style', 'Cloud Drop'],
                            'Grades56': ['Red Line', 'Red Line 2', 'Cloud Drop']}
              }
    for category in categories:
        this_df = race_df[race_df['series_gender_category'] == category].copy()
        this_cat = this_df['category'].iloc[0]
        cat_stages = [stage.lower() for stage in stages[race.capitalize()][this_cat]]
        for stage in cat_stages:
            this_cat[stage] = pd.to_timedelta(this_cat[stage], unit='s')
        this_cat['total_time'] = this_cat[cat_stages].sum(axis=1)

        series_results = pd.concat([series_results, this_cat], ignore_index=True)


    return series_results


def score_enduro(race, previous_race):
    """
    'virtual' scoring for enduro race using the series category instead of the category on race day
    :param race: csv file with enduro race to score for series category
    :param previous_race: csv file of prior race used to determine series category
    :return: dataframe containing results of enduro race
    """
    series_category_dict = _determine_series_category(previous_race)
    results = determine_series_rank(race, series_category_dict)

    return results


if __name__ == "__main__":
    race = 'Cochrans'
    previous_race = 'Ascutney'
    enduro_score = score_enduro(race, previous_race)