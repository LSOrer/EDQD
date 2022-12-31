import pandas as pd

df = pd.read_csv('data/2easyOneDouble.csv')

#search every row of a dataframe for the most n-common values
#return a list with the most common values
def most_common_values(df, n):
    common_values = []
    for i in df:
        common_values.append(df[i].value_counts().head(n))
    return common_values

#search a dataframe for the most n-common rows
#return a list with the most common rows
def most_common_rows(df, n):
    common_rows = []
    for i in df:
        common_rows = df[df.columns].value_counts().head(n)
    return common_rows

#print(most_common_rows(df,2))

#number of items in each container 
def items_in_container(df):
    items = []
    for i in df:
        items = df.apply(len)
    return items

#print(items_in_container(df))

#length of characters/numbers in n rows in the dataframe 
def length_of_items(df, n):
    item_length = df.applymap(lambda x: len(str(x))).head(n)
    return item_length

#print(length_of_items(df,3))

#search for and return the minimum values of all columns
def minimum_value(df):
    smallest = df.apply(pd.Series.min)
    return smallest

#print(minimum_value(df))

def maximum_value(df):
    largest = df.apply(pd.Series.max)
    return largest

#print(maximum_value(df))