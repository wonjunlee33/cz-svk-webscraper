#!/bin/bash
printf "It is strongly suggested that you create a virtual environment before running this script.\n"
# install required packages
pip3 install -r requirements.txt

# run all the files concurrently
python3 scraper-datart.py &
python3 scraper-alza.py &
python3 scraper-electroworld.py &
