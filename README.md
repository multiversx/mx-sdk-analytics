# mx-sdk-analytics
Tool for data gathering and analysis (on SDKs usage).

## ENVIRONMENT VARIABLES
- LIBRARIES_IO_API_KEY (Api key for the libraries.io account)
- JSON_FOLDER (Folder where generated json files are stored after gathering data from Repository sites - "./Output" for development mode)
- MX_GITHUB_TOKEN (Github fine-grained personal access token that gives access to traffic and community api pages)

## INSTALL
Create a virtual environment and install the dependencies:
```
python3 -m venv ./venv
source ./venv/bin/activate
pip install -r ./requirements.txt --upgrade
```
## INSTALL DEVELOPMENT DEPENDENCIES

```
pip install -r ./requirements-dev.txt --upgrade
```


## RUN
### GATHER-DATA - script to be run on a weekly basis that fetches data from repository sites and saves it in a json format in the JSON_FOLDER
- fetch data for 1 month for package managers and two weeks for Github, until 1 day before current date
   ```
    python gather_repository_data.py
   ```
- fetches data for 1 month for package managers and two weeks for Github, until Sunday of week {week_number}
   ```
    python gather_data.py --week={week_number}
   ```
- fetches data for 1 month for package managers and two weeks for Github, until {date_string}
   ```
    python gather_data.py --date={date_string}
   ```
- shows argument options
   ```
    python gather_data --help
   ```

### BLUE-REPORT - script that renders the visual report for package usage. Report available at port 8050
```
   python blue_report.py
```

 - renders the blue report from the most recent json file generated through gathering.
 - the file rendered can be changed from a drop-down menu inside the report
 - different repository sites can be accesed through tabs in the report

### GREEN-REPORT - script that renders the visual report for GITHUB repository usage. Report available at port 8051
```
   python green_report.py
```

 - renders the green report from the most recent json file generated through gathering.
 - the file rendered can be changed from a drop-down menu inside the report
 - language based filtering is possible through a menu in the upper part of the report page
