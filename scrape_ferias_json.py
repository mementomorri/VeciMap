#!/usr/bin/env python3
"""
Ferias Vecinales Scraper

Scrapes data from municipal websites to extract information about neighborhood markets (ferias vecinales).
Outputs structured JSON data with location and schedule information.
"""

import json
import re
import sys
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import click
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import time


class FeriasScraper:
    """Scraper for extracting feria vecinal data from municipal websites."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def extract_ferias_from_page(self, url: str) -> List[Dict]:
        """
        Extract feria data from a single municipal page.
        
        Args:
            url: URL of the municipal page containing feria information
            
        Returns:
            List of dictionaries containing feria data
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            ferias = []
            
            # Find the main content area that contains the feria information
            # Look for the div with class that contains the feria content
            content_div = soup.find('div', class_='field--name-field-art-cuerpo-contenido')
            if not content_div:
                # Fallback: look for any div containing feria information
                content_div = soup.find('div', string=re.compile(r'feria', re.IGNORECASE))
            
            if not content_div:
                click.echo(f"No feria content found on {url}", err=True)
                return []
            
            # Extract ferias from the structured HTML
            current_barrio = "Desconocido"
            
            # Process each element in the content
            for element in content_div.find_all(['h2', 'h3', 'ul', 'li']):
                if element.name in ['h2', 'h3']:
                    # This is a barrio header
                    barrio_text = element.get_text().strip()
                    if barrio_text and len(barrio_text) > 2 and not barrio_text.startswith('CCZ'):
                        current_barrio = barrio_text
                
                elif element.name == 'ul':
                    # This is a list of ferias for the current barrio
                    for li in element.find_all('li'):
                        li_text = li.get_text().strip()
                        if li_text and any(day in li_text.lower() for day in ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']):
                            # Extract feria information from this list item
                            feria_data = self._parse_feria_text(li_text, current_barrio)
                            if feria_data:
                                ferias.append(feria_data)
            
            return ferias
            
        except requests.RequestException as e:
            click.echo(f"Error fetching {url}: {e}", err=True)
            return []
        except Exception as e:
            click.echo(f"Error processing {url}: {e}", err=True)
            return []
    
    def _parse_feria_text(self, text: str, barrio: str) -> Optional[Dict]:
        """
        Parse a single feria text line and extract structured data.
        
        Args:
            text: The text containing feria information
            barrio: The barrio name
            
        Returns:
            Dictionary with feria data or None if parsing fails
        """
        # Clean the text
        text = text.strip()
        
        # Pattern 1: "Street entre Start y End. Day"
        pattern1 = r'([A-Za-záéíóúñ\s\.]+)\s+entre\s+([A-Za-záéíóúñ\s\.]+)\s+y\s+([A-Za-záéíóúñ\s\.]+)\.\s*\*\*([A-Za-záéíóúñ]+)\*\*'
        match = re.search(pattern1, text)
        if match:
            street = match.group(1).strip()
            from_street = match.group(2).strip()
            to_street = match.group(3).strip()
            day = match.group(4).strip()
            return self._create_feria_data(barrio, street, from_street, to_street, day, text)
        
        # Pattern 2: "Street entre Start y End. Day" (without bold)
        pattern2 = r'([A-Za-záéíóúñ\s\.]+)\s+entre\s+([A-Za-záéíóúñ\s\.]+)\s+y\s+([A-Za-záéíóúñ\s\.]+)\.\s*([A-Za-záéíóúñ]+)'
        match = re.search(pattern2, text)
        if match:
            street = match.group(1).strip()
            from_street = match.group(2).strip()
            to_street = match.group(3).strip()
            day = match.group(4).strip()
            return self._create_feria_data(barrio, street, from_street, to_street, day, text)
        
        # Pattern 3: "Street, desde Start hasta End. Day"
        pattern3 = r'([A-Za-záéíóúñ\s\.]+),\s+desde\s+([A-Za-záéíóúñ\s\.]+)\s+hasta\s+([A-Za-záéíóúñ\s\.]+)\.\s*\*\*([A-Za-záéíóúñ]+)\*\*'
        match = re.search(pattern3, text)
        if match:
            street = match.group(1).strip()
            from_street = match.group(2).strip()
            to_street = match.group(3).strip()
            day = match.group(4).strip()
            return self._create_feria_data(barrio, street, from_street, to_street, day, text)
        
        # Pattern 4: "Street, desde Start hasta End. Day" (without bold)
        pattern4 = r'([A-Za-záéíóúñ\s\.]+),\s+desde\s+([A-Za-záéíóúñ\s\.]+)\s+hasta\s+([A-Za-záéíóúñ\s\.]+)\.\s*([A-Za-záéíóúñ]+)'
        match = re.search(pattern4, text)
        if match:
            street = match.group(1).strip()
            from_street = match.group(2).strip()
            to_street = match.group(3).strip()
            day = match.group(4).strip()
            return self._create_feria_data(barrio, street, from_street, to_street, day, text)
        
        # Pattern 5: "Street y Start. Day" (simpler format)
        pattern5 = r'([A-Za-záéíóúñ\s\.]+)\s+y\s+([A-Za-záéíóúñ\s\.]+)\.\s*\*\*([A-Za-záéíóúñ]+)\*\*'
        match = re.search(pattern5, text)
        if match:
            street = match.group(1).strip()
            from_street = match.group(2).strip()
            to_street = match.group(2).strip()  # Same as from for simple format
            day = match.group(3).strip()
            return self._create_feria_data(barrio, street, from_street, to_street, day, text)
        
        # Pattern 6: "Street y Start. Day" (without bold)
        pattern6 = r'([A-Za-záéíóúñ\s\.]+)\s+y\s+([A-Za-záéíóúñ\s\.]+)\.\s*([A-Za-záéíóúñ]+)'
        match = re.search(pattern6, text)
        if match:
            street = match.group(1).strip()
            from_street = match.group(2).strip()
            to_street = match.group(2).strip()  # Same as from for simple format
            day = match.group(3).strip()
            return self._create_feria_data(barrio, street, from_street, to_street, day, text)
        
        # Pattern 7: "Street desde Start hasta End. Day" (without comma)
        pattern7 = r'([A-Za-záéíóúñ\s\.]+)\s+desde\s+([A-Za-záéíóúñ\s\.]+)\s+hasta\s+([A-Za-záéíóúñ\s\.]+)\.\s*\*\*([A-Za-záéíóúñ]+)\*\*'
        match = re.search(pattern7, text)
        if match:
            street = match.group(1).strip()
            from_street = match.group(2).strip()
            to_street = match.group(3).strip()
            day = match.group(4).strip()
            return self._create_feria_data(barrio, street, from_street, to_street, day, text)
        
        # Pattern 8: "Street desde Start hasta End. Day" (without bold and comma)
        pattern8 = r'([A-Za-záéíóúñ\s\.]+)\s+desde\s+([A-Za-záéíóúñ\s\.]+)\s+hasta\s+([A-Za-záéíóúñ\s\.]+)\.\s*([A-Za-záéíóúñ]+)'
        match = re.search(pattern8, text)
        if match:
            street = match.group(1).strip()
            from_street = match.group(2).strip()
            to_street = match.group(3).strip()
            day = match.group(4).strip()
            return self._create_feria_data(barrio, street, from_street, to_street, day, text)
        
        # Pattern 9: More comprehensive pattern for complex cases with numbers and special chars
        pattern9 = r'([A-Za-záéíóúñ\s\.]+)\s+entre\s+([A-Za-záéíóúñ\s\.0-9]+)\s+y\s+([A-Za-záéíóúñ\s\.0-9]+)\.\s*([A-Za-záéíóúñ]+)'
        match = re.search(pattern9, text)
        if match:
            street = match.group(1).strip()
            from_street = match.group(2).strip()
            to_street = match.group(3).strip()
            day = match.group(4).strip()
            return self._create_feria_data(barrio, street, from_street, to_street, day, text)
        
        # Pattern 10: More comprehensive pattern for "y" cases with numbers and special chars
        pattern10 = r'([A-Za-záéíóúñ\s\.]+)\s+y\s+([A-Za-záéíóúñ\s\.0-9]+)\.\s*([A-Za-záéíóúñ]+)'
        match = re.search(pattern10, text)
        if match:
            street = match.group(1).strip()
            from_street = match.group(2).strip()
            to_street = match.group(2).strip()  # Same as from for simple format
            day = match.group(3).strip()
            return self._create_feria_data(barrio, street, from_street, to_street, day, text)
        
        # Pattern 11: More comprehensive pattern for "desde/hasta" cases with numbers and special chars
        pattern11 = r'([A-Za-záéíóúñ\s\.]+),\s+desde\s+([A-Za-záéíóúñ\s\.0-9]+)\s+hasta\s+([A-Za-záéíóúñ\s\.0-9]+)\.\s*([A-Za-záéíóúñ]+)'
        match = re.search(pattern11, text)
        if match:
            street = match.group(1).strip()
            from_street = match.group(2).strip()
            to_street = match.group(3).strip()
            day = match.group(4).strip()
            return self._create_feria_data(barrio, street, from_street, to_street, day, text)
        
        # Pattern 12: More comprehensive pattern for "desde/hasta" without comma, with numbers and special chars
        pattern12 = r'([A-Za-záéíóúñ\s\.]+)\s+desde\s+([A-Za-záéíóúñ\s\.0-9]+)\s+hasta\s+([A-Za-záéíóúñ\s\.0-9]+)\.\s*([A-Za-záéíóúñ]+)'
        match = re.search(pattern12, text)
        if match:
            street = match.group(1).strip()
            from_street = match.group(2).strip()
            to_street = match.group(3).strip()
            day = match.group(4).strip()
            return self._create_feria_data(barrio, street, from_street, to_street, day, text)
        
        # Pattern 13: Handle cases with "AV." abbreviation
        pattern13 = r'([A-Za-záéíóúñ\s\.]+)\s+entre\s+([A-Za-záéíóúñ\s\.0-9]+)\s+y\s+([A-Za-záéíóúñ\s\.0-9]+)\.\s*([A-Za-záéíóúñ]+)'
        match = re.search(pattern13, text)
        if match:
            street = match.group(1).strip()
            from_street = match.group(2).strip()
            to_street = match.group(3).strip()
            day = match.group(4).strip()
            return self._create_feria_data(barrio, street, from_street, to_street, day, text)
        
        # Pattern 14: Handle cases with "Nº" and other special characters
        pattern14 = r'([A-Za-záéíóúñ\s\.]+)\s+desde\s+([A-Za-záéíóúñ\s\.0-9º]+)\s+hasta\s+([A-Za-záéíóúñ\s\.0-9º]+)\.\s*([A-Za-záéíóúñ]+)'
        match = re.search(pattern14, text)
        if match:
            street = match.group(1).strip()
            from_street = match.group(2).strip()
            to_street = match.group(3).strip()
            day = match.group(4).strip()
            return self._create_feria_data(barrio, street, from_street, to_street, day, text)
        
        return None
    
    def _create_feria_data(self, barrio: str, street: str, from_street: str, to_street: str, day: str, raw_text: str) -> Optional[Dict]:
        """
        Create a feria data dictionary after validation.
        
        Args:
            barrio: Barrio name
            street: Street name
            from_street: Starting street
            to_street: Ending street
            day: Day of the week
            raw_text: Original text
            
        Returns:
            Dictionary with feria data or None if validation fails
        """
        # Clean up the data
        barrio = re.sub(r'\s+', ' ', barrio).strip()
        street = re.sub(r'\s+', ' ', street).strip()
        from_street = re.sub(r'\s+', ' ', from_street).strip()
        to_street = re.sub(r'\s+', ' ', to_street).strip()
        day = re.sub(r'\s+', ' ', day).strip()
        
        # Remove bold markers from day
        day = re.sub(r'\*\*', '', day)
        
        # Validate that we have meaningful data
        if (len(street) > 2 and 
            len(from_street) > 2 and len(to_street) > 2 and 
            len(day) > 2 and day.lower() in ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']):
            
            return {
                "barrio": barrio,
                "street": street,
                "from": from_street,
                "to": to_street,
                "day": day,
                "raw": raw_text
            }
        
        return None
    
    def scrape_multiple_urls(self, urls: List[str]) -> List[Dict]:
        """
        Scrape feria data from multiple URLs.
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            List of all feria data found across all URLs
        """
        all_ferias = []
        
        for url in tqdm(urls, desc="Scraping municipal pages"):
            ferias = self.extract_ferias_from_page(url)
            all_ferias.extend(ferias)
            
            # Be respectful with requests
            time.sleep(1)
        
        return all_ferias


def validate_url(url: str) -> bool:
    """Validate if a URL is properly formatted."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


@click.command()
@click.option('--urls', '-u', multiple=True, help='URLs to scrape (can specify multiple)')
@click.option('--url-file', '-f', type=click.Path(exists=True), help='File containing URLs (one per line)')
@click.option('--output', '-o', default='ferias.json', help='Output JSON file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def main(urls, url_file, output, verbose):
    """
    Scrape feria vecinal data from municipal websites.
    
    Example usage:
        python scrape_ferias_json.py -u "http://montevideo.gub.uy/areas-tematicas/cultura-y-tiempo-libre/ferias-vecinales-en-el-municipio-b"
        
        python scrape_ferias_json.py -f urls.txt -o my_ferias.json
    """
    
    # Collect URLs from different sources
    all_urls = list(urls)
    
    if url_file:
        try:
            with open(url_file, 'r') as f:
                file_urls = [line.strip() for line in f if line.strip()]
                all_urls.extend(file_urls)
        except Exception as e:
            click.echo(f"Error reading URL file: {e}", err=True)
            sys.exit(1)
    
    if not all_urls:
        click.echo("No URLs provided. Use --urls or --url-file options.", err=True)
        sys.exit(1)
    
    # Validate URLs
    valid_urls = [url for url in all_urls if validate_url(url)]
    invalid_urls = [url for url in all_urls if not validate_url(url)]
    
    if invalid_urls:
        click.echo(f"Warning: Invalid URLs found: {invalid_urls}", err=True)
    
    if not valid_urls:
        click.echo("No valid URLs provided.", err=True)
        sys.exit(1)
    
    if verbose:
        click.echo(f"Scraping {len(valid_urls)} URLs...")
        for url in valid_urls:
            click.echo(f"  - {url}")
    
    # Initialize scraper and scrape data
    scraper = FeriasScraper("")
    ferias = scraper.scrape_multiple_urls(valid_urls)
    
    if verbose:
        click.echo(f"Found {len(ferias)} ferias across all pages.")
    
    # Save results to JSON file
    try:
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(ferias, f, ensure_ascii=False, indent=2)
        
        click.echo(f"Successfully saved {len(ferias)} ferias to {output}")
        
        # Show summary
        if ferias:
            days_count = {}
            for feria in ferias:
                day = feria['day']
                days_count[day] = days_count.get(day, 0) + 1
            
            click.echo("\nSummary by day:")
            for day, count in sorted(days_count.items()):
                click.echo(f"  {day}: {count} ferias")
    
    except Exception as e:
        click.echo(f"Error saving to {output}: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main() 