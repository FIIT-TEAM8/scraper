#!/bin/sh
set -m
scrapyd & 
scrapyd-deploy
fg
