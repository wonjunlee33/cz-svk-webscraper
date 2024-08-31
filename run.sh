#!/bin/bash

# if a virtual env already exists, erase and create a new one
if [ -d ".venv" ]; then
    printf "Existing virtual environment found, deleting..."
    rm -rf .venv
    printf "done\n"
fi
printf "Creating new virtual environment..."
python3 -m venv .venv
source .venv/Scripts/activate
printf "done\n"

# install required packages
printf "Installing required packages..."
pip3 install -r requirements.txt > /dev/null 2>&1
printf "done\n"

printf "Running scrapers. This will run all concurrently, please wait.\n"
# create a directory for the spreadsheets if it doesn't exist
if [ -d "./res" ]; then
    printf "Existing res directory found, deleting..."
    rm -rf res
    printf "done\n"
fi
printf "Creating res directory..."
mkdir res
printf "done\n"
cd src

printf "========================================\n"

printf "Starting generation...\n"
# run all the files concurrently
python3 scraper-datart-cz.py &
python3 scraper-alza-cz.py &
# python3 scraper-electroworld-cz.py &
python3 scraper-datart-sk.py &
python3 scraper-alza-sk.py &
# python3 scraper-nay-sk.py &
# wait for all to finish
wait

printf "========================================\n"
printf "Generation complete.\n"

cd ..
printf "Done. Check 'res' file for the spreadsheets.\n"
printf "Deactivating virtual environment..."
deactivate
printf "done\n"
printf "Remember to move the spreadsheets out before running the script again if you want to save them.\n"
printf "Spreadsheets will be overwritten if you run the script again.\n"
printf "Press any key to exit..."
read -n 1 -s

