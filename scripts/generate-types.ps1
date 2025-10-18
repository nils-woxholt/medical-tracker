# Generate TypeScript types from OpenAPI specification
# Usage: ./scripts/generate-types.ps1

Write-Host "🔄 Generating TypeScript types from OpenAPI specification..." -ForegroundColor Blue

# Check if OpenAPI contract exists
$contractPath = Join-Path $PSScriptRoot "../contracts/openapi.yaml"
if (!(Test-Path $contractPath)) {
    Write-Host "❌ OpenAPI contract not found at $contractPath" -ForegroundColor Red
    Write-Host "Please ensure the OpenAPI contract has been generated first." -ForegroundColor Yellow
    exit 1
}

# Check if openapi-typescript is installed
$frontendPath = Join-Path $PSScriptRoot "../frontend"
Set-Location $frontendPath

if (!(Test-Path "node_modules/.bin/openapi-typescript")) {
    Write-Host "📦 Installing openapi-typescript..." -ForegroundColor Yellow
    npm install --save-dev openapi-typescript
}

# Generate types
Write-Host "🔧 Generating types..." -ForegroundColor Green

try {
    # Create contracts directory structure
    $contractsPath = Join-Path $PSScriptRoot "../contracts"
    $typesPath = Join-Path $contractsPath "types"
    if (!(Test-Path $typesPath)) {
        New-Item -ItemType Directory -Path $typesPath -Force
    }

    # Generate TypeScript types from local OpenAPI spec
    $outputPath = Join-Path $typesPath "api.ts"
    
    npx openapi-typescript $contractPath --output $outputPath
    
    Write-Host "✅ TypeScript types generated successfully!" -ForegroundColor Green
    Write-Host "📁 Types available at: $outputPath" -ForegroundColor Cyan
    
    # Show file size for verification
    $fileSize = (Get-Item $outputPath).Length
    Write-Host "📊 Generated file size: $([math]::Round($fileSize/1KB, 2)) KB" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Failed to generate types: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Optional: Run TypeScript check on generated types
try {
    Write-Host "🔍 Validating generated types..." -ForegroundColor Blue
    npx tsc --noEmit --skipLibCheck $outputPath
    Write-Host "✅ Generated types are valid!" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Warning: Generated types have TypeScript issues" -ForegroundColor Yellow
    Write-Host "This is usually not a problem and types should still work" -ForegroundColor Yellow
}

Write-Host "🎉 Type generation completed!" -ForegroundColor Green