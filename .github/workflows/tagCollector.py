import os
import subprocess
import json
import requests
from git import Repo
import re
from enum import Enum
from packaging import version

def clone_repository(repo_url, repo_dir):
    if not os.path.exists(repo_dir):
        subprocess.run(['git', 'clone', repo_url, repo_dir])
    else:
        print(f"Repository {repo_dir} already exists")

def checkout_branch(repo_dir, branch='origin/main'):
    subprocess.run(['git', '-C', repo_dir, 'checkout', branch])

'''
def inspect_dockerfile_for_variants(repo_dir):
    dockerfile_path = os.path.join(repo_dir, 'docker/Dockerfile')
    variant_files = [f for f in os.listdir(os.path.join(repo_dir, 'docker'))] #if f.startswith('manifest-') and f.endswith('.json')]
    variants = {}
    
    with open(dockerfile_path, 'r') as dockerfile:
        for line in dockerfile:
            if line.startswith('FROM'):
                # Check if variants exist
                if '{VARIANT}' in line:
                    for variant_file in variant_files:
                        variant_name = variant_file.split('-')[1].replace('.json', '')
                        variants[variant_name] = variant_file
                    return variants  # Variant available
                else:
                    return False  # No variants
'''
def inspect_dockerfile_for_variants(repo_dir):
    dockerfile_path = os.path.join(repo_dir, 'docker/Dockerfile')
    variant_files = [f for f in os.listdir(os.path.join(repo_dir, 'docker'))]
    variants = {}
    
    with open(dockerfile_path, 'r') as dockerfile:
        for line in dockerfile:
            if line.startswith('FROM'):
                if '{VARIANT}' in line:
                    for variant_file in variant_files:
                        variant_name = variant_file.split('-')[1].replace('.json', '')
                        variants[variant_name] = variant_file
                    return variants
                else:
                    return False

repo_dir = os.getenv('GITHUB_WORKSPACE', '/path/to/repo')
image_name = "example_image"
variants = inspect_dockerfile_for_variants(repo_dir)

    
def fetch_and_sort_tags(image_name, variants):
    tags = {}
    docker_hub_url = "https://hub.docker.com/v2/repositories"

    if not variants:
        # No variant found
        url = f"{docker_hub_url}/{image_name}/tags/"
        response = requests.get(url)
        if response.status_code == 200:
            tags_data = response.json()['results']
            tags = sorted([tag['name'] for tag in tags_data])
        else:
            print(f"Error fetching tags for {image_name}")
    else:
        # Variant found
        for variant_name in variants.keys():
            url = f"{docker_hub_url}/{image_name}-{variant_name}/tags/"
            response = requests.get(url)
            if response.status_code == 200:
                tags_data = response.json()['results']
                tags[variant_name] = sorted([tag['name'] for tag in tags_data])
            else:
                print(f"Error fetching tags for {image_name}-{variant_name}")
    
    return tags

def find_common_tags(variant_tags):
    if not isinstance(variant_tags, dict) or len(variant_tags) < 2:
        print("Not enough variants found.")
        return None

    # Find common tags
    common_tags = set(variant_tags[next(iter(variant_tags))]) 
    for tags in variant_tags.values():
        common_tags.intersection_update(tags)  
    
    return sorted(common_tags)

def collect_repo_tags(repo_dir):
    tag_file_path = os.path.join(repo_dir, 'tags')
    repo_tags = []

    if os.path.exists(tag_file_path):
        with open(tag_file_path, 'r') as file:
            repo_tags = [line.strip() for line in file.readlines()]

    return sorted(repo_tags)

def find_newer_versions(repo_tags, common_tags):
    repo_tags_sorted = sorted(repo_tags, key=version.parse)
    common_tags_sorted = sorted(common_tags, key=version.parse)
    
    for tag in common_tags_sorted:
        if tag not in repo_tags_sorted:
            os.environ['newversion'] = tag
            return tag  
    return None
    
repo_dir = "/path/to/repo"
image_name = "example_image"
variants = inspect_dockerfile_for_variants(repo_dir)

variant_tags = fetch_and_sort_tags(image_name, variants)

if variants:
    common_tags = find_common_tags(variant_tags)
else:
    common_tags = variant_tags 

repo_tags = collect_repo_tags(repo_dir)
newer_version = find_newer_versions(repo_tags, common_tags)

if newer_version:
    print(f"New version found: {newer_version}")
else:
    print("No new version found.")
