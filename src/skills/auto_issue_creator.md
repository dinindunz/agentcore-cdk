# Auto Issue Creator

Analyze a repository's issue-to-star ratio and create a tracking issue if the ratio is high.

## Parameters

- owner/repo

## Steps

1. Get repository details for '{owner/repo}' using getRepository to obtain the star count
2. List open issues for '{owner/repo}' using listIssues with state=open
3. Calculate the issue-to-star ratio: divide issue count by star count using the calculator divide tool
4. Multiply the ratio by 1000 for readability using the calculator multiply tool
5. If the normalized ratio exceeds 5, create a new issue titled 'High issue-to-star ratio detected' with the calculated metrics in the body using createIssue
6. Report the star count, issue count, normalized ratio, and whether an issue was created

## Tools Used

- getRepository
- listIssues
- divide
- multiply
- createIssue
