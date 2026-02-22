# Repo Hotness Rating

Search GitHub for top repositories on a topic and calculate a hotness score using temperature conversion.

## Parameters

- topic

## Steps

1. Search GitHub for repositories matching '{topic}', sorted by stars, limit to 3 results
2. For each result, get the star count using getRepository
3. Divide each star count by 1000 using the calculator divide tool
4. Convert each scaled value from Celsius to Fahrenheit to produce a hotness score
5. Present results in a table with columns: repo name, stars, scaled value, hotness (°F)

## Tools Used

- searchRepositories
- getRepository
- divide
- celsius_to_fahrenheit
