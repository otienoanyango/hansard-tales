#!/usr/bin/env python3
"""
Generate simple SVG party logos for Kenyan political parties.
Uses party colors and abbreviations to create clean, professional logos.
"""
import os
from pathlib import Path


# Party information with colors (based on official party colors)
PARTY_INFO = {
    'UDA': {'name': 'United Democratic Alliance', 'color': '#FFD700', 'text_color': '#000000'},  # Yellow/Gold
    'ODM': {'name': 'Orange Democratic Movement', 'color': '#FF8C00', 'text_color': '#FFFFFF'},  # Orange
    'KANU': {'name': 'Kenya African National Union', 'color': '#DC143C', 'text_color': '#FFFFFF'},  # Red
    'ANC': {'name': 'Amani National Congress', 'color': '#4169E1', 'text_color': '#FFFFFF'},  # Blue
    'JP': {'name': 'Jubilee Party', 'color': '#DC143C', 'text_color': '#FFFFFF'},  # Red
    'FORD-K': {'name': 'Forum for the Restoration of Democracy', 'color': '#228B22', 'text_color': '#FFFFFF'},  # Green
    'FORD - K': {'name': 'Forum for the Restoration of Democracy', 'color': '#228B22', 'text_color': '#FFFFFF'},  # Green (space variant)
    'WDM': {'name': 'Wiper Democratic Movement', 'color': '#4682B4', 'text_color': '#FFFFFF'},  # Steel Blue
    'DAP-K': {'name': 'Democratic Action Party', 'color': '#8B4513', 'text_color': '#FFFFFF'},  # Brown
    'CCM': {'name': 'Chama Cha Mashinani', 'color': '#FF6347', 'text_color': '#FFFFFF'},  # Tomato
    'KUP': {'name': 'Kenya Union Party', 'color': '#2F4F4F', 'text_color': '#FFFFFF'},  # Dark Slate Gray
    'MDG': {'name': 'Muungano Development Group', 'color': '#8B008B', 'text_color': '#FFFFFF'},  # Dark Magenta
    'MCCP': {'name': 'Maendeleo Chap Chap Party', 'color': '#FF4500', 'text_color': '#FFFFFF'},  # Orange Red
    'NAP-K': {'name': 'National Agenda Party', 'color': '#4B0082', 'text_color': '#FFFFFF'},  # Indigo
    'NOPEU': {'name': 'National Ordinary People Empowerment Union', 'color': '#006400', 'text_color': '#FFFFFF'},  # Dark Green
    'PAA': {'name': 'Pamoja African Alliance', 'color': '#8B4789', 'text_color': '#FFFFFF'},  # Purple
    'TSP': {'name': 'The Service Party', 'color': '#20B2AA', 'text_color': '#FFFFFF'},  # Light Sea Green
    'UDM': {'name': 'United Democratic Movement', 'color': '#4682B4', 'text_color': '#FFFFFF'},  # Steel Blue
    'UPA': {'name': 'United Progressive Alliance', 'color': '#FF1493', 'text_color': '#FFFFFF'},  # Deep Pink
    'UPIA': {'name': 'United People\'s Independent Alliance', 'color': '#9370DB', 'text_color': '#FFFFFF'},  # Medium Purple
    'GDDP': {'name': 'Grand Dream Development Party', 'color': '#DAA520', 'text_color': '#000000'},  # Goldenrod
    'IND': {'name': 'Independent', 'color': '#808080', 'text_color': '#FFFFFF'},  # Gray
    'IND.': {'name': 'Independent', 'color': '#808080', 'text_color': '#FFFFFF'},  # Gray (variant)
}


def generate_svg_logo(party_abbr, width=120, height=120):
    """Generate a simple SVG logo for a party."""
    party_info = PARTY_INFO.get(party_abbr, {
        'name': party_abbr,
        'color': '#6B7280',  # Gray-500
        'text_color': '#FFFFFF'
    })
    
    # Calculate font size based on abbreviation length
    abbr_length = len(party_abbr)
    if abbr_length <= 3:
        font_size = 36
    elif abbr_length <= 5:
        font_size = 28
    else:
        font_size = 20
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <!-- Background circle -->
  <circle cx="{width/2}" cy="{height/2}" r="{width/2 - 2}" fill="{party_info['color']}" stroke="#000000" stroke-width="2"/>
  
  <!-- Party abbreviation -->
  <text x="{width/2}" y="{height/2}" 
        font-family="Helvetica Neue, Arial, sans-serif" 
        font-size="{font_size}" 
        font-weight="bold" 
        fill="{party_info['text_color']}" 
        text-anchor="middle" 
        dominant-baseline="central">
    {party_abbr}
  </text>
</svg>'''
    
    return svg


def main():
    """Generate all party logos."""
    # Create output directory
    output_dir = Path('static/images/party-logos')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating party logos in {output_dir}/")
    
    # Generate logos for all parties
    for party_abbr in PARTY_INFO.keys():
        svg_content = generate_svg_logo(party_abbr)
        
        # Save to file (use safe filename)
        safe_filename = party_abbr.replace(' ', '-').replace('.', '')
        output_path = output_dir / f'{safe_filename}.svg'
        
        with open(output_path, 'w') as f:
            f.write(svg_content)
        
        print(f"  ✓ Generated {safe_filename}.svg")
    
    print(f"\nGenerated {len(PARTY_INFO)} party logos successfully!")
    print(f"Logos saved to: {output_dir}/")


if __name__ == '__main__':
    main()
