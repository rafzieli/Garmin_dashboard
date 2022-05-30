import pandas as pd
import numpy as np
import os
from datetime import datetime
from datetime import timedelta
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
pd.set_option('display.max_rows', 100)
pd.options.mode.chained_assignment = None  # default='warn'

# assign path
path, dirs, files = next(os.walk("./data/"))
file_count = len(files)

#create a list of names from files
names_list = [name[:-4] for name in files]



#load all files to data frames
df_dict = {}
for name in names_list:
    df_dict['df_%s' % name] = pd.read_csv("./data/"+name+'.csv')
    df_dict['df_%s' % name]['Athlete'] = '%s' % name

#create a data frame with all data concatenated
df_all = pd.concat(df_dict[name] for name in list(df_dict.keys()))
#df_all = df_all.set_index('Athlete')


# as we have our .csv files in different language and number of columns we can't silmply rename columns while impoting data
# thats why I choosed only columns with important data, and then will fill NaN values in english-named columns with vlaues
# from polish-named ones

important_columns_en = ['Athlete', 'Activity Type', 'Date', 'Title', 'Distance', 'Calories', 'Time', 'Avg HR', 'Max HR',
                        'Avg Run Cadence', 'Max Run Cadence', 'Avg Pace', 'Best Pace', 'Total Ascent', 'Total Descent',
                        'Best Lap Time', 'Number of Laps', 'Moving Time', 'Elapsed Time', 'Min Elevation',
                        'Max Elevation']
important_columns_pl = ['Athlete', 'Typ aktywności', 'Data', 'Tytuł', 'Dystans', 'Kalorie', 'Czas', 'Średnie tętno', 'Maksymalne tętno',
                         'Średni rytm biegu', 'Maksymalny rytm biegu', 'Średnia prędkość', 'Maksymalna prędkość',
                         'Całkowity wznios', 'Całkowity spadek', 'Czas najlepszego okrążenia', 'Liczba okrążeń',
                         'Czas ruchu', 'Upłynęło czasu', 'Minimalna wysokość', 'Maksymalna wysokość']

# we creat dict to loop over it

en_pl_dict = dict(zip(important_columns_en,important_columns_pl))

for key, value in en_pl_dict.items():
    df_all[key].fillna(df_all[value], inplace=True)

# now we can choose columns that we need for our program

df_all = df_all[important_columns_en]

# lets change colnames to more usefull form

df_all.columns = [item.replace(' ', '') for item in important_columns_en]


# manage with Activity Type names

#df_all.ActivityType.unique()

# mapping names of activites used in app

cycling_activities = {'Cycling': ['Gravel/Unpaved Cycling','Kolarstwo', 'Jazda przełajowa', 'Jazda górska', 'Cyclocross',
                      'Jazda po żwirze/drogach nieutwardz.', 'Indoor Cycling', 'Mountain Biking', 'Road Cycling',
                                 'Cycling']}

running_acitvities = {'Running': ['Trail Running', 'Bieganie', 'Bieg na bieżni', 'Bieg przełajowy', 'Street Running',
                                 'Running','Treadmill Running']}

hiking_activities = {'Hiking': ['Mountaineering', 'Piesze wędrówki', 'Alpinizm', 'Walking', 'Chodzenie', 'Chód sportowy']}

replace_list = [hiking_activities, running_acitvities, cycling_activities]

# normalizing names
for activity in replace_list:
    for key, value in activity.items():
        df_all.loc[:,'ActivityType'] = df_all['ActivityType'].replace(value, key)

df = df_all[df_all.ActivityType.isin(['Hiking', 'Running', 'Cycling'])]

# removing thousends separator
df.Calories = [item.replace(',', '') for item in list(df.Calories)]

numeric_cols = ['Distance', 'Calories', 'AvgHR', 'MaxHR', 'AvgRunCadence', 'MaxRunCadence', 'NumberofLaps', 'TotalAscent',
                'TotalDescent', 'MinElevation', 'MaxElevation']
timedelta_cols = ['Time','BestLapTime', 'MovingTime', 'ElapsedTime']

# converting dtypes
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce', axis=1)
df[timedelta_cols] = df[timedelta_cols].apply(pd.to_timedelta, errors='coerce', axis=1)
df.Date = [date[:10] for date in list(df.Date)]
df.Date = df.Date.apply(pd.to_datetime)

# replacing '--' value winth np.nan

df = df.replace('--', np.nan)

#remove activities with distance less then 1 km - we assume that was missclicks
df = df[df.Distance > 1]

# function to convert timedelta to string (needed to display timedelta in app)
def format_timedelta(td):
    minutes, seconds = divmod(td.seconds + td.days * 86400, 60)
    hours, minutes = divmod(minutes, 60)
    return '{:02d}:{:02d}'.format(minutes, seconds)

# as watches not always deliver us information about avgSpeed/avgPace, we need to calculate it in additional column
df['TimeInSec'] = [item.total_seconds() for item in list(df.Time)]
df['AvgSpeed'] = round((df.Distance / (df.TimeInSec)) * 3600, 1)
df['AvgPaceCountTimedelta'] = df.Time/ df.Distance
df['AvgPaceCountTimedelta'] = pd.to_timedelta(df['AvgPaceCountTimedelta'])
df['AvgPaceCountString'] = df.apply(lambda x: format_timedelta(x['AvgPaceCountTimedelta']), axis=1)

# reset index and remove running activities with pace > 8min
df.reset_index(inplace=True, drop=True)
df.drop(df[(df.ActivityType == 'Running') & (df.AvgPaceCountTimedelta > timedelta(minutes=8))].index, inplace = True)

# removing unnecessary cols
cols_to_drop = ['AvgPace']
df = df.drop(cols_to_drop, axis=1)

#save df to csv
df.to_csv('dashboard_df.csv')