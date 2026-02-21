# Trending Topic Scout

Search GitHub for a topic, calculate the star spread and midpoint, and convert to a momentum temperature.

## Parameters

- topic

## Steps

1. Search GitHub for repositories matching '{topic}', sorted by stars
2. Note the star count of the top result and the lowest result in the list
3. Calculate the spread (difference) between top and bottom using the calculator subtract tool
4. Calculate the midpoint by adding top and bottom star counts, then dividing by 2
5. Convert the midpoint from Celsius to Fahrenheit to gauge topic momentum
6. Present the top repo, bottom repo, spread, midpoint, and momentum temperature (°F)

## Tools Used

- searchRepositories
- subtract
- add
- divide
- celsius_to_fahrenheit
