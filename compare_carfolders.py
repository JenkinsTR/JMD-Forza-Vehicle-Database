import os
import re
import shelve
import json
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from mappings import parent_folders, folder_to_image, game_folder_codes, manufacturer_logos, manufacturer_codes, variant_mappings, car_overrides, variant_logos

# Excluded subfolders
excluded_subfolders = ["_library", "appearancepresets", "driver", "shadersettings", "shared", "tex"]

# Function to strip '_slod' or 'slod' from the folder name
def strip_slod_suffix(folder_name):
    return re.sub(r'(_?slod)$', '', folder_name, flags=re.IGNORECASE)

# Function to calculate the size of a single folder
def get_folder_size(folder_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size

# Function to concurrently calculate folder sizes and update the cache
def calculate_folder_sizes_with_cache(folder_paths, cache_file='folder_sizes_cache.db'):
    folder_sizes = {}
    with ThreadPoolExecutor() as executor, shelve.open(cache_file) as cache:
        futures = {executor.submit(get_folder_size, path): path for path in folder_paths}
        for future in as_completed(futures):
            folder_path = futures[future]
            try:
                if folder_path in cache:
                    size = cache[folder_path]
                    print(f"Using cached size for '{folder_path}': {size / (1024 * 1024):.2f} MB")
                else:
                    size = future.result()
                    cache[folder_path] = size
                    print(f"Size of '{folder_path}': {size / (1024 * 1024):.2f} MB")
                
                folder_sizes[folder_path] = size / (1024 * 1024)
            except Exception as e:
                print(f"Exception occurred for folder {folder_path}: {e}")
    return folder_sizes

# Function to Get File List for a Single Folder
def get_file_list_for_folder(folder_path):
    print(f"Generating file list for folder: {folder_path}")
    file_list = []
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            file_size = os.path.getsize(file_path)

            # Trim off the 'car subfolder path' portion to get the relative path
            relative_file_path = os.path.relpath(file_path, folder_path)
            file_list.append((relative_file_path, file_size))

    return file_list

# Function to Get File List with Cache and Multithreading
def get_file_list_with_cache(folder_paths, cache_file='file_lists_cache.db'):
    file_lists = {}
    with ThreadPoolExecutor() as executor, shelve.open(cache_file) as cache:
        futures = {}
        for folder_path in folder_paths:
            if folder_path in cache:
                print(f"Using cached file list for '{folder_path}'")
                file_lists[folder_path] = cache[folder_path]
            else:
                print(f"Cache miss, generating file list for '{folder_path}'")
                futures[executor.submit(get_file_list_for_folder, folder_path)] = folder_path

        for future in as_completed(futures):
            folder_path = futures[future]
            try:
                file_list = future.result()
                print(f"File list generated for '{folder_path}', updating cache")
                cache[folder_path] = file_list
                file_lists[folder_path] = file_list
            except Exception as e:
                print(f"Exception for folder {folder_path}: {e}")
    return file_lists

def generate_file_list_html(file_list):
    file_list_html = ""
    if not isinstance(file_list, list) or not all(isinstance(item, tuple) and len(item) == 2 for item in file_list):
        print(f"Invalid file list format for path: {file_list}")
        return "<tr class='file_row'><td class='align-middle text-center' colspan='2'>No file details available</td></tr>"

    for file_name, file_size in file_list:
        file_size_mb = file_size / (1024 * 1024)
        file_list_html += f"<tr class='file_row'><td class='align-middle text-left file'>{file_name}</td><td class='align-middle text-right file_size'>{file_size_mb:.2f} MB</td></tr>"
    return file_list_html

# Function to generate partial HTML file for car details
def generate_car_details_html(subfolder_path, original_name, file_list_html, game_folder_codes, parent_folder_path, output_dir='car_details'):
    # Retrieve the game code using the parent folder path
    game_code = game_folder_codes.get(parent_folder_path, "unknown")
    file_name = f"{original_name.replace(' ', '_').replace('.', '_')}_{game_code}.html"
    image_path = folder_to_image.get(parent_folder_path, "_images/unknown.png")
    game_name = parent_folders.get(parent_folder_path, "Unknown Game")

    partial_html_content = f"""
                <div class="modal fade" id="detailsModal" tabindex="-1" role="dialog" aria-labelledby="detailsModalTitle" aria-hidden="true">
                    <div class="modal-dialog modal-xl" role="document">
                        <div class="modal-content">
                            <div class="modal-header align-items-center">
                                <img src="{image_path}" alt="{game_name}" title="{game_name}" width="64" height="64" class="mr-3">
                                <div class="text-left">
                                    <h2 class="modal-title" id="detailsModalTitle">File Details for {original_name}</h2>
                                    <span class="font-weight-light small ml-auto">{subfolder_path}</span>
                                </div>
                                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                                    <span aria-hidden="true">&times;</span>
                                </button>
                            </div>
                            <div class="modal-body">
                                <table class="table table-sm table-bordered table-hover">
                                    <thead class="thead-dark">
                                        <tr>
                                            <th style="text-align:center;">File</th>
                                            <th style="text-align:center;">Size</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {file_list_html}
                                    </tbody>
                                </table>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                            </div>
                        </div>
                    </div>
                </div>
    """

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Write partial HTML content to file
    with open(os.path.join(output_dir, file_name), 'w') as file:
        file.write(partial_html_content)

    return file_name

def generate_and_format_all_occurrences(occurrences, folder_to_image, parent_folders, file_lists, folder_sizes):
    all_occurrences_display = ""
    for occ_index, (occ_path, occ_name) in enumerate(occurrences):
        full_subfolder_path = os.path.join(occ_path, occ_name)
        file_list = file_lists.get(full_subfolder_path, [])
        file_list_html = generate_file_list_html(file_list)

        # Generate a unique filename for each occurrence
        details_file_name = generate_car_details_html(full_subfolder_path, occ_name, file_list_html)

        # Format the occurrence for display
        occurrence_display = format_full_path_and_image(full_subfolder_path, occ_name, parent_folders.get(occ_path, "Unknown Game"), folder_sizes.get(full_subfolder_path, 0), details_file_name)
        all_occurrences_display += occurrence_display

    return all_occurrences_display

# Function to format the occurrences with the full path and image, including detailed file list modal 
def format_full_path_and_image(folder_path, original_name, game_name, folder_sizes, file_list_html, game_folder_codes):
    
    # Extract parent folder path from the full subfolder path
    parent_folder_path = os.path.dirname(folder_path)
    game_code = game_folder_codes.get(parent_folder_path, "unknown")
    
    image_path = folder_to_image.get(parent_folder_path, "_images/unknown.png")
    full_path = os.path.join(parent_folder_path, original_name)
    
    folder_size_mb = folder_sizes.get(full_path, 0)  # Now using the full path of the car subfolder

    # Use the same naming convention to determine the details file name
    details_file_name = f"{original_name.replace(' ', '_').replace('.', '_')}_{game_code}.html"

    # print("DEBUG: -------------------------------")
    # print(f"DEBUG: Folder path: {folder_path}")
    # print(f"DEBUG: Image path: {image_path}")
    # print(f"DEBUG: Full path: {full_path}")
    # print(f"DEBUG: Folder size mb: {folder_size_mb}")
    # print(f"DEBUG: Parent folder path: {parent_folder_path}")
    # print(f"DEBUG: Game code: {game_code}")
    # print(f"DEBUG: Details filename: {details_file_name}")
    # print("DEBUG: -------------------------------")
    
    return f'''
    <li class="media border-bottom align-items-center">
        <img src="{image_path}" alt="{game_name}" title="{game_name}" width="64" height="64" class="mr-3">
        <div class="media-body col-sm-8">
            <h5 class="mt-0 mb-1">{original_name}</h5>
            <span class="font-weight-light small ml-auto">{full_path}</span></br>
            <span class="ml-auto">Folder Size: {folder_size_mb:.2f} MB</span>
        </div>
        <div class="media-body col-sm-4 text-right">
            <button type="button" class="btn btn-secondary details-button" data-details-url="car_details/{details_file_name}">
                File Details
            </button>
            
            <!-- Modal -->
            <div id="dynamicModalContent">
                                    <!-- Content will be loaded here -->
            </div>
        </div>
    </li>
    '''

# Function to parse folder name into Manufacturer, Model, Year, Variant, and Race Number (if present)
def parse_folder_name(folder_name):
    # Initialize default values
    manufacturer, model, year, variant, race_number = 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown'
    manufacturer_logo = "_images/brands/Unknown_Logo.png"

    # Process folder name if no override exists
    folder_name = re.sub(r'(_?slod)$', '', folder_name, flags=re.IGNORECASE)
    parts = folder_name.split('_')
    manufacturer_code = parts[0].lower() if len(parts) >= 3 else 'unknown'

    # Check if an override exists for this folder name
    if folder_name in car_overrides:
        manufacturer, model, year, variant, race_number = car_overrides[folder_name]
        # Check if manufacturer is directly in the logos dictionary
        if manufacturer.lower() in manufacturer_logos:
            manufacturer_code = manufacturer.lower()
    else:
        if len(parts) >= 3:
            manufacturer_code = parts[0].lower()  # Convert to lowercase
            manufacturer = manufacturer_codes.get(manufacturer_code, 'Unknown')
            model = parts[1].title()
            year = parts[-1]

            # Check for a race number before the model
            race_number = ''
            model_start_index = 1
            if parts[1].isdigit():
                race_number = parts[1]
                model_start_index = 2
        
            model = parts[model_start_index].title()
        
            # Handle year, which should be the last segment
            year_part = parts[-1]
            if len(year_part) == 2:
                current_year_last_two_digits = datetime.now().year % 100
                year_prefix = '19' if int(year_part) > current_year_last_two_digits else '20'
                year = year_prefix + year_part
            else:
                year = year_part
        
            # Variant may include the segments between model and year
            variant_parts = parts[model_start_index + 1:-1]
            variant = ' '.join(variant_parts).title() if variant_parts else ''
            variant = variant_mappings.get(variant, variant)  # Map the variant code to friendly name

    # Fetch the logo using the manufacturer code or name
    manufacturer_logo = manufacturer_logos.get(manufacturer_code, "_images/brands/Unknown_Logo.png")

    # Fetch the variant logo or use plain text
    variant_logo = variant_logos.get(variant, variant)  # This will return the image path or plain text

    return manufacturer, manufacturer_logo, model, year, variant, variant_logo, race_number

# Function to determine the cell color based on the number of occurrences
# def get_cell_color(occurrences):
#     count = len(occurrences)
#     if count > 2:
#         return 'pink'
#     elif count == 1:
#         return 'green'
#     else:
#         return 'orange'

# Function to assign badge class based on occurrences
def assign_badge(occurrences):
    count = len(occurrences)
    if count > 2:
        return 'badge badge-danger', 'Duplicated in > 2 games'
    elif count > 1:
        return 'badge badge-warning', 'Duplicated'
    else:
        return 'badge badge-success', 'Unique'

# Function to format the game image HTML
def format_game_image(folder_path, original_name):
    image_path = folder_to_image.get(folder_path, "_images/unknown.png")
    game_name = parent_folders.get(folder_path, "Unknown Game")
    return f'''
<div class="d-flex align-items-center justify-content-between">
    <img src="{image_path}" alt="{game_name}" title="{game_name}" width="64" height="64" class="img-fluid">
    <span>{original_name}</span>
</div>
'''

def get_game_id(folder_path):
    # Extract game id from the image file name in the folder_to_image mapping
    image_file = folder_to_image.get(folder_path, "")
    game_id = os.path.splitext(os.path.basename(image_file))[0]  # gets 'fh1' from '_images/fh1.png'
    return game_id

# Add a function to generate game filter HTML
def generate_game_filters_html(parent_folders, folder_to_image):
    game_filters_html = ""
    for folder_path, game_name in parent_folders.items():
        game_image = folder_to_image.get(folder_path, "_images/unknown.png")
        game_id = get_game_id(folder_path)  # Use game_id for filter value
        filter_id = "filter-" + game_id  # Use game_id for ID
        game_filters_html += f'''
            <label class="game-filter">
                <input type="checkbox" id="{filter_id}" class="filter-game" value="{game_id}" checked>
                <img src="{game_image}" alt="{game_name}" title="{game_name}" width="32" height="32">
                <span class="font-weight-light small">{game_name}</span>
            </label>
        '''
    return game_filters_html

print("Building data...")

# Assuming manufacturer_codes is a dictionary mapping codes to names
name_to_code_mapping = {name.lower(): code for code, name in manufacturer_codes.items()}

# You should now collect paths of the individual subfolders instead of the parent folders
subfolders_dict = {}
unique_folder_paths = set()  # This will collect individual car subfolder paths

for folder_path, game_name in parent_folders.items():
    try:
        for subfolder in os.listdir(folder_path):
            original_name = subfolder
            subfolder_normalized = strip_slod_suffix(subfolder).lower()
            subfolder_full_path = os.path.join(folder_path, subfolder)  # Full path to the subfolder

            if subfolder_normalized in excluded_subfolders or not re.match(r'^[a-z]{2,3}_', subfolder_normalized):
                continue

            if os.path.isdir(subfolder_full_path):
                unique_folder_paths.add(subfolder_full_path)  # Add the path of each car subfolder

                parsed_values = parse_folder_name(subfolder_normalized)
                comparison_key = parsed_values

                if comparison_key not in subfolders_dict:
                    subfolders_dict[comparison_key] = [(folder_path, original_name)]
                else:
                    if (folder_path, original_name) not in subfolders_dict[comparison_key]:
                        subfolders_dict[comparison_key].append((folder_path, original_name))
    except FileNotFoundError:
        print(f"Warning: The folder {folder_path} was not found or is not accessible.")

# Retrieve folder sizes, using the cache if available
folder_sizes = calculate_folder_sizes_with_cache(unique_folder_paths)

# After calculating folder sizes
file_lists = get_file_list_with_cache(unique_folder_paths, 'file_lists_cache.db')

# Initialize total size variables
total_size_all_cars = 0
total_size_unique_cars = 0

# Initialize counters
total_cars = 0
unique_cars = 0

for comparison_key, occurrences in subfolders_dict.items():
    is_unique = len(occurrences) == 1  # Flag to check if the car is unique
    total_cars += len(occurrences)

    for folder_path, original_name in occurrences:
        subfolder_full_path = os.path.join(folder_path, original_name)
        size_mb = folder_sizes.get(subfolder_full_path, 0)  # Ensure size is in MB
        total_size_all_cars += size_mb

        if is_unique:
            unique_cars += 1
            total_size_unique_cars += size_mb

# Call the function to generate the HTML for game filters
game_filters_html = generate_game_filters_html(parent_folders, folder_to_image)

# def generate_model_mappings_csv(subfolders_dict, csv_file='model_mappings.csv'):
#     with open(csv_file, 'w', newline='', encoding='utf-8') as file:
#         writer = csv.writer(file)
#         writer.writerow(['Folder Name', 'Manufacturer', 'Model', 'Year', 'Variant', 'Race Number'])
# 
#         for comparison_key, occurrences in subfolders_dict.items():
#             for _, original_name in occurrences:
#                 # Call the parse_folder_name function
#                 manufacturer, _, model, year, variant, race_number = parse_folder_name(original_name)
#                 # Write to CSV
#                 writer.writerow([original_name, manufacturer, model, year, variant, race_number])
#     
#     print(f"Model mappings CSV file saved to '{csv_file}'")

# Call the function
# generate_model_mappings_csv(subfolders_dict)

html_output = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Forza Vehicle Database</title>
<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css">
<!-- DataTables CSS -->
<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.21/css/jquery.dataTables.css">
<style>
  .image-cell {{
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .image-cell img {{
    max-width: 64px;
    max-height: 64px;
  }}
  
.container-fluid {{
    padding-right: 0px !important;
    padding-left: 0px !important;
}}
.table-bordered {{
    border: 0px solid #dee2e6 !important;
}}
/* Sticky header styles */
th {{
  background-color: white; /* or any color that matches your design */
  position: sticky;
  top: 0;
  border-top: 0px solid #e1e1e1 !important;
  border-bottom: 0px solid #e1e1e1 !important;
  z-index: 10; /* Ensure the header is above other content */
}}

/* Ensure the table content doesn't overlap with border */
table {{
  border-spacing: 0;
  border-top: 0px solid #e1e1e1 !important;
  border-bottom: 0px solid #e1e1e1 !important;
}}

/* Optional: Add a shadow to the sticky header */
th::after {{
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: -1px;
  border-bottom: 0px solid #e1e1e1 !important;
  box-shadow: 0px 4px 15px 3px rgba(0,0,0,0.4);
  border-top: 0px solid #e1e1e1 !important;
}}
.centered-content {{
  text-align: center;
  vertical-align: middle;
}}
/* .manufacturer-logo {{ */
/*   background-color: #343a40; */
/* }} */
#manufacturer {{
    width: 1em;
}}
span.circlebehind {{
  background: #030303;
  -moz-border-radius: 50%;
  -webkit-border-radius: 50%;
  border-radius: 50%;
  color: #0e0e0e;
  display: inline-block;
  font-weight: bold;
  line-height: 44px;
  margin-right: 5px;
  text-align: center;
  width: 44px;
}}
span.circle {{
  background: #e3e3e3;
  -moz-border-radius: 50%;
  -webkit-border-radius: 50%;
  border-radius: 50%;
  color: #0e0e0e;
  display: inline-block;
  font-weight: bold;
  line-height: 40px;
  text-align: center;
  width: 40px;
}}
.row {{
    margin-right: 0px !important;
    margin-left: 0px !important;
}}
/* Custom checkbox styles */
.checkbox-filters label {{
    cursor: pointer;
    margin-right: 5px;
    border-radius: 0.25rem;
    padding: 0.25rem 0.6rem;
    -webkit-user-select: none; /* Prevent text selection on Safari */
    user-select: none; /* Prevent text selection */
}}

.checkbox-filters input[type="checkbox"]:checked + span {{
    text-decoration: none;
}}
.modal-dialog.modal-xl {{
    max-width: 80vw !important;
}}
.car-list li:last-child {{
    border-bottom: none !important;
}}
.dataTables_wrapper .dataTables_filter input {{
    width: 50vw;
}}
#carTable_length label {{
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
    align-items: center;
}}
</style>
</head>
<body>

<div class="container-fluid">
    <div class="row align-items-center justify-content-between">
        <div class="col-sm-8">
            <h1 style="text-align:left;">Forza Vehicle Database</h1>
        </div>
        <div class="col-sm-4 text-right">
            <div class="legend">
                <span class="badge badge-success">Unique</span>
                <span class="badge badge-warning">Duplicated</span>
                <span class="badge badge-danger">Duplicated in > 2 games</span>
            </div>
            <div class="totals">
                <div>Total cars: {total_cars} (Total Size: {total_size_all_cars:.2f} MB)</div>
                <div>Total unique cars: {unique_cars} (Total Size: {total_size_unique_cars:.2f} MB)</div>
            </div>
        </div>
    </div>
    <hr>
    <div class="row">
        <div class="col-6 checkbox-filters">
            <label class="btn btn-sm badge badge-success">
                <input type="checkbox" id="filter-unique" class="filter" value="Unique" checked> Unique
            </label>
            <label class="btn btn-sm badge badge-warning">
                <input type="checkbox" id="filter-duplicates" class="filter" value="Duplicates" checked> Duplicated
            </label>
            <label class="btn btn-sm badge badge-danger">
                <input type="checkbox" id="filter-multidupes" class="filter" value="MultiDupes" checked> Duplicated in > 2 games
            </label>
        </div>
        <div class="col-6 game-filters text-right">{game_filters_html}</div>
    </div>

    <table id="carTable" class="table table-sm table-bordered table-hover">
        <thead class="thead-dark">
            <tr>
                <th id="manufacturer" style="text-align:center;">Manufacturer</th>
                <th id="race_number" style="text-align:center;">Race #</th>
                <th id="model" style="text-align:center;">Model</th>
                <th id="year" style="text-align:center;">Year</th>
                <th id="variant" style="text-align:center;">Variant</th>
                <th id="internal_name" style="text-align:center;">Internal Name</th>
                <th id="first_occurrence_display" style="text-align:center;">First Occurrence</th>
                <th id="all_occurrences_display" style="text-align:center;">All Occurrences</th>
            </tr>
        </thead>
        <tbody>
"""

# Pre-generate partial HTML files for each unique folder
for i, folder_path in enumerate(unique_folder_paths, 1):
    if folder_path in file_lists:
        original_name = os.path.basename(folder_path)  # Extract the folder name
        file_list = file_lists[folder_path]
        file_list_html = generate_file_list_html(file_list)
        
        # Extract parent folder path from the full subfolder path
        parent_folder_path = os.path.dirname(folder_path)
        details_file_name = generate_car_details_html(folder_path, original_name, file_list_html, game_folder_codes, parent_folder_path)

        # Print the debug information
        # debug_game_code = game_folder_codes.get(parent_folder_path, "unknown")
        # print(f"Debug: Parent Folder Path - {parent_folder_path}, Game Code - {debug_game_code}")
        
        # Print progress for partial HTML file generation
        print(f'Generating partial HTML for car {i}/{len(unique_folder_paths)}')

# Sort and add rows to the table, ensuring sorting by the original internal_name
sorted_subfolders = sorted(subfolders_dict.items(), key=lambda x: x[1][0][1].lower())  # Sort by the original_name in lowercase
for i, (comparison_key, occurrences) in enumerate(sorted_subfolders, 1):
    ## color_class = get_cell_color(occurrences)
    
    # Assuming the first occurrence's path determines the game
    first_folder_path = occurrences[0][0]
    game_name = parent_folders.get(first_folder_path, "Unknown Game")

    # Add game classes to each row
    game_classes = [get_game_id(folder_path) for folder_path, _ in occurrences]
    game_class_str = " ".join(game_classes)

    # Correctly unpack all six values returned by the parse_folder_name function
    first_folder_path, first_original_name = occurrences[0]
    manufacturer, manufacturer_logo, model, year, variant, variant_logo, race_number = parse_folder_name(first_original_name)

    # Format first occurrence for display with image
    first_occurrence_display = format_game_image(first_folder_path, first_original_name)
    
    # Replace first_original_name with stripped version
    first_original_name = strip_slod_suffix(first_original_name)
    
    # Get the badge class and text based on occurrences
    badge_class, badge_text = assign_badge(occurrences)

    # Wrap the first_original_name with the badge span tag
    first_original_name_display = f'<span class="{badge_class}" data-filter-type="{badge_text}" title="{badge_text}">{first_original_name}</span>'

    # Format all occurrences for display with images and full paths, image left-aligned and path right-aligned
    # Generate and format all occurrences
    all_occurrences_display = ""
    for occ_path, occ_name in occurrences:
        full_subfolder_path = os.path.join(occ_path, occ_name)
        if full_subfolder_path in file_lists:
            file_list = file_lists[full_subfolder_path]
            file_list_html = generate_file_list_html(file_list)

            # Format the occurrence for display
            occurrence_display = format_full_path_and_image(
                full_subfolder_path, occ_name, parent_folders.get(occ_path, "Unknown Game"), 
                folder_sizes, file_list_html, game_folder_codes
            )
            all_occurrences_display += occurrence_display

    # This line checks if race_number is not empty or None and includes circlebehind
    race_number_html = f'<span class="circlebehind"><span class="circle">{race_number}</span></span>' if race_number else f'<span class="circle">{race_number}</span>'

    row_class = "unique-row" if badge_text == "Unique" else ("duplicate-row" if badge_text == "Duplicated" else "multi-duplicate-row")

    # Determine if variant_logo is an image path or plain text
    if variant_logo.endswith('.png'):
        variant_display = f'<img src="{variant_logo}" alt="{variant}" title="{variant}" class="img-fluid" width="150" height="50"><span class="d-none">{variant}</span>  <!-- Hidden text for search -->'
    else:
        variant_display = variant  # Plain text

    html_output += f"""
    <tr class="{row_class} {game_class_str}">
      <td class="align-middle text-center manufacturer-logo">
          <img src="{manufacturer_logo}" alt="{manufacturer}" title="{manufacturer}" class="img-fluid">
          <span class="d-none">{manufacturer}</span>  <!-- Hidden text for search -->
      </td>
      <td class="align-middle" style="text-align:center;">{race_number_html}</td>
      <td class="align-middle" style="text-align:center;">{model}</td>
      <td class="align-middle" style="text-align:center;">{year}</td>
      <td class="align-middle" style="text-align:center;">{variant_display}</td>
      <td class="align-middle" style="text-align:center;">{first_original_name_display}</td>
      <td class="align-middle" style="text-align:left;">{first_occurrence_display}</td>
      <td class="align-middle" style="text-align:left;"><ul class="list-unstyled align-items-center mb-0 car-list">{all_occurrences_display}</ul></td>
    </tr>
    """

# Close the HTML tags
html_output += """
    </tbody>
  </table>
</div>
<!-- Dependencies -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.5.1/jquery.min.js" crossorigin="anonymous"></script>

<!-- Include jQuery UI for Autocomplete -->
<link rel="stylesheet" href="https://code.jquery.com/ui/1.13.2/themes/base/jquery-ui.css">
<script src="https://code.jquery.com/ui/1.13.2/jquery-ui.min.js" crossorigin="anonymous"></script>

<script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/2.6.0/umd/popper.min.js" crossorigin="anonymous"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/4.6.0/js/bootstrap.min.js" crossorigin="anonymous"></script>

<!-- DataTables script -->
<script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/1.10.21/js/jquery.dataTables.js" crossorigin="anonymous"></script>

<!-- Bootstrap 4 Autocomplete -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap-4-autocomplete/dist/bootstrap-4-autocomplete.min.js" crossorigin="anonymous"></script>

<script>
    $(document).ready(function() {
        var table = $('#carTable').DataTable({
            "lengthMenu": [ [10, 25, 50, 100, -1], [10, 25, 50, 100, "All (NOT recommended"] ],
            "pageLength": 25,
            "columns": [
                { "orderable": true }, //manufacturer
                { "orderable": true }, //race_number
                { "orderable": true }, //model
                { "orderable": true }, //year
                { "orderable": true }, //variant
                { "orderable": true }, //first_original_name
                { "orderable": false }, //first_occurrence
                { "orderable": false } //all_occurrences
            ]
        });
        
        // Use setTimeout to wait for the DataTables elements to be ready
        setTimeout(function() {
            // Replace the search input
            var searchInput = $('#carTable_filter input[type="search"]');
            searchInput
                .removeClass() // Remove existing classes
                .addClass('form-control form-control-lg mb-2') // Add Bootstrap classes
                .attr('placeholder', 'Search for car names, manufacturers, etc'); // Add new placeholder
    
            // Remove the label tag but keep the input
            var label = $('#carTable_filter label');
            label.contents().filter(function() {
                return this.nodeType === 3; // Node type 3 is a text node
            }).remove();
            label.contents().unwrap();
			
            // Replace the dropdown selector
            var dropdownSelector = $('#carTable_length select[name="carTable_length"]');
            dropdownSelector
                .removeClass() // Remove existing classes
                .addClass('form-control ml-2 mr-2 mt-2') // Add Bootstrap classes
        }, 0); // You can adjust the delay time if needed
        
        $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
            var uniqueFilter = $('#filter-unique').prop('checked');
            var duplicateFilter = $('#filter-duplicates').prop('checked');
            var multiDuplicateFilter = $('#filter-multidupes').prop('checked');
        
            var gameFilters = $('.filter-game:checked').map(function() {
                return this.value;
            }).get();
        
            // If no game filters are selected, return false (show no rows)
            if (gameFilters.length === 0) {
                return false;
            }
        
            // Game filter logic
            var gameMatch = false;
            var row = table.row(dataIndex).node();
        
            gameFilters.forEach(function(gameId) {
                if ($(row).hasClass(gameId)) {
                    gameMatch = true;
                }
            });
        
            return (
                gameMatch && 
                (
                    (uniqueFilter && $(row).hasClass('unique-row')) ||
                    (duplicateFilter && $(row).hasClass('duplicate-row')) ||
                    (multiDuplicateFilter && $(row).hasClass('multi-duplicate-row'))
                )
            );
        });
        
        $('.filter, .filter-game').on('change', function() {
            table.draw();
        });
        
        // Fetch autocomplete data and apply Bootstrap 4 Autocomplete to the search input
        $.getJSON('car_details/autocomplete_data.json', function(data) {
            var src = data.manufacturers.reduce(function(map, obj) {
                map[obj] = obj; // Map each manufacturer name to itself
                return map;
            }, {});

            function onSelectItem(item, element) {
                $(element).val(item.label); // Set the input value to the selected label
                table.search(item.label).draw(); // Perform the search in DataTable
            }

            $('#carTable_filter input[type="search"]').autocomplete({
                source: src,
                onSelectItem: onSelectItem,
                highlightClass: 'text-danger'
            });
        });
        
        // Event listener for opening modal and loading content
        $('#carTable').on('click', '.details-button', function() {
            var detailsUrl = $(this).data('details-url');
            $('#dynamicModalContent').load(detailsUrl, function() {
                // After loading, find the modal inside the content and show it
                $('#dynamicModalContent .modal').modal('show');
            });
        });
    });
</script>
</body>
</html>
"""

# Extract the friendly names from the manufacturer_codes dictionary
autocomplete_data = {
    "manufacturers": list(manufacturer_codes.values())
}

# Writing JSON data to the car_details folder
json_filename = 'car_details/autocomplete_data.json'
with open(json_filename, 'w') as json_file:
    json.dump({"manufacturers": list(manufacturer_codes.values())}, json_file)

print(f"Autocomplete JSON data saved to '{json_filename}'")

# Write to HTML file
output_file_path = 'car_subfolders.html'
with open(output_file_path, 'w') as file:
    file.write(html_output)

print(f"The HTML file with a color-coded table of car subfolders has been written to '{output_file_path}'")