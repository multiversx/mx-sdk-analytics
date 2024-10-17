# mx-sdk-analytics
Tool for data gathering and analysis on SDKs usage.

## ENVIRONMENT VARIABLES
- LIBRARIES_IO_API_KEY (Api key for the libraries.io account)
- JSON_FOLDER (Folder where generated json files are stored after gathering data from Repository sites - "./Output" for development mode)
- REPORT_FOLDER (Folder where saved .pdf files are stored)
- MX_GITHUB_TOKEN (Github fine-grained personal access token that gives access to traffic and community api pages)
- ELASTIC_SEARCH_USER, ELASTIC_SEARCH_PASSWORD credentials for accessing the logs index

## INSTALL
Create a virtual environment and install the dependencies:
```
python3 -m venv ./venv
source ./venv/bin/activate
pip install -r ./requirements.txt --upgrade
export PYTHONPATH=.
```

## INSTALL DEVELOPMENT DEPENDENCIES

```
pip install -r ./requirements-dev.txt --upgrade
```


## CONFIGURATION
### CONSTANTS.PY
- GITHUB_OWN_ORGANIZATION - the organization to which the Github token belongs to, which allows for traffic data to be obtained
- BLUE_REPORT_PORT, GREEN_REPORT_PORT, YELLOW_REPORT_PORT - Ports used for the Green, Blue, and Yellow Reports
- adjust time needed to load different components when exporting the report as pdf (Ex: WAIT_FOR_TABS_COMPONENT_LOAD = 2000)
- LOG_URL, INDEX_NAME = url and name of the index that logs data related to network access    

### ECOSYSTEM_CONFIGURATION.PY
- Enables adding or removing organizations to/from the reports as well as filtering repositories

### ECOSYSTEM.PY
- Enables fine-tunig for filtering the repositories

## RUN
### GATHER-DATA - script to be run on a weekly basis that fetches data from elastic search and repository sites and saves it in a json format in the JSON_FOLDER
- fetch data for 1 month for package managers and two weeks for Github, until 1 day before current date
   ```
    python ./multiversx_usage_analytics_tool/gather_repository_data.py
   ```
- fetches data for 1 month for package managers and two weeks for Github, until Sunday of week {week_number}
   ```
    python ./multiversx_usage_analytics_tool/gather_data.py --week={week_number}
   ```
- fetches data for 1 month for package managers and two weeks for Github, until {date_string}
   ```
    python ./multiversx_usage_analytics_tool/gather_data.py --date={date_string}
   ```
- shows argument options
   ```
    python ./multiversx_usage_analytics_tool/gather_data --help
   ```

### BLUE-REPORT - script that renders the visual report for package usage. Report available at port 8050
```
   python ./multiversx_usage_analytics_tool/blue_report.py
```

 - renders the blue report from the most recent json file generated through gathering.
 - the file rendered can be changed from a drop-down menu inside the report
 - different organizations can be accessed through a menu in the upper part of the report page
 - different repository sites can be accesed through tabs in the report

### GREEN-REPORT - script that renders the visual report for GITHUB repository usage. Report available at port 8051
```
   python ./multiversx_usage_analytics_tool/green_report.py
```

 - renders the green report from the most recent json file generated through gathering.
 - the file rendered can be changed from a drop-down menu inside the report
 - different organizations can be accesssed through tabs in the report
 - language based filtering is possible through a menu in the upper part of the report page

### YELLOW-REPORT - script that renders the visual report for Client access usage. Report available at port 8052
```
   python ./multiversx_usage_analytics_tool/yellow_report.py
```

 - renders the yellow report from the most recent json file generated through gathering.
 - the file rendered can be changed from a drop-down menu inside the report

### BLUE-REPORT-TO-PDF - script that exports the Blue Report in PDF format
```
   python ./multiversx_usage_analytics_tool/blue_report_to_pdf.py
```

 - exports the blue report in PDF format.
 - the Blue Report must be available at BLUE_REPORT_PORT.
 - the target report is selected from a list of available json files in the JSON_FOLDER

 ### GREEN-REPORT-TO-PDF - script that exports the Green Report in PDF format
```
   python ./multiversx_usage_analytics_tool/green_report_to_pdf.py
```

 - exports the green report in PDF format.
 - the Green Report must be available at GREEN_REPORT_PORT.
 - the target report is selected from a list of available json files in the JSON_FOLDER

 ### YELLOW-REPORT-TO-PDF - script that exports the Yellow Report in PDF format
```
   python ./multiversx_usage_analytics_tool/yellow_report_to_pdf.py
```

 - exports the yellow report in PDF format.
 - the Yellow Report must be available at YELLOW_REPORT_PORT.
 - the target report is selected from a list of available json files in the JSON_FOLDER

## SOURCES
- Github
- npmjs.org
- crates.io
- pypi.org
- pypistats.org
- snyk.io
- libraries.io
