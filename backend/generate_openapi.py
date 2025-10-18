#!/usr/bin/env python3
"""
Generate OpenAPI specification from FastAPI application.
"""

import json
import os
import sys
import yaml

# Suppress all logging during import
os.environ['LOG_LEVEL'] = 'CRITICAL'
os.environ['DEVELOPMENT'] = 'false'

# Redirect stderr temporarily
import io
original_stderr = sys.stderr
sys.stderr = io.StringIO()

try:
    from app.main import app
    
    # Restore stderr
    sys.stderr = original_stderr
    
    # Generate OpenAPI spec
    openapi_spec = app.openapi()
    
    # Write JSON version
    with open('../contracts/openapi.json', 'w') as f:
        json.dump(openapi_spec, f, indent=2)
    
    # Write YAML version
    with open('../contracts/openapi.yaml', 'w') as f:
        yaml.dump(openapi_spec, f, default_flow_style=False, sort_keys=False)
    
    print("✅ OpenAPI specification generated successfully")
    print(f"   - JSON: contracts/openapi.json")
    print(f"   - YAML: contracts/openapi.yaml")
    
except Exception as e:
    sys.stderr = original_stderr
    print(f"❌ Error generating OpenAPI spec: {e}")
    sys.exit(1)