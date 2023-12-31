# JMD Forza Vehicle Database
A vehicle database HTML generator for Forza written in Python

## Overview

This repository contains a Python script designed to parse, organize, and display vehicle data for the Forza series of games. It was created to address the challenges in managing and navigating the extensive vehicle assets within the Forza games. This tool efficiently processes large directories of vehicle assets, extracting key details like manufacturer, model, year, variant, and race number. The script generates detailed HTML tables with sorting, searching, and filtering functionalities, making it an invaluable asset for modders, developers, and enthusiasts looking to streamline their workflow and enhance their experience.

## Features

- **Folder Parsing**: Analyzes car subfolder names based on specific naming conventions to extract key vehicle details.
- **Image Mapping**: Automatically links manufacturers and variants to corresponding images for a visual representation, using file naming conventions or configuration files for mapping.
- **File Size Calculation**: Efficiently computes and caches the sizes of individual car folders, significantly reducing load times and improving data handling.
- **HTML Table Generation**: Creates an interactive table displaying all vehicles, complete with search, sort, and filter capabilities for an in-depth analysis of the vehicle data.
- **Multithreading & Caching**: Utilizes concurrent processing with multiple threads and caching of processed data for enhanced performance and speed.
- **Detailed Modals**: Generates clickable modals for each vehicle, showing extensive file details such as file type, size, and resolution for images.
- **Autocomplete Search**: Features an autocomplete search bar, dynamically populated with manufacturers and models from the vehicle data.
- **Custom Filters**: Offers custom filters to sort data based on unique/duplicate status and game appearance.

## Installation

1. Clone the repository:

2. Navigate to the cloned directory.

3. Ensure Python 3.x is installed on your system.

4. Install required Python packages:
- `shelve`
- `json`

## Usage

1. Run the script in your Python environment:

`python forza_vehicle_db.py`

2. The script processes all subfolders in the specified directories, generating an HTML file with a comprehensive table of all vehicles.
3. Open the generated HTML file in a web browser to access the interactive data table.
4. Utilize the search bar, filters, and column sorting features for in-depth data exploration.

## Customization

- Modify `mappings.py` to adjust the mappings for manufacturers, models, and variants.
- Edit the script to change folder paths or add additional functionality.
- Customize the generated HTML and CSS for a different look or additional features. For example, to change the table's color scheme, update the `.table` class in the CSS.

## Folders

The script utilizes several folders, each serving a specific purpose:

- `"_images"`: Stores images used in the HTML output.
- `"_images\brands"`: Contains brand-specific images, mainly logo graphics for different car manufacturers.
- `"_images\brands\Square"`: A subfolder within the brands directory for square-shaped images.
- `"_images\editions"`: Dedicated to images representing different editions or variants of vehicles.
- `"car_details"`: Stores detailed information about each car, including HTML files or data files generated by the script.

## Contributions

Contributions are welcome. Please fork the repository and submit a pull request with your changes or enhancements.

## Support and Troubleshooting

For support or if you encounter any issues, feel free to open an issue on GitHub.

## Acknowledgments

- Forza developers (Turn10 and Playground Games) and the community for their invaluable insights and data.
- Forza Wiki for various graphics.
- Contributors who have provided feedback and improvements.
- Uses Bootstrap v4 for page styling, DataTables JS, Bootstrap 4 Autocomplete, and jQuery.

## Future Plans

We are continuously working to enhance this tool. Upcoming features include advanced data analytics capabilities and support for additional Forza titles.
