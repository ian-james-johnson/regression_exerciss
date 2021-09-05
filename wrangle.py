# this function be used to access the SQL server
# the user, host, and password will come from importing 'env'

import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer

from env import user, host, password

def get_connection(db, user=user, host=host, password=password):
    '''
    This function creates a connection to the Codeup db.
    It takes db argument as a string name.
    '''
    return f'mysql+pymysql://{user}:{password}@{host}/{db}'

def new_zillow_data():
    '''
    This function gets new telco data from the Codeup database.
    '''
    sql_query = """
                SELECT bedroomcnt, bathroomcnt, calculatedfinishedsquarefeet, taxvaluedollarcnt, yearbuilt, taxamount, fips
                FROM properties_2017
                JOIN propertylandusetype USING (propertylandusetypeid)
                WHERE propertylandusedesc = 'Single Family Residential';
                """
    # Read in dataframe from Codeup
    df = pd.read_sql(sql_query,get_connection('zillow'))
    return df

def get_zillow_data():
        '''
        This function gets telco data from csv, or otherwise from Codeup database.
        '''
        if os.path.isfile('zillow.csv'):
            df = pd.read_csv('zillow.csv', index_col = 0)
        else:
            df = new_zillow_data()
            df.to_csv('zillow.csv')
        return df

def remove_outliers(df, k, col_list):
    '''
    Remove outliers from a list of columns.
    '''
    for col in col_list:
        # Get quartiles
        q1, q3 = df[col].quantile([.25, .75])
        
        # Get interquartile range
        iqr = q3 - q1
        
        upper_bound = q3 + k * iqr
        lower_bound = q1 - k * iqr
        
        # Return the dataframe without the outliers
        df = df[(df[col] > lower_bound) & (df[col] < upper_bound)]
        
        return df


def wrangle_zillow(df):
    # Replace a whitespace sequence or empty with a NaN value 
    # and reassign this manipulation to df.
    df = df.replace(r'^\s*$', np.nan, regex=True)

    # Remove outliers from the dataframe
    df = remove_outliers(df, 1.5, df.columns)

    # fips appears to be a categorical number (i.e. like a zip code)
    # year_built may also be categorical if we aren't looking at age
    df.fips = df.fips.astype(object)
    df.year_built = df.year_built.astype(object)

    # Split the data into train, validate, and test subsets
    train_validate, test = train_test_split(df, test_size=.2, random_state=123)
    train, validate = train_test_split(df, test_size=.3, random_state=123)

    # Need to fill nulls for: year_built, area_sqft, tax_value

    # Create -> Fit -> Use
    # Create the object
    imputer_year = SimpleImputer(strategy='most_frequent')

    # Fit the object to train
    imputer_year.fit(train[['year_built']])

    # Use the object to impute on train, validate, and test subsets
    train[['year_built']]=imputer_year.transform(train[['year_built']])
    validate[['year_built']]=imputer_year.transform(validate[['year_built']])
    test[['year_built']]=imputer_year.transform(test[['year_built']])

    # Now repeat the imputing process for area_sqft
    imputer_area = SimpleImputer(strategy='median')
    imputer_area.fit(train[['area_sqft']])

    train[['area_sqft']]=imputer_area.transform(train[['area_sqft']])
    validate[['area_sqft']]=imputer_area.transform(validate[['area_sqft']])
    test[['area_sqft']]=imputer_area.transform(test[['area_sqft']])

    # Now repeat the imputing process for tax_value
    imputer_tax = SimpleImputer(strategy='median')
    imputer_tax.fit(train[['tax_value']])

    train[['tax_value']]=imputer_tax.transform(train[['tax_value']])
    validate[['tax_value']]=imputer_tax.transform(validate[['tax_value']])
    test[['tax_value']]=imputer_tax.transform(test[['tax_value']])

    return train, validate, test


