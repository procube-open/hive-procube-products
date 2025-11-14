#!/bin/bash

# Install libvirt
sudo apt-get update
sudo apt-get install -y qemu-kvm libvirt-daemon-system libvirt-daemon virtinst bridge-utils libosinfo-bin libvirt-dev lsb-release polkit* policykit*

# Install vagrant
wget -O - https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt-get update && sudo apt-get install -y vagrant
vagrant plugin install vagrant-libvirt
vagrant plugin install vagrant-proxyconf

# Setup libvirt
sudo usermod -aG libvirt $USER
sudo systemctl restart libvirtd dbus polkit
