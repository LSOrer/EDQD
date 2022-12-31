import pandas as pd

df = pd.read_csv('data/2easyColumnWithSpaces.csv')

#replacing spaces with underscores in the column names 
def spaces_to_underscore(df):
    df.columns = df.columns.str.replace(' ', '_')
    return df

#print(spaces_to_underscore(df))

#change all values of the df to lower case & return the df
def all_values_lowercase(df):
    lowercase_df = df.apply(lambda x: x.astype(str).str.lower())
    return lowercase_df

#print(all_values_lowercase(df))



#print(df)