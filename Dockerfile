# syntax=docker/dockerfile:1

FROM ubuntu:20.04

WORKDIR /FuzzPlanner

# RUN apt-get update
# RUN apt install sudo
RUN export USER=root
