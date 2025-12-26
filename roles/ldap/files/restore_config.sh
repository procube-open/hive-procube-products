#!/bin/bash
systemctl stop slapd.service

echo restore ldap config
find /etc/openldap/slapd.d -mindepth 1 -delete
slapadd -n0 -F /etc/openldap/slapd.d -l /root/ldap_config.ldif
chown ldap:ldap -R /etc/openldap/slapd.d

systemctl start slapd.service
