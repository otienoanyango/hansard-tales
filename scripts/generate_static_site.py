#!/usr/bin/env python3
"""
Generate static HTML files from Jinja2 templates for GitHub Pages deployment.
"""
import os
import shutil
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape


def url_for(endpoint, **kwargs):
    """Mock Flask's url_for for static site generation."""
    if endpoint == 'static':
        filename = kwargs.get('filename', '')
        return f'/static/{filename}'
    elif endpoint == 'index':
        return '/index.html'
    elif endpoint == 'mps_list':
        return '/mps.html'
    elif endpoint == 'parties':
        return '/parties.html'
    elif endpoint == 'about':
        return '/about.html'
    elif endpoint == 'disclaimer':
        return '/disclaimer.html'
    elif endpoint == 'privacy':
        return '/privacy.html'
    else:
        return f'/{endpoint}.html'


def generate_static_site():
    """Generate static HTML files from templates."""
    # Setup paths
    base_dir = Path(__file__).parent.parent
    template_dir = base_dir / 'templates'
    dist_dir = base_dir / 'dist'
    
    # Clean and create dist directory
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(parents=True)
    
    # Copy static files
    static_src = base_dir / 'static'
    static_dst = dist_dir / 'static'
    if static_src.exists():
        shutil.copytree(static_src, static_dst)
    
    # Setup Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(['html', 'xml']),
        trim_blocks=True,
        lstrip_blocks=True
    )
    
    # Add global functions and variables
    env.globals['url_for'] = url_for
    env.globals['current_year'] = datetime.now().year
    env.globals['last_updated'] = datetime.now().strftime('%B %d, %Y')
    
    # Pages to generate
    pages = [
        ('pages/test.html', 'index.html', 'home'),
        ('pages/test.html', 'mps.html', 'mps'),
        ('pages/test.html', 'parties.html', 'parties'),
        ('pages/test.html', 'about.html', 'about'),
        ('pages/test.html', 'disclaimer.html', 'home'),
        ('pages/test.html', 'privacy.html', 'home'),
    ]
    
    # Generate each page
    for template_name, output_name, active_page in pages:
        template = env.get_template(template_name)
        html = template.render(active_page=active_page)
        
        output_path = dist_dir / output_name
        output_path.write_text(html)
        print(f'Generated: {output_name}')
    
    # Create .nojekyll file to prevent GitHub Pages from ignoring files starting with _
    (dist_dir / '.nojekyll').touch()
    
    print(f'\nStatic site generated in: {dist_dir}')
    print(f'Total files: {len(list(dist_dir.rglob("*")))}')


if __name__ == '__main__':
    generate_static_site()
