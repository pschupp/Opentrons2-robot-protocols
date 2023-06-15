#!/bin/bash
sudo service networking restart
sudo ifconfig enx00e04c366590 169.254.1.1 broadcast 169.254.255.255 netmask 255.255.0.0
sudo ifconfig enx00e04c366590 up

sudo ifconfig enx00e04f399206 169.254.1.1 broadcast 169.254.255.255 netmask 255.255.0.0
sudo ifconfig enx00e04f399206 up
