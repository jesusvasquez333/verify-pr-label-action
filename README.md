# Verify Pull Request Label Action

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/162d73a2aff6478081cdc34ee9ee7b6e)](https://app.codacy.com/manual/jesusvasquez333/verify-pr-label-action?utm_source=github.com&utm_medium=referral&utm_content=jesusvasquez333/verify-pr-label-action&utm_campaign=Badge_Grade_Dashboard)

## Description

This action will verify if a pull request has at least one label from a set of valid labels. The set of valid labels is defined by the user and passed as an input argument.

If the pull request does not contain a label from the set of valid labels, then the action will create a pull request review using the event `REQUEST_CHANGES`. On the other hand, if a valid label is present in the pull request, the action will instead create a pull request review using the event `APPROVE`. In both of these cases the exit code will be `0`, and the GitHub check will succeed.

This action uses the pull request workflow to prevent the merging of a pull request without a valid label, instead of the status of the GitHub checks. The reason for this is that GitHub workflows will run independent checks for different trigger conditions, instead of grouping them together. For example, consider that the action is triggered by `pull_request`'s types `opened` and `labeled`, then if a pull request is opened without adding a valid label at the time of creating the pull request, then that event will trigger a check that should fail; however, adding later a valid label to the pull request will just trigger a **new** check which will succeed, but the first check will remain in the failed state (and the pull request merge will be blocked if the option `Require status checks to pass before merging` is enabled in the repository).

Instead, consider the same example, the action is triggered by `pull_request`'s types `opened` and `labeled`, then if a pull request is opened without adding a valid label at the time of creating the pull request, then that event will trigger a check that will succeed, but will crate a pull request review, requesting for changes. The pull request review will prevent the merging of the pull request (if the option `Require pull request reviews before merging` is enabled in the repository) in this case. Adding a valid label to the repository will then trigger a **new** action which will succeed as well, but in this case it will create a new pull request review, approving the pull request. After this, the pull request can be merged.

When this action runs, it will look for the previous review done by this action. If it finds it, it will check if it was approved or if it requested changes, and it will not repeat the same request again. However, if the option `Dismiss stale pull request approvals when new commits are pushed` is enabled in the repository, previous review will be automatically dismissed and therefore this check will fail, and a new request will always be generated.

**Note**: if you want to use the `Require pull request reviews before merging` to require reviews approval before merging pull requests, then you need to increase the number of `Required approving reviewers` by one, as this check will do an approval when a valid label is present. So, for example, if you want at least one reviewer approval, then set this value to 2.

## Note when working with forks

When a pull request is opened from a forked repository, Github actions run with read-only permissions, and so the action won't be able to create a pull request review.

Fortunately, Github recently added a new trigger event `pull_request_target` which behaves in an almost identical way to the `pull_request` event, but the action runs in the base of the pull request and will therefore have write permission. However, as the action runs in the base of the pull request, the pull request number is not available in the environmental variables, and must therefore be passed as an input argument. Please refer to the example usage section for more details.

## Inputs

### `github-token`

**Required** The GitHub token.

### `valid-labels`

**Required** A list of valid labels. It must be a quoted string, with label separated by commas. For example: `'bug, enhancement'`

### `pull-request-number`

**Optional** The pull request number, available in the github context: `${{ github.event.pull_request.number }}`. This number is automatically extracted from the environmental variables when the action triggers on `pull_request`. However, when the trigger used is `pull_request_target`, then this input must be used.

## Example usage

### If you want to allow PRs from forks

If you want to allow PRs from anywhere, including forks, then you can use this example. These instructions will work even if you are not going to work with forks.

In your workflow YAML file add these steps:
```yaml
uses: jesusvasquez333/verify-pr-label-action@v1.3.1
with:
    github-token: '${{ secrets.GITHUB_TOKEN }}'
    valid-labels: 'bug, enhancement'
    pull-request-number: '${{ github.event.pull_request.number }}'
```

and trigger it with:
```yaml
on:
  pull_request_target:
   types: [opened, labeled, unlabeled, synchronize]
```

### If you plan to only open PRs from the same repository

If you plan to open PR only from the same repository, you can use this example, which requires one less input value. However, this won't work if you open a PR from a fork.

In your workflow YAML file add this step:
```yaml
uses: jesusvasquez333/verify-pr-label-action@v1.3.1
with:
    github-token: '${{ secrets.GITHUB_TOKEN }}'
    valid-labels: 'bug, enhancement'
```

and trigger it with:
```yaml
on:
  pull_request:
   types: [opened, labeled, unlabeled, synchronize]
```
