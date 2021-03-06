# Verify Pull Request Label Action

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/162d73a2aff6478081cdc34ee9ee7b6e)](https://app.codacy.com/manual/jesusvasquez333/verify-pr-label-action?utm_source=github.com&utm_medium=referral&utm_content=jesusvasquez333/verify-pr-label-action&utm_campaign=Badge_Grade_Dashboard)

## Description

This action will verify if a pull request has at least one label from a set of valid labels, as well as no label from a set of invalid labels. The sets of valid and invalid labels are defined by the user and passed as input arguments.

To prevent the merging of an invalid pull request, this action uses either the standard pull request workflow or the status of the GitHub Action check.

### Using the standard pull request workflow

By default, this action uses the standard pull request workflow. In this mode, if the pull request does not contain a label from the set of valid labels, or contains a label from the set of invalid labels, then the action will create a pull request review using the event `REQUEST_CHANGES`; independent reviews are generated for both cases. Otherwise, the action will instead create a pull request review using the event `APPROVE`. In both of these cases the exit code will be `0`, and the GitHub Action check will always succeed.

The `REQUEST_CHANGES` review will prevent the merging of the pull request (if the option `Require pull request reviews before merging` is enabled in the repository) until the `APPROVE` review is generated. After that, the pull request can be merged.

When this action runs, it will look for the previous review done by itself, and it will not repeat the same request again. However, if the option `Dismiss stale pull request approvals when new commits are pushed` is enabled in the repository, previous review will be automatically dismissed and therefore this check will fail, and a new request will always be generated.

**Note**: if you want to use the `Require pull request reviews before merging` to require reviews approval before merging pull requests, then you need to increase the number of `Required approving reviewers` by one, as this check will do an approval when a valid label is present. So, for example, if you want at least one reviewer approval, then set this value to 2.

### Using the GitHub Action check status

On the other hand, the creations of reviews can be disabled by setting the input `disable-reviews` to `true`. In this mode, if the pull request does not contain a label from the set of valid labels, or contains a label from the set of invalid labels, then the action will exit with an error code (`1`), and the GitHub Action check will fail. Otherwise, the action will instead exit with the code `0`, and the GitHub Action check will succeed. In both cases, the action won't create any pull request review.

The failing of the GitHub Action check will prevent the merging of the pull request (if the option `Require status checks to pass before merging` is enabled in the repository) until the check succeeds. After that, the pull request can be merged.

## Note when working with forks

When a pull request is opened from a forked repository, Github actions run with read-only permissions, and so the action won't be able to create a pull request review.

Fortunately, Github recently added a new trigger event `pull_request_target` which behaves in an almost identical way to the `pull_request` event, but the action runs in the base of the pull request and will therefore have write permission. However, as the action runs in the base of the pull request, the pull request number is not available in the environmental variables, and must therefore be passed as an input argument. Please refer to the example usage section for more details.

## Inputs

### `github-token`

**Required** The GitHub token.

### `valid-labels`

**Required** A list of valid labels. It must be a quoted string, with label separated by commas. For example: `'bug, enhancement'`

### `invalid-labels`

**Optional** A list of invalid labels. It must be a quoted string, with label separated by commas. For example: `'help wanted, invalid'`.

### `pull-request-number`

Depending on the trigger condition used, this input is:
*   **Required** when the action is triggered using `pull_request_target`. It is available in the github context as: `${{ github.event.pull_request.number }}`. Or,
*   **Optional** when the action is triggered using `pull_request`. In this case this number is is automatically extracted from the environmental variables.

### `disable-reviews`

**Optional** Set to `true` to disable the creation on pull request reviews, and use the exit code instead.

## Example usage

Normally, in your project you would want to allow PRs both from the same repository as well as forks. In that case, you must use the trigger condition `pull_request_target`, as described in this example:

In your workflow YAML file add these steps:
```yaml
uses: jesusvasquez333/verify-pr-label-action@v1.3.1
with:
    github-token: '${{ secrets.GITHUB_TOKEN }}'
    valid-labels: 'bug, enhancement'
    invalid-labels: 'help wanted, invalid'
    pull-request-number: '${{ github.event.pull_request.number }}'
```

and trigger it with:
```yaml
on:
  pull_request_target:
   types: [opened, labeled, unlabeled, synchronize]
```

The above example should you preferred method. Nevertheless, the trigger condition `pull_request` is also supported, and you can use it instead of `pull_request_target`. This condition, however, works only for PRs from the same repository; its only advantage is that the `pull-request-number` input is not needed in this case and can be omitted. So, if you want to use that condition instead, follow this example:

In your workflow YAML file add this step:
```yaml
uses: jesusvasquez333/verify-pr-label-action@v1.3.1
with:
    github-token: '${{ secrets.GITHUB_TOKEN }}'
    valid-labels: 'bug, enhancement'
    invalid-labels: 'help wanted, invalid'
```

and trigger it with:
```yaml
on:
  pull_request:
   types: [opened, labeled, unlabeled, synchronize]
```

Please note that you must use only **one** trigger condition for your action, either `pull_request_target` or `pull_request`, but not both at the same time.
