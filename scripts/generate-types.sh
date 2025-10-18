#!/bin/bash
# Generate TypeScript types from OpenAPI specification
# Usage: ./scripts/generate-types.sh

echo "🔄 Generating TypeScript types from OpenAPI specification..."

# Check if backend is running
if ! curl -s -f http://localhost:8000/health > /dev/null; then
    echo "❌ Backend server is not running or not healthy"
    echo "Please start the backend server first:"
    echo "  cd backend && uvicorn app.main:app --reload"
    exit 1
fi

# Navigate to frontend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_PATH="$SCRIPT_DIR/../frontend"
cd "$FRONTEND_PATH"

# Check if openapi-typescript is installed
if [ ! -f "node_modules/.bin/openapi-typescript" ]; then
    echo "📦 Installing openapi-typescript..."
    npm install --save-dev openapi-typescript
fi

# Generate types
echo "🔧 Generating types..."

# Create contracts directory if it doesn't exist
CONTRACTS_PATH="$SCRIPT_DIR/../contracts"
GENERATED_PATH="$CONTRACTS_PATH/generated"
mkdir -p "$GENERATED_PATH"

# Fetch OpenAPI spec and generate TypeScript types
OPENAPI_URL="http://localhost:8000/openapi.json"
OUTPUT_PATH="$GENERATED_PATH/api.ts"

if npx openapi-typescript "$OPENAPI_URL" --output "$OUTPUT_PATH"; then
    echo "✅ TypeScript types generated successfully!"
    echo "📁 Types available at: $OUTPUT_PATH"
    
    # Show file size for verification
    FILE_SIZE=$(stat -f%z "$OUTPUT_PATH" 2>/dev/null || stat -c%s "$OUTPUT_PATH" 2>/dev/null)
    FILE_SIZE_KB=$((FILE_SIZE / 1024))
    echo "📊 Generated file size: ${FILE_SIZE_KB} KB"
else
    echo "❌ Failed to generate types"
    exit 1
fi

# Optional: Run TypeScript check on generated types
echo "🔍 Validating generated types..."
if npx tsc --noEmit --skipLibCheck "$OUTPUT_PATH" 2>/dev/null; then
    echo "✅ Generated types are valid!"
else
    echo "⚠️ Warning: Generated types have TypeScript issues"
    echo "This is usually not a problem and types should still work"
fi

echo "🎉 Type generation completed!"