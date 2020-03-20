FROM python:3.6.10-alpine3.10

RUN pip3 install pygithub==1.47

COPY verify_pr_lables.py /verify_pr_lables.py

ENTRYPOINT ["/verify_pr_lables.py"]
