# JMD Forza Vehicle Database
 A vehicle database HTML generator for Forza written in Python

## Overview

This repository contains a Python script designed to parse, organize, and display vehicle data for the Forza series of games. It efficiently processes large directories of vehicle assets, extracting key details like manufacturer, model, year, variant, and race number. The script also generates detailed HTML tables with sorting, searching, and filtering functionalities, making it an invaluable tool for Forza modders, developers, and enthusiasts.

## Features

- **Folder Parsing**: Analyzes car subfolder names to extract vehicle details.
- **Image Mapping**: Links manufacturers and variants to specific images for visual representation.
- **File Size Calculation**: Computes and caches the sizes of individual car folders for efficient data handling.
- **HTML Table Generation**: Creates an interactive table displaying all vehicles, with search, sort, and filter capabilities.
- **Multithreading & Caching**: Utilizes concurrent processing and caching for improved performance.
- **Detailed Modals**: Generates modals for each vehicle, showing file details and sizes.
- **Autocomplete Search**: Incorporates an autocomplete feature for easy searching of manufacturers and models.
- **Custom Filters**: Allows filtering based on unique/duplicate status and game appearance.

## Installation

1. Clone the repository:

2. Navigate to the cloned directory.

3. Ensure Python 3.x is installed on your system.

4. Install required Python packages:


## Usage

1. Run the script in your Python environment:

```
python forza_vehicle_db.py
```

2. The script will process all subfolders in the specified directories, generating an HTML file with a comprehensive table of all vehicles.

3. Open the generated HTML file in a web browser to view and interact with the data.

4. Utilize the search bar, filters, and column sorting features for in-depth analysis of the vehicle data.

## Customization

- Modify `mappings.py` to adjust the mappings for manufacturers, models, and variants.
- Edit the script to change the folder paths or add additional functionality.
- Customize the generated HTML and CSS for a different look or additional features.

## Contributions

Contributions are welcome. Please fork the repository and submit a pull request with your changes or enhancements.
see the LICENSE file for details.

## Acknowledgments

- Forza developers (Turn10 and Playground Games) and the community for their invaluable insights and data.
- Forza Wiki for various graphics
- Contributors who have provided feedback and improvements.
- Uses Bootstrap v4 for page styling
- DataTables JS
- Bootstrap 4 Autocomplete
- jQuery
