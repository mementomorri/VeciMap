# Ferias CLI Toolkit

A comprehensive Python CLI toolkit for scraping municipal feria vecinal (neighborhood market) data and generating interactive maps.

## Features

🔍 **Web Scraping**: Extracts feria data from municipal websites with intelligent pattern matching
🗺️ **Interactive Maps**: Generates color-coded maps using OpenStreetMap and Folium
📸 **PNG Export**: Optional screenshot generation using Node.js and Puppeteer
🎨 **Color Coding**: Each day of the week has a distinct color for easy identification

## Installation

### Prerequisites

- Python 3.7 or higher
- Node.js (optional, for PNG snapshot generation)

### Setup

1. **Clone or download the project**:
   ```bash
   git clone <repository-url>
   cd ferias-cli
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies** (optional, for PNG snapshots):
   ```bash
   npm install puppeteer
   ```

## Usage

### 1. Scraping Feria Data

The scraper extracts structured data from municipal websites and outputs JSON.

#### Basic Usage

```bash
# Scrape a single URL
python scrape_ferias_json.py -u "http://montevideo.gub.uy/areas-tematicas/cultura-y-tiempo-libre/ferias-vecinales-en-el-municipio-b"

# Scrape multiple URLs
python scrape_ferias_json.py -u "http://url1.com" -u "http://url2.com" -u "http://url3.com"

# Use a file with URLs (one per line)
python scrape_ferias_json.py -f urls.txt

# Specify custom output file
python scrape_ferias_json.py -u "http://url.com" -o my_ferias.json

# Enable verbose output
python scrape_ferias_json.py -u "http://url.com" -v
```

#### URL File Format

Create a text file with one URL per line:
```
http://montevideo.gub.uy/areas-tematicas/cultura-y-tiempo-libre/ferias-vecinales-en-el-municipio-a
http://montevideo.gub.uy/areas-tematicas/cultura-y-tiempo-libre/ferias-vecinales-en-el-municipio-b
http://montevideo.gub.uy/areas-tematicas/cultura-y-tiempo-libre/ferias-vecinales-en-el-municipio-c
```

#### Output Format

The scraper generates a JSON file with the following structure:

```json
[
  {
    "barrio": "Barrio Sur",
    "street": "Convención",
    "from": "Soriano",
    "to": "Canelones",
    "day": "Miércoles",
    "raw": "Barrio Sur: Convención desde Soriano hasta Canelones – Miércoles"
  }
]
```

### 2. Generating Interactive Maps

The map generator creates interactive HTML maps with color-coded markers.

#### Basic Usage

```bash
# Generate map from default ferias.json
python generate_ferias_map.py

# Specify custom input and output files
python generate_ferias_map.py -i my_ferias.json -o my_map.html

# Generate map with PNG snapshot
python generate_ferias_map.py -i ferias.json --snapshot

# Custom PNG output filename
python generate_ferias_map.py -i ferias.json --snapshot --png-output my_map.png

# Enable verbose output
python generate_ferias_map.py -i ferias.json -v
```

#### Map Features

- **Color-coded markers** by day of the week:
  - Lunes → Blue
  - Martes → Green
  - Miércoles → Purple
  - Jueves → Orange
  - Viernes → Dark Red
  - Sábado → Red
  - Domingo → Cadet Blue

- **Interactive popups** showing:
  - Neighborhood (barrio)
  - Street name
  - Start and end streets
  - Day of operation

- **Legend** showing color coding for each day

### 3. Complete Workflow Example

```bash
# Step 1: Scrape data from multiple municipalities
python scrape_ferias_json.py \
  -u "http://montevideo.gub.uy/areas-tematicas/cultura-y-tiempo-libre/ferias-vecinales-en-el-municipio-a" \
  -u "http://montevideo.gub.uy/areas-tematicas/cultura-y-tiempo-libre/ferias-vecinales-en-el-municipio-b" \
  -o ferias.json \
  -v

# Step 2: Generate interactive map
python generate_ferias_map.py -i ferias.json -o ferias_map.html -v

# Step 3: Generate PNG snapshot (optional)
python generate_ferias_map.py -i ferias.json --snapshot
```

## File Structure

```
ferias-cli/
├── scrape_ferias_json.py      # Main scraper script
├── generate_ferias_map.py     # Map generator script
├── requirements.txt           # Python dependencies
├── README.md                 # This file
├── ferias.json              # Generated feria data (example)
├── ferias_map.html          # Generated interactive map (example)
└── ferias_map.png           # Generated PNG snapshot (example)
```

## Technical Details

### Scraping Engine

The scraper uses multiple pattern matching strategies to extract feria information:

1. **Regex Patterns**: Matches common text patterns like "Barrio: Street desde Start hasta End – Day"
2. **HTML Element Analysis**: Searches through lists, paragraphs, and table cells
3. **Text Cleaning**: Removes extra whitespace and validates extracted data
4. **Duplicate Prevention**: Ensures no duplicate entries are added

### Geocoding

- Uses OpenStreetMap Nominatim API for address geocoding
- Implements retry logic with exponential backoff
- Adds Montevideo context to improve geocoding accuracy
- Calculates midpoint between start and end streets for marker placement

### Map Generation

- Built with Folium (Python wrapper for Leaflet.js)
- Uses OpenStreetMap tiles
- Responsive design with interactive markers
- Includes legend and tooltips

### PNG Snapshot

- Uses Node.js and Puppeteer for headless browser rendering
- Automatically installs Puppeteer if not present
- Configurable viewport size and output format

## Troubleshooting

### Common Issues

1. **Geocoding Failures**: Some addresses may not be found. The tool will skip these and continue with successful geocodings.

2. **Rate Limiting**: The scraper includes delays between requests to be respectful to servers.

3. **Node.js Not Found**: PNG snapshot generation requires Node.js. Install it from [nodejs.org](https://nodejs.org/).

4. **Puppeteer Installation**: The tool will automatically install Puppeteer if needed, but this requires an internet connection.

### Error Messages

- `"No URLs provided"`: Use `-u` or `-f` options to specify URLs
- `"Input file not found"`: Check that the JSON file exists
- `"No locations could be geocoded"`: Try with different addresses or check internet connection

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the toolkit.

## License

This project is open source and available under the MIT License. 