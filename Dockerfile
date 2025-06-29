# syntax=docker/dockerfile:1

FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y \
      sudo \
      ca-certificates \
      curl \
      gnupg \
      lsb-release \
 && mkdir -p /etc/apt/keyrings \
 && curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
      | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
 && echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
      https://download.docker.com/linux/ubuntu \
      focal stable" \
      > /etc/apt/sources.list.d/docker.list \
 && apt-get update \
 && apt-get install -y docker-ce-cli \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /FuzzPlanner

ENV USER=root
