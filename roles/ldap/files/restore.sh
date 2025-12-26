#!/bin/bash
systemctl stop slapd.service

echo restore ldap data
find /var/lib/ldap -mindepth 1 -delete
cp /usr/share/openldap-servers/DB_CONFIG.example /var/lib/ldap/DB_CONFIG
slapadd -l /root/ldap.ldif
chown ldap:ldap -R /var/lib/ldap

systemctl start slapd.service
