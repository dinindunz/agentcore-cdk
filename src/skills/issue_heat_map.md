# Issue Heat Map

Analyze a repository's open issues and PRs to calculate a maintenance burden index as a temperature.

## Parameters

- owner/repo

## Steps

1. List open issues for '{owner/repo}' using listIssues with state=open
2. List open pull requests for '{owner/repo}' using listPullRequests with state=open
3. Calculate the issue-to-PR ratio using the calculator divide tool
4. Multiply the ratio by 10 using the calculator multiply tool
5. Convert the result from Fahrenheit to Celsius to get the maintenance burden index
6. Present the issue count, PR count, ratio, and maintenance burden index (°C)

## Tools Used

- listIssues
- listPullRequests
- divide
- multiply
- fahrenheit_to_celsius
