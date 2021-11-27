#!/bin/bash
set -m
scrapyd & 
scrapyd-deploy
fg
