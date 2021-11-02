#!/usr/bin/env python3

import os
import sys
import re
import distutils.util
from github import Github


def get_env_var(env_var_name, echo_value=False):
    """Try to get the value from a environmental variable.

    If the values is 'None', then a ValueError exception will
    be thrown.

    Args
    ----
    env_var_name : str
        The name of the environmental variable.
    echo_value : bool, optional, default False
        Print the resulting value.

    Returns
    -------
    value : str
        The value from the environmental variable.

    """
    value = os.environ.get(env_var_name)

    if value is None:
        print(f'ERROR: The environmental variable {env_var_name} is empty!',
              file=sys.stderr)
        sys.exit(1)

    if echo_value:
        print(f"{env_var_name} = {value}")

    return value


# Check if the number of input arguments is correct
if len(sys.argv) != 6:
    print('ERROR: Invalid number of arguments!', file=sys.stderr)
    sys.exit(1)

# Get the GitHub token
token = sys.argv[1]
if not token:
    print('ERROR: A token must be provided!', file=sys.stderr)
    sys.exit(1)

# Get the list of valid labels
valid_labels = [label.strip() for label in sys.argv[2].split(',')]
print(f'Valid labels are: {valid_labels}')

# Get the list of invalid labels
invalid_labels = [label.strip() for label in sys.argv[3].split(',')]
print(f'Invalid labels are: {invalid_labels}')

# Get the PR number
pr_number_str = sys.argv[4]

# Are reviews disabled?
try:
    pr_reviews_disabled = bool(distutils.util.strtobool(sys.argv[5]))
except ValueError:
    pr_reviews_disabled = False
print(f"PR reviews are: {'disabled' if pr_reviews_disabled else 'enabled'}")

# Get needed values from the environmental variables
repo_name = get_env_var('GITHUB_REPOSITORY')
github_ref = get_env_var('GITHUB_REF')
github_event_name = get_env_var('GITHUB_EVENT_NAME')

# Create a repository object, using the GitHub token
repo = Github(token).get_repo(repo_name)

# When this actions runs on a "pull_reques_target" event, the pull request
# number is not available in the environmental variables; in that case it must
# be defined as an input value. Otherwise, we will extract it from the
# 'GITHUB_REF' variable.
if github_event_name == 'pull_request_target':
    # Verify the passed pull request number
    try:
        pr_number = int(pr_number_str)
    except ValueError:
        print('ERROR: A valid pull request number input must be defined when '
              'triggering on "pull_request_target". The pull request number '
              'passed was "{pr_number_str}".',
              file=sys.stderr)
        sys.exit(1)
else:
    # Try to extract the pull request number from the GitHub reference.
    try:
        pr_number = int(re.search('refs/pull/([0-9]+)/merge',
                        github_ref).group(1))
    except AttributeError:
        print('ERROR: The pull request number could not be extracted from '
              f'GITHUB_REF = "{github_ref}"', file=sys.stderr)
        sys.exit(1)

print(f'Pull request number: {pr_number}')

# Create a pull request object
pr = repo.get_pull(pr_number)

# Check if the PR comes from a fork. If so, the trigger must be
# 'pull_request_target'. Otherwise exit on error here.
if pr.head.repo.full_name != pr.base.repo.full_name:
    if github_event_name != 'pull_request_target':
        print('ERROR: PRs from forks are only supported when trigger on '
              '"pull_request_target"', file=sys.stderr)
        sys.exit(1)

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

# If reviews are enabled, look for the last reviews done by this module.
# We look backward in the review history for all the reviews done by this
# module, until we find the last approved review. In the process, we check is
# there has been reviews with request for changes due to missing valid label
# as well as due to containing invalid labels; if found, we set to 'True' the
# flags 'review_missing_label' and 'review_invalid_label' accordingly.
# If the latest review done by this module was approved, then we set the flag
# 'review_approved' to 'True'. The temporal flag 'latest_review' is used to
# determine which is the latest review done by this module.
if not pr_reviews_disabled:
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
#
# Note: When reviews are enabled, we always exit without an error code and let
# the check to succeed. Instead, we will create a pull request review, marked
# with 'REQUEST_CHANGES' when no valid label or invalid labels are found.
# This will prevent merging the pull request. When a valid label and not
# invalid labels are found, we will create a new pull request review, but in
# this case marked as 'APPROVE'. This will allow merging the pull request.
#
# Note 2: When reviews are enabled, we check for the status of the previous
# review done by this module. If a previous review exists, and it state and
# the current state are the same, a new request won't be generated.
#
# Note 3: We want to generate independent reviews for both cases: an invalid
# label is present and a valid label is missing.
#
# Note 4: If reviews are disabled, we do not generate reviews. Instead, we exit
# with an error code when no valid label or invalid labels are found, making
# the check fail. This will prevent merging the pull request. When a valid
# label and not invalid labels are found, we exit without an error code,
# making the check pass. This will allow merging the pull request.

# First, we check if there are invalid labels, and generate a review if needed,
# or exit with an error code.
if pr_invalid_labels:
    print('Error! This pull request contains the following invalid labels: '
          f'{pr_invalid_labels}', file=sys.stderr)

    # If reviews are disable, exit with an error code.
    if pr_reviews_disabled:
        print('Exiting with an error code')
        sys.exit(1)

    # If there has been already a request for changes due to the presence of
    # invalid labels, then we don't request changes again.
    if review_invalid_label:
        print('The last review already requested changes')
    else:
        pr.create_review(
            body='This pull request contains invalid labels. Please remove '
                 f'all of the following labels: `{invalid_labels}`',
            event='REQUEST_CHANGES')
else:
    print('This pull request does not contain invalid labels')

# Then, we check it there are valid labels, and generate a review if needed,
# or exit with an error code. This is done independently of the presence of
# invalid labels above.
if not pr_valid_labels:
    print('Error! This pull request does not contain any of the valid labels: '
          f'{valid_labels}', file=sys.stderr)

    # If reviews are disable, exit with an error code.
    if pr_reviews_disabled:
        print('Exiting with an error code')
        sys.exit(1)

    # If there has been already a request for changes due to missing a valid
    # label, then don't request changes again.
    if review_missing_label:
        print('The last review already requested changes')
    else:
        formatted_labels = "\n".join(map(lambda label: f"• {label}", valid_labels))
        pr.create_review(
            body='This pull request does not contain a valid label.\n\nPlease '
                 f'add one of the following labels:\n`{formatted_labels}`',
            event='REQUEST_CHANGES')
else:
    print('This pull request contains the following valid labels: '
          f'{pr_valid_labels}')

# Finally, we check if all labels are OK, and generate a review if needed,
# or exit without an error code. This condition is complimentary to the other
# two conditions above.
if not pr_invalid_labels and pr_valid_labels:
    print('All labels are OK in this pull request')

    # If reviews are disable, exit without an error code.
    if pr_reviews_disabled:
        print('Exiting without an error code')
        sys.exit(0)

    # If the latest review done was approved, then don't approved it again.
    if last_review_approved:
        print('The last review was already approved')
    else:
        pr.create_review(event='APPROVE')
