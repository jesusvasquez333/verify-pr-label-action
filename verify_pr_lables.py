#!/usr/bin/env python3

import os
import sys
import re
from github import Github

def get_env_var(env_var_name, echo_value=False):
    """Try to get the value from a environmental variable.

    If the values is 'None', then a ValueError exception will
    be thrown.

    Args
    ----
        env_var_name : str
            The name of the environmental variable.
        echo_value : bool
            Print the resulting value.

    Returns
    -------
        value : str
            The value from the environmental variable.
    """
    value=os.environ.get(env_var_name)

    if value is None:
        raise ValueError(f'The environmental variable {env_var_name} is empty!')

    if echo_value:
        print(f"{env_var_name} = {value}")

    return value

# Check if the number of input arguments is correct
if len(sys.argv) != 5:
    raise ValueError('Invalid number of arguments!')

# Get the GitHub token
token=sys.argv[1]

# Get the list of valid labels
valid_labels=sys.argv[2]
print(f'Valid labels are: {valid_labels}')

# Get the PR number
pr_number_str=sys.argv[3]

# Get needed values from the environmental variables
repo_name=get_env_var('GITHUB_REPOSITORY')
github_ref=get_env_var('GITHUB_REF')
github_event_name=get_env_var('GITHUB_EVENT_NAME')

# Create a repository object, using the GitHub token
repo = Github(token).get_repo(repo_name)

# When this actions runs on a "pull_reques_target" event, the pull request number is not
# available in the environmental variables; in that case it must be defined as an input
# value. Otherwise, we will extract it from the 'GITHUB_REF' variable.
if github_event_name == 'pull_request_target':
    # Verify the passed pull request number
    try:
        pr_number=int(pr_number_str)
    except ValueError:
        print(f'A valid pull request number input must be defined when triggering on ' \
            f'"pull_request_target". The pull request number passed was "{pr_number_str}".')
        raise
else:
    # Try to extract the pull request number from the GitHub reference.
    try:
        pr_number=int(re.search('refs/pull/([0-9]+)/merge', github_ref).group(1))
    except AttributeError:
        print(f'The pull request number could not be extracted from the GITHUB_REF = ' \
            f'"{github_ref}"')
        raise

print(f'Pull request number: {pr_number}')

# Create a pull request object
pr = repo.get_pull(pr_number)

# Check if the PR comes from a fork. If so, the trigger must be 'pull_request_target'.
# Otherwise raise an exception here.
if pr.head.repo.full_name != pr.base.repo.full_name:
    if github_event_name != 'pull_request_target':
        raise Exception('PRs from forks are only supported when trigger on "pull_request_target"')

# Get the pull request labels
pr_labels = pr.get_labels()

# Get the list of reviews
pr_reviews = pr.get_reviews()

# List of required labels
mLabels = []
tLabels = []

# Check which of the label in the pull request, are in the
# list of valid labels
regex = sys.argv[4]

for label in pr_labels:
    validLabel= re.search(regex[0], label.name)

    if validLabel is None:
        if len(regex) == 2:
            validLabel = re.search(regex[1], label.name)
            if validLabel is not None:
                tLabels.append(validLabel.string)
    else:
        mLabels.append(validLabel.string)

# Look for the last review done by this module. The variable
# 'was_approved' will be set to True/False if the last review
# done was approved/requested changes; if there was not a
# previous review the variable will be set to 'None'.
was_approved = None
for review in pr_reviews.reversed:
    # Reviews done by this modules uses a login name
    # 'github-actions[bot]'
    if review.user.login == 'github-actions[bot]':
        if review.state == 'APPROVED':
            # The last review was approved
            was_approved = True
        elif review.state == 'CHANGES_REQUESTED':
            # The last review requested changes
            was_approved = False

        # Break this loop after the last review is found.
        # If no review was done, 'was_approved' will remain
        # as 'None'.
        break

# Check if there were at least one valid label
# Note: In both cases we exit without an error code and let the check to succeed. This is because GitHub
# workflow will create different checks for different trigger conditions. So, adding a missing label won't
# clear the initial failed check during the PR creation, for example.
# Instead, we will create a pull request review, marked with 'REQUEST_CHANGES' when no valid label was found.
# This will prevent merging the pull request until a valid label is added, which will trigger this check again
# and will create a new pull request review, but in this case marked as 'APPROVE'
# Note 2: We check for the status of the previous review done by this module. If a previous review exists, and
# it state and the current state are the same, a new request won't be generated.

if mLabels and tLabels:
    # If there were valid labels, create a pull request review, approving it
    print(f'Success! This pull request contains the following valid labels: {mLabels}, {tLabels}')

    # If the last review done was approved, then don't approved it again
    if was_approved:
        print('The last review was already approved')
    else:
        pr.create_review(event = 'APPROVE')
else:

    if not mLabels:
        print(f'Error! This pull request does not contain any module label')

    else:
        print(f'Error! This pull request does not contain any task label')

    # If the last review done requested changes, then don't request changes again.
    # 'was_approved' can be 'None', so here we need to explicitly compare against 'False'.
    if was_approved == False:
        print('The last review already requested changes')
    else:
        pr.create_review(body = 'This pull request does not contain a valid label. '
                                f'Please add one of the following labels: `{valid_labels}`',
                         event = 'REQUEST_CHANGES')
