#!/bin/bash
scripts_dir=$(dirname $0)

sudo apt-get -y install squid
sudo cp $scripts_dir/../files/squid.conf /etc/squid/squid.conf
sudo systemctl restart squid
