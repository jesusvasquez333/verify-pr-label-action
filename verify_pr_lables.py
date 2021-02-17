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

# Get the list of invalid labels
invalid_labels=sys.argv[3]
print(f'Invalid labels are: {invalid_labels}')

# Get the PR number
pr_number_str=sys.argv[4]

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

# This is a list of valid labels found in the pull request
pr_valid_labels = []

# This is a list of invalid labels found in the pull request
pr_invalid_labels = []

# Check which of the label in the pull request, are in the
# list of valid labels
for label in pr_labels:
    if label.name in valid_labels:
        pr_valid_labels.append(label.name)
    if label.name in invalid_labels:
        pr_invalid_labels.append(label.name)

# Look for the last reviews done by this module. We look backward
# in the review history for all the reviews done by this module, until
# we find the last approved review. In the process, we check is there has
# been reviews with request for changes due to missing valid label as well as
# due to containing invalid labels; if found, we set to 'True' the flags
# 'review_missing_label' and 'review_invalid_label' accordingly.
# If the latest review done by this module was approved, then we set the flag
# 'review_approved' to 'True'. The temporal flag 'latest_review' is used to
# determine which is the latest review done by this module.
last_review_approved = False
review_invalid_label = False
review_missing_label = False
latest_review = True
for review in pr_reviews.reversed:
    # Reviews done by this modules uses a login name
    # 'github-actions[bot]'
    if review.user.login == 'github-actions[bot]':
        if review.state == 'APPROVED':
            # This review was approved

            # Check is this is the latest review done by this module
            if latest_review:
                # Indicate that the last review was an approved review.
                last_review_approved = True

            # Break the loop after the last approved review is found.
            break

        elif review.state == 'CHANGES_REQUESTED':
            # This review requested changes. Determine the reason based on the
            # body of the review.
            if 'This pull request contains invalid labels.' in review.body:
                # The changes were requested due to invalid labels
                review_invalid_label = True
            else:
                # The changes were requested due to missing a valid label
                review_missing_label = True

        # Indicate that the next review is not the latest review done
        # by this module
        latest_review = False

# Check if there were not invalid labels and at least one valid label.
# Note: In any case we exit without an error code and let the check to succeed. This is because GitHub
# workflow will create different checks for different trigger conditions. So, adding a missing label won't
# clear the initial failed check during the PR creation, for example.
# Instead, we will create a pull request review, marked with 'REQUEST_CHANGES' when no valid label was found.
# This will prevent merging the pull request until a valid label is added, which will trigger this check again
# and will create a new pull request review, but in this case marked as 'APPROVE'
# Note 2: We check for the status of the previous review done by this module. If a previous review exists, and
# it state and the current state are the same, a new request won't be generated.
# Note 3: We want to generate independent reviews for both cases: an invalid label is present and a valid label is missing.

# First, we check if there are invalid labels, and generate a review if needed.
if pr_invalid_labels:
    # If there were invalid labels, then create a pull request review, requesting changes
    print(f'Error! This pull request contains the following invalid labels: {pr_invalid_labels}')

    # If there has been already a request for changes due to the presence of
    # invalid labels, then we don't request changes again.
    if review_invalid_label:
        print('The last review already requested changes')
    else:
        pr.create_review(body = 'This pull request contains invalid labels. '
                                f'Please remove the following labels: `{pr_invalid_labels}`',
                         event = 'REQUEST_CHANGES')
else:
    print('This pull request does not contain invalid labels')

# Then, we check it there are valid labels, and generate a review if needed.
# This is done independently of the presence of invalid labels above.
if not pr_valid_labels:
    # If there were not valid labels, then create a pull request review, requesting changes
    print(f'Error! This pull request does not contain any of the valid labels: {valid_labels}')

    # If there has been already a request for changes due to missing a valid
    # label, then don't request changes again.
    if review_missing_label:
        print('The last review already requested changes')
    else:
        pr.create_review(body = 'This pull request does not contain a valid label. '
                                f'Please add one of the following labels: `{valid_labels}`',
                         event = 'REQUEST_CHANGES')
else:
    print(f'This pull request contains the following valid labels: {pr_valid_labels}')

# Finally, we check if all labels are OK, and generate a review if needed.
# This condition is complimentary to the other two conditions above.
if not pr_invalid_labels and pr_valid_labels:
    # If there were valid labels, create a pull request review, approving it
    # If the latest review done was approved, then don't approved it again.
    if last_review_approved:
        print('The last review was already approved')
    else:
        pr.create_review(event = 'APPROVE')
