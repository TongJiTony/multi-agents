import pandas as pd

file_name = "full_strategy"
df = pd.read_csv(file_name + ".csv")

df['1st_votes_not_nan'] = df['1st_votes'].notna().astype(int)
df['2nd_votes_not_nan'] = df['2nd_votes'].notna().astype(int)
df['3rd_votes_not_nan'] = df['3rd_votes'].notna().astype(int)

eta0 = 1.0
eta1 = 1.5
eta2 = 3.0

n = 6
df['rf_value'] = eta0 * df['1st_votes_not_nan'] * (n - 1 - df['1st_votes'])
df.loc[df['2nd_votes_not_nan'] == 1, 'rf_value'] += eta1 * (n - 1 - 1 - df['2nd_votes'])
df.loc[df['3rd_votes_not_nan'] == 1, 'rf_value'] += eta2 * (n - 1 - 2 - df['3rd_votes'])

min_val = 0
max_val = 20

df['rf_value_norm'] = (df['rf_value'] - min_val) / (max_val - min_val)

print(df)
df.to_csv(file_name + "_value" + ".csv", index=False)