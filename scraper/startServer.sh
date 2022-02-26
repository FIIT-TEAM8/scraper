#!/bin/sh

scrapyd &> output.log &
scrapyd-deploy
