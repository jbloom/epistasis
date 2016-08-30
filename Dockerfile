FROM andrewosh/binder-base

MAINTAINER Zach Sailer <zsailer@uoregon.edu>

USER root

# Add dependency
RUN apt-get update

USER main

# Install requirements for Python 2 and 3
RUN pip install -e .
RUN /home/main/anaconda/envs/python3/bin/pip install -e .