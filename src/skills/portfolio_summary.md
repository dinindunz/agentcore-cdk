# Portfolio Summary

List your GitHub repositories, calculate total and average stars, and derive a portfolio temperature.

## Parameters

None

## Steps

1. List the authenticated user's repositories using listAuthenticatedUserRepos
2. Accumulate the total star count across all repos using the calculator add tool
3. Calculate the average stars per repo using the calculator divide tool
4. Convert the average stars from Celsius to Fahrenheit as a portfolio temperature
5. Present a summary with total repos, total stars, average stars, and portfolio temperature (°F)

## Tools Used

- listAuthenticatedUserRepos
- add
- divide
- celsius_to_fahrenheit
