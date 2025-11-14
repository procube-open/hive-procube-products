#!/bin/bash

workspace_folder=$1

# Install the collection
/opt/hive/bin/ansible-galaxy collection install -r $(/opt/hive/bin/pip show hive-builder | grep Location: | awk '{print $2}')/hive_builder/requirements.yml -p $workspace_folder/.collections
/opt/hive/bin/pip install -r $workspace_folder/.collections/ansible_collections/azure/azcollection/requirements.txt
