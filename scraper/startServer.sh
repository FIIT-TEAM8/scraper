#!/bin/sh

scrapyd &> output.log &
scrapyd-deploy
tail -f output.log
