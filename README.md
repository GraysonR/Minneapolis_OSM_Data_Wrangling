# Minneapolis Open Street Map Data Wrangling

### About
My goal was to clean some data from the <a href="http://openstreetmap.org">Open Street Map project</a>. I choose to clean this data set 
because I live near Minneapolis and enjoy visiting the city. This repo contains a running report of the work I've done and some basic information about the cleaned data set.

Python files:
  1. audit.py - audits the .osm file
  2. process.py - cleans the .osm file turning it into a .json file and loads it into a MongoDB collection at the
  3. query.py - runs queries against the MongoDB collection that has the cleaned data

### Getting the data
You can download an osm xml file with Minneapolis St. Paul data from <a href="https://mapzen.com/data/metro-extracts/">here</a>. A sample file has been provided (sample.osm) that contains 1/10th the data of the original.
