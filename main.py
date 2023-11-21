import streamlit as st
import altair as alt
import pandas as pd
import numpy as np
    
# Helper functions
def extract_lower_bound(age_group):
    '''Extract the lower bound of an age group.'''
    if '-' in age_group:
        return int(age_group.split(' - ')[0])
    else:
        return 85

# Load the data
df_all = pd.read_csv('all_data.csv')

st.title("Cancer in Belgium")
st.markdown("Data source: [Kankerregister](https://kankerregister.org/)")

# Data prepapration
df_after_2003 = df_all[df_all['Year'] > 2003]
df_latest = df_all[df_all['Year'] == max(df_all['Year'])]

# Most frequent cancers
st.header(f"Top 10 cancer types by gender and age in 2020")
col1, col2 = st.columns(2)

gender = col1.selectbox('Gender', ('All', 'Male', 'Female'))

df_agegroups = pd.DataFrame(df_all['Age'].unique(), columns=['Age'])
df_agegroups['Age_Lower_Bound'] = df_agegroups['Age'].apply(extract_lower_bound)
df_agegroups = df_agegroups.sort_values(by=['Age_Lower_Bound'])
age = col2.selectbox('Age Group', ["All"] + df_agegroups['Age'].tolist())

df_latest_gender_age = df_latest
if gender != 'All':
    df_latest_gender_age = df_latest[df_latest['Gender'] == gender]
if age != 'All':
    df_latest_gender_age = df_latest[df_latest['Age'] == age]

df_cancer_type = df_latest_gender_age.groupby('Name')['Count'].sum()

df_cancer_type = df_cancer_type.sort_values(ascending=False)
df_top10 = df_cancer_type.head(9).reset_index()

other_count = df_cancer_type[9:].sum()

df_other = pd.DataFrame({'Name': ['Other'], 'Count': [other_count]}, index=[9])

df_chart = pd.concat([df_top10, df_other])

df_chart['Sort'] = np.where(df_chart['Name'] == 'Other', df_chart['Count'].min() - 1, df_chart['Count'])

total_count = df_chart['Count'].sum()
df_chart['Percentage'] = df_chart['Count'] / total_count

chart = alt.Chart(df_chart).mark_arc(innerRadius=60, outerRadius=120).encode(
    alt.Theta('Count:Q', stack=True),
    alt.Color('Name:N', sort=alt.EncodingSortField(field='Sort', order='descending'), legend=alt.Legend(labelLimit=0)),
    alt.Order('Sort:Q', sort='descending'),
    tooltip=[alt.Tooltip('Name:N', title='Type'), alt.Tooltip('Count:Q', format=',', title='Count'), alt.Tooltip('Percentage:Q', format='.0%', title='Percentage')]
)
st.altair_chart(chart, use_container_width=True)

# Data by year
df_year = df_after_2003.groupby('Year', as_index=False)['Count'].sum()

chart = alt.Chart(df_year).mark_area().encode(
    alt.X('Year:O', title=None, axis=alt.Axis(labelAngle=0)),
    alt.Y('Count:Q', title=None),
    [alt.Tooltip('Year:O', title='Year'), alt.Tooltip('Count:Q', format=',', title='Count')]
)
st.header("Detected cancer cases by year")
st.altair_chart(chart, use_container_width=True)


# Data by year and gender
df_year_gender = df_after_2003.groupby(['Year', 'Gender'], as_index=False)['Count'].sum()

chart = alt.Chart(df_year_gender).mark_line().encode(
    alt.X('Year:N', title=None, axis=alt.Axis(labelAngle=0)),
    alt.Y('Count:Q', aggregate='sum', title=None),
    alt.Color('Gender:N', legend=alt.Legend(orient='bottom', title=' ', padding=-20)),
    [alt.Tooltip('Year:N', title='Year'), alt.Tooltip('Gender:N', title='Gender'), alt.Tooltip('Count:Q', format=',', title='Count')]
)

st.header("Detected cancer cases by year and gender")
st.altair_chart(chart, use_container_width=True)

# Data by year and gender percentage
df_year_gender['Total'] = df_year_gender.groupby('Year')['Count'].transform('sum')
df_year_gender['Percentage'] = df_year_gender['Count'] / df_year_gender['Total']

chart = alt.Chart(df_year_gender).mark_area().encode(
    alt.X('Year:N', title=None, axis=alt.Axis(labelAngle=0)),
    alt.Y('Count:Q', stack='normalize', title=None),
    alt.Color('Gender:N', legend=alt.Legend(orient='bottom', title=' ', padding=-20)), # Bug in Altair when using legend=None it cuts the y axis
    [alt.Tooltip('Year:N', title='Year'), alt.Tooltip('Gender:N', title='Gender'), alt.Tooltip('Count:Q', format=',', title='Count'), alt.Tooltip('Percentage:Q', format='.1%', title='Percentage')]
)
st.altair_chart(chart, use_container_width=True)

# Data by gender
df_gender = df_latest.groupby(['Gender'])['Count'].sum().reset_index()
df_gender['Percentage'] = df_gender['Count'] / df_gender['Count'].sum()

st.header("Detected cancer cases by gender in 2020")
chart = alt.Chart(df_gender).mark_arc(innerRadius=60, outerRadius=120).encode(
    alt.Theta("Count:Q").stack(True),
    alt.Color("Gender:N"),
    tooltip=[alt.Tooltip('Gender:N', title='Type'), alt.Tooltip('Count:Q', format=',', title='Count'), alt.Tooltip('Percentage:Q', format='.0%', title='Percentage')]
)
st.altair_chart(chart, use_container_width=True)

# Data by age
df_age = df_latest.groupby(['Age'])['Count'].sum().reset_index()
df_age['Age_Lower_Bound'] = df_age['Age'].apply(extract_lower_bound)
df_age = df_age.sort_values(by=['Age_Lower_Bound'])
df_age['Age'] = pd.Categorical(df_age['Age'], categories=df_age['Age'].tolist(), ordered=True)
df_age = df_age.drop(columns=['Age_Lower_Bound'])

st.header("Detected cancer cases by age group in 2020")
chart = alt.Chart(df_age).mark_bar().encode(
    x=alt.X('Age:N', title='Age Group', sort=df_age['Age'].tolist()),
    y=alt.Y('Count:Q', title='Count'),
    tooltip=[alt.Tooltip('Age:N', title='Age Group'), alt.Tooltip('Count:Q', format=',', title='Count')]
)
st.altair_chart(chart, use_container_width=True)

# Data by type
top_types = df_latest.groupby('Name')['Count'].sum().sort_values(ascending=False).head(20)
other_count = df_latest[~df_latest['Name'].isin(top_types.index)]['Count'].sum()
df_type = pd.concat([top_types.reset_index(), pd.DataFrame({'Name': ['Other'], 'Count': [other_count]})], ignore_index=True).sort_values('Count', ascending=False)
df_type = pd.concat([df_type[df_type['Name'] != 'Other'], df_type[df_type['Name'] == 'Other']])

st.header("Detected cancer cases by type in 2020")
chart = alt.Chart(df_type).mark_bar().encode(
    y=alt.Y('Name:N', sort=None, title=None),
    x=alt.X('Count:Q', title=None),
    tooltip=[alt.Tooltip('Name:N', title='Type'), alt.Tooltip('Count:Q', format=',', title='Count')]
).configure_axis(
    labelLimit=400
)
st.altair_chart(chart, use_container_width=True)