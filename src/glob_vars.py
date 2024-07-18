import datetime as dt
import pandas as pd

TIME_NOW = dt.datetime.now()
PHYSICALS = pd.read_csv(
            "./data/physicals.csv"
        ).set_index('id').to_dict('index')
