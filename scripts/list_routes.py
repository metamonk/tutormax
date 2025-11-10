#!/usr/bin/env python3
"""
Script to list all API routes and endpoints in the TutorMax application.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.main import app


def list_routes():
    """List all routes in the FastAPI application."""
    routes = []

    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            methods = sorted(route.methods)
            path = route.path
            name = route.name if hasattr(route, "name") else ""
            tags = route.tags if hasattr(route, "tags") else []

            routes.append({
                "path": path,
                "methods": methods,
                "name": name,
                "tags": tags,
            })

    # Sort by path
    routes.sort(key=lambda x: x["path"])

    # Group by tags
    routes_by_tag = {}
    untagged = []

    for route in routes:
        if route["tags"]:
            for tag in route["tags"]:
                if tag not in routes_by_tag:
                    routes_by_tag[tag] = []
                routes_by_tag[tag].append(route)
        else:
            untagged.append(route)

    # Print organized output
    print("=" * 80)
    print("TutorMax API Routes")
    print("=" * 80)
    print()

    # Print by tags
    for tag in sorted(routes_by_tag.keys()):
        print(f"\n{'='*80}")
        print(f"  {tag}")
        print(f"{'='*80}")
        for route in routes_by_tag[tag]:
            methods_str = ", ".join(route["methods"])
            print(f"  {methods_str:20} {route['path']}")
            if route["name"]:
                print(f"  {' '*20} └─ {route['name']}")

    # Print untagged routes
    if untagged:
        print(f"\n{'='*80}")
        print("  Untagged Routes")
        print(f"{'='*80}")
        for route in untagged:
            methods_str = ", ".join(route["methods"])
            print(f"  {methods_str:20} {route['path']}")
            if route["name"]:
                print(f"  {' '*20} └─ {route['name']}")

    print(f"\n{'='*80}")
    print(f"Total Routes: {len(routes)}")
    print(f"{'='*80}")

    # Print summary
    print("\n\nQuick Access URLs (when running on http://localhost:8000):")
    print("  Interactive Docs:  http://localhost:8000/docs")
    print("  ReDoc:            http://localhost:8000/redoc")
    print("  OpenAPI Schema:   http://localhost:8000/openapi.json")
    print()


if __name__ == "__main__":
    try:
        list_routes()
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure to install dependencies: pip install -r requirements.txt")
        sys.exit(1)
