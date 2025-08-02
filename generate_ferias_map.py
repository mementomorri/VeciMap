#!/usr/bin/env python3
"""
Ferias Vecinales Map Generator

Generates an interactive map from feria data JSON file.
Creates color-coded markers for each feria based on the day of the week.
"""

import json
import sys
import subprocess
import os
from typing import List, Dict, Tuple, Optional
import click
import folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from tqdm import tqdm
import time
import re


class FeriasMapGenerator:
    """Generator for interactive maps of feria vecinal locations."""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="ferias-cli/1.0")
        self.day_colors = {
            'Lunes': 'blue',
            'Martes': 'green', 
            'Miércoles': 'purple',
            'Jueves': 'orange',
            'Viernes': 'darkred',
            'Sábado': 'red',
            'Domingo': 'cadetblue'
        }
        # Montevideo center coordinates as fallback
        self.montevideo_center = (-34.9011, -56.1645)
    
    def clean_address(self, address: str) -> str:
        """
        Clean and standardize address for better geocoding.
        
        Args:
            address: Raw address string
            
        Returns:
            Cleaned address string
        """
        # Remove common prefixes and suffixes
        address = re.sub(r'^la calle\s+', '', address, flags=re.IGNORECASE)
        address = re.sub(r'^el\s+', '', address, flags=re.IGNORECASE)
        address = re.sub(r'\s+el\s+Nº\s+\d+.*$', '', address, flags=re.IGNORECASE)
        address = re.sub(r'\s+desde\s+', ' ', address, flags=re.IGNORECASE)
        address = re.sub(r'\s+hasta\s+', ' ', address, flags=re.IGNORECASE)
        address = re.sub(r'\s+entre\s+', ' ', address, flags=re.IGNORECASE)
        address = re.sub(r'\s+y\s+', ' ', address, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        address = re.sub(r'\s+', ' ', address).strip()
        
        return address
    
    def geocode_address(self, address: str, max_retries: int = 3) -> Optional[Tuple[float, float]]:
        """
        Geocode an address using Nominatim API.
        
        Args:
            address: Address to geocode
            max_retries: Maximum number of retry attempts
            
        Returns:
            Tuple of (latitude, longitude) or None if geocoding fails
        """
        for attempt in range(max_retries):
            try:
                # Add Montevideo context to improve geocoding accuracy
                full_address = f"{address}, Montevideo, Uruguay"
                location = self.geolocator.geocode(full_address, timeout=10)
                
                if location:
                    # Verify the location is actually in Montevideo (rough check)
                    lat, lon = location.latitude, location.longitude
                    if -34.95 <= lat <= -34.85 and -56.25 <= lon <= -56.05:
                        return (lat, lon)
                
                # If first attempt fails, try without Montevideo context
                location = self.geolocator.geocode(address, timeout=10)
                if location:
                    lat, lon = location.latitude, location.longitude
                    # Verify the location is actually in Montevideo (rough check)
                    if -34.95 <= lat <= -34.85 and -56.25 <= lon <= -56.05:
                        return (lat, lon)
                
            except (GeocoderTimedOut, GeocoderUnavailable) as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    return None
            except Exception as e:
                return None
        
        return None
    
    def geocode_feria_location(self, feria: Dict, verbose: bool = False) -> Optional[Tuple[float, float]]:
        """
        Geocode a feria location using multiple strategies.
        
        Args:
            feria: Feria dictionary
            verbose: Whether to show verbose output
            
        Returns:
            Tuple of (latitude, longitude) or None if geocoding fails
        """
        street = self.clean_address(feria['street'])
        from_street = self.clean_address(feria['from'])
        to_street = self.clean_address(feria['to'])
        barrio = feria['barrio']
        
        # Determine if this is an intersection (from == to) or a street range
        is_intersection = from_street == to_street
        
        if is_intersection:
            # This is an intersection between two streets
            strategies = [
                # Strategy 1: Intersection with barrio
                f"{street} y {from_street}, {barrio}, Montevideo, Uruguay",
                # Strategy 2: Intersection without barrio
                f"{street} y {from_street}, Montevideo, Uruguay",
                # Strategy 3: Street with barrio
                f"{street}, {barrio}, Montevideo, Uruguay",
                # Strategy 4: From street with barrio
                f"{from_street}, {barrio}, Montevideo, Uruguay",
                # Strategy 5: Barrio center
                f"{barrio}, Montevideo, Uruguay"
            ]
        else:
            # This is a street range (from != to)
            strategies = [
                # Strategy 1: Street with barrio
                f"{street}, {barrio}, Montevideo, Uruguay",
                # Strategy 2: Street intersection with from street
                f"{street} y {from_street}, Montevideo, Uruguay",
                # Strategy 3: Street intersection with to street
                f"{street} y {to_street}, Montevideo, Uruguay",
                # Strategy 4: Just street name with Montevideo
                f"{street}, Montevideo, Uruguay",
                # Strategy 5: Barrio center
                f"{barrio}, Montevideo, Uruguay"
            ]
        
        for i, strategy in enumerate(strategies):
            if verbose:
                click.echo(f"  Strategy {i+1}: {strategy}")
            
            location = self.geocode_address(strategy)
            if location:
                if verbose:
                    click.echo(f"  ✓ Found: {location[0]}, {location[1]}")
                return location
            
            time.sleep(0.5)  # Be respectful
        
        if verbose:
            click.echo(f"  ✗ All strategies failed for {street}")
        return None
    
    def generate_map(self, ferias: List[Dict], output_file: str = 'ferias_map.html', verbose: bool = False) -> bool:
        """
        Generate an interactive HTML map from feria data.
        
        Args:
            ferias: List of feria dictionaries
            output_file: Output HTML file path
            verbose: Whether to show verbose output
            
        Returns:
            True if successful, False otherwise
        """
        if not ferias:
            click.echo("No feria data provided.", err=True)
            return False
        
        # Geocode all ferias
        successful_geocoding = 0
        geocoded_ferias = []
        
        click.echo("Geocoding feria locations...")
        
        for feria in tqdm(ferias, desc="Processing ferias"):
            coordinates = self.geocode_feria_location(feria, verbose)
            
            if coordinates:
                feria['coordinates'] = coordinates
                geocoded_ferias.append(feria)
                successful_geocoding += 1
            else:
                feria['coordinates'] = None
                if verbose:
                    click.echo(f"Failed to geocode: {feria['street']} in {feria['barrio']}")
            
            time.sleep(1)  # Be respectful with API requests
        
        if not geocoded_ferias:
            click.echo("No locations could be geocoded. Cannot generate map.", err=True)
            return False
        
        # Calculate map center from successful coordinates
        if geocoded_ferias:
            avg_lat = sum(feria['coordinates'][0] for feria in geocoded_ferias) / len(geocoded_ferias)
            avg_lon = sum(feria['coordinates'][1] for feria in geocoded_ferias) / len(geocoded_ferias)
            center = [avg_lat, avg_lon]
        else:
            center = list(self.montevideo_center)
        
        # Create the map
        m = folium.Map(
            location=center,
            zoom_start=13,
            tiles='OpenStreetMap'
        )
        
        # Add markers for each successfully geocoded feria
        for feria in geocoded_ferias:
            lat, lon = feria['coordinates']
            day = feria['day']
            color = self.day_colors.get(day, 'gray')
            
            # Create popup content
            is_intersection = feria['from'] == feria['to']
            
            if is_intersection:
                location_desc = f"{feria['street']} y {feria['from']}"
            else:
                location_desc = f"{feria['street']} entre {feria['from']} y {feria['to']}"
            
            popup_content = f"""
            <div style="font-family: Arial, sans-serif; min-width: 250px; max-width: 300px;">
                <h4 style="margin: 0 0 10px 0; color: #333; border-bottom: 2px solid {color}; padding-bottom: 5px;">
                    {feria['barrio']}
                </h4>
                <p style="margin: 8px 0;"><strong>Ubicación:</strong> {location_desc}</p>
                <p style="margin: 8px 0;"><strong>Día:</strong> <span style="color: {color}; font-weight: bold;">{day}</span></p>
            </div>
            """
            
            # Add marker
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=350),
                icon=folium.Icon(color=color, icon='shopping-cart', prefix='fa'),
                tooltip=f"{feria['barrio']} - {day}"
            ).add_to(m)
        
        # Add improved legend
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 20px; left: 20px; 
                    background-color: white; 
                    border: 2px solid #666; 
                    border-radius: 8px;
                    z-index: 9999; 
                    font-family: Arial, sans-serif;
                    font-size: 12px; 
                    padding: 15px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                    max-height: 300px;
                    overflow-y: auto;">
        <h4 style="margin: 0 0 15px 0; color: #333; text-align: center; border-bottom: 1px solid #ccc; padding-bottom: 8px;">
            Días de la Semana
        </h4>
        '''
        
        for day, color in self.day_colors.items():
            legend_html += f'''
            <div style="margin: 5px 0; display: flex; align-items: center;">
                <i class="fa fa-circle" style="color: {color}; margin-right: 8px; font-size: 14px;"></i>
                <span style="color: #333;">{day}</span>
            </div>
            '''
        
        legend_html += '</div>'
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Save the map
        try:
            m.save(output_file)
            click.echo(f"Successfully generated map with {successful_geocoding}/{len(ferias)} ferias at {output_file}")
            if successful_geocoding < len(ferias):
                click.echo(f"Warning: {len(ferias) - successful_geocoding} ferias could not be geocoded and were excluded from the map.")
            return True
        except Exception as e:
            click.echo(f"Error saving map to {output_file}: {e}", err=True)
            return False
    
    def generate_png_snapshot(self, html_file: str, output_png: str = 'ferias_map.png') -> bool:
        """
        Generate a PNG snapshot of the HTML map using Node.js and Puppeteer.
        
        Args:
            html_file: Path to the HTML map file
            output_png: Output PNG file path
            
        Returns:
            True if successful, False otherwise
        """
        # Check if Node.js is available
        try:
            subprocess.run(['node', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            click.echo("Node.js is not installed or not available in PATH.", err=True)
            return False
        
        # Create a simple Node.js script to capture the HTML
        node_script = f'''
const puppeteer = require('puppeteer');
const path = require('path');

(async () => {{
    const browser = await puppeteer.launch({{headless: true}});
    const page = await browser.newPage();
    
    // Load the HTML file
    const htmlPath = path.resolve('{html_file}');
    await page.goto(`file://${{htmlPath}}`);
    
    // Wait for map to load
    await page.waitForTimeout(3000);
    
    // Set viewport size
    await page.setViewport({{width: 1200, height: 800}});
    
    // Take screenshot
    await page.screenshot({{
        path: '{output_png}',
        fullPage: false
    }});
    
    await browser.close();
    console.log('Screenshot saved to {output_png}');
}})();
'''
        
        # Write the Node.js script to a temporary file
        script_file = 'temp_screenshot.js'
        try:
            with open(script_file, 'w') as f:
                f.write(node_script)
            
            # Check if Puppeteer is installed
            try:
                subprocess.run(['npm', 'list', 'puppeteer'], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                click.echo("Installing Puppeteer...")
                subprocess.run(['npm', 'install', 'puppeteer'], check=True)
            
            # Run the screenshot script
            result = subprocess.run(['node', script_file], capture_output=True, text=True)
            
            if result.returncode == 0:
                click.echo(f"Successfully generated PNG snapshot: {output_png}")
                return True
            else:
                click.echo(f"Error generating PNG: {result.stderr}", err=True)
                return False
                
        except Exception as e:
            click.echo(f"Error creating PNG snapshot: {e}", err=True)
            return False
        finally:
            # Clean up temporary script file
            if os.path.exists(script_file):
                os.remove(script_file)


@click.command()
@click.option('--input', '-i', default='ferias.json', help='Input JSON file path')
@click.option('--output', '-o', default='ferias_map.html', help='Output HTML file path')
@click.option('--snapshot', '-s', is_flag=True, help='Generate PNG snapshot of the map')
@click.option('--png-output', default='ferias_map.png', help='Output PNG file path (when using --snapshot)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def main(input, output, snapshot, png_output, verbose):
    """
    Generate an interactive map from feria data JSON file.
    
    Example usage:
        python generate_ferias_map.py -i ferias.json -o my_map.html
        
        python generate_ferias_map.py -i ferias.json --snapshot
    """
    
    # Check if input file exists
    if not os.path.exists(input):
        click.echo(f"Input file not found: {input}", err=True)
        sys.exit(1)
    
    # Load feria data
    try:
        with open(input, 'r', encoding='utf-8') as f:
            ferias = json.load(f)
        
        if verbose:
            click.echo(f"Loaded {len(ferias)} ferias from {input}")
    
    except json.JSONDecodeError as e:
        click.echo(f"Error parsing JSON file {input}: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error reading file {input}: {e}", err=True)
        sys.exit(1)
    
    # Initialize map generator
    generator = FeriasMapGenerator()
    
    # Generate the HTML map
    if not generator.generate_map(ferias, output, verbose):
        sys.exit(1)
    
    # Generate PNG snapshot if requested
    if snapshot:
        if verbose:
            click.echo("Generating PNG snapshot...")
        
        if not generator.generate_png_snapshot(output, png_output):
            click.echo("Warning: PNG snapshot generation failed, but HTML map was created successfully.", err=True)


if __name__ == '__main__':
    main() 