# mx-sdk-analytics
Tool for data gathering and analysis (on SDKs usage).

## ENVIRONMENT VARIABLES
- LIBRARIES_IO_API_KEY (Api key for the libraries.io account)
- JSON_FOLDER (Folder where generated json files are stored after gathering data from Repository sites - "./Output" for development mode) 

## INSTALL
Create a virtual environment and install the dependencies:
`
python3 -m venv ./venv
source ./venv/bin/activate
pip install -r ./requirements.txt --upgrade
`

## INSTALL DEVELOPMENT DEPENDENCIES

`pip install -r ./requirements-dev.txt --upgrade`


## RUN
### GATHER-REPOSITORY-DATA - script to be run on a weekly basis that fetches data from repository sites and saves it in a json format in the JSON_FOLDER
 - `python gather_repository_data`                            -   fetches data for 1 month, until 1 day before current date
 - `python gather_repository_data --week={week_number}`       -   fetches data for 1 month, until Sunday of week {week_number}
 - `python gather_repository_data --date={date_string}`       -   fetches data for 1 month, until {date_string}
 - `python gather_repository_data --help`                     -   shows argument options

### BLUE-REPORT - script that renders the visual report for package usage. Report available at port 8050
 - renders the blue report from the most recent json file generated through gathering. 
 - the file rendered can be changed from a drop-down menu inside the report
 - different reporitory sites can be accesed through tabs in the report
`python blue_report`
