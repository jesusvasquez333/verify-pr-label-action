# Verify Pull Request Label Action

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/162d73a2aff6478081cdc34ee9ee7b6e)](https://app.codacy.com/manual/jesusvasquez333/verify-pr-label-action?utm_source=github.com&utm_medium=referral&utm_content=jesusvasquez333/verify-pr-label-action&utm_campaign=Badge_Grade_Dashboard)

## Description

This action verifies that there is at least one label for each of the regex that the user passes as an input argument

If the pull request does not have at least one label for each of the regex it will create a pull request review using the 'REQUEST_CHANGES' event. On the contrary, if there is at least one label for each of the regex passed as a parameter, the pull request will be approved with the 'APPROVE' event

This action will be triggered by a series of events chosen by the user. for example, firing the event on type 'OPEN' will allow the developer to be notified when they open a pull request without the required tags.

The use of regex in this module allows labels to be added or removed in an agile way without having to modify the action configuration each time. It also allows to organize the labels under the same pattern, which can be the modified module, the type of task, the urgency of the change.

For example, if you are working with labels of the form 'M.LabelName' where the label identifies the module that was worked on in the pull request, just add the regex 'M\..*' in the action. Then you can easily add a label of the form 'M.secondLabel' to represent another module that was modified, and the regex will keep checking correctly.

## Note when working with forks

When a pull request is opened from a forked repository, Github actions run with read-only permissions, and so the action won't be able to create a pull request review.

Fortunately, Github recently added a new trigger event `pull_request_target` which behaves in an almost identical way to the `pull_request` event, but the action runs in the base of the pull request and will therefore have write permission. However, as the action runs in the base of the pull request, the pull request number is not available in the environmental variables, and must therefore be passed as an input argument. Please refer to the example usage section for more details.

## Inputs

### `github-token`

**Required** The GitHub token.


### `pull-request-number`

**Optional** The pull request number, available in the github context: `${{ github.event.pull_request.number }}`. This number is automatically extracted from the environmental variables when the action triggers on `pull_request`. However, when the trigger used is `pull_request_target`, then this input must be used.

### `regex`

**Required** A list of regular expressions that must be satisfied by at least one tag. It must be a quoted string, with the regex separated by commas.
example: 'M\..*, T\..*, A\..*'

## Example usage

### If you want to allow PRs from forks

If you want to allow PRs from anywhere, including forks, then you can use this example. These instructions will work even if you are not going to work with forks.

In your workflow YAML file add these steps:
```yaml
uses: germanalvarez8/verify-pr-label-action@v1.4.4
with:
    github-token: '${{ secrets.GITHUB_TOKEN }}'
    pull-request-number: '${{ github.event.pull_request.number }}'
    regex: 'M\..*, T\..*, A\..*'
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
uses: germanalvarez8/verify-pr-label-action@v1.4.4
with:
    github-token: '${{ secrets.GITHUB_TOKEN }}'
    regex: 'M\..*, T\..*, A\..*'
```

and trigger it with:
```yaml
on:
  pull_request:
   types: [opened, labeled, unlabeled, synchronize]
```
