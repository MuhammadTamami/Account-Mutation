# PowerShell script to generate all Mermaid diagrams as SVG (scalable)
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  Generating All SVG Diagrams       " -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

$files = @(
    "version-timeline",
    "bank-accuracy-chart",
    "architecture-diagram",
    "feature-comparison",
    "processing-modes",
    "statistics-dashboard",
    "user-workflow"
)

$total = $files.Count
$success = 0
$failed = 0

for ($i = 0; $i -lt $total; $i++) {
    $file = $files[$i]
    $num = $i + 1
    
    Write-Host "[$num/$total] Generating $file.svg..." -ForegroundColor Yellow
    
    $result = & mmdc -i "$file.mmd" -o "$file.svg" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Success: $file.svg created" -ForegroundColor Green
        $success++
    } else {
        Write-Host "   ✗ Failed: $file.mmd" -ForegroundColor Red
        Write-Host "   Error: $result" -ForegroundColor Red
        $failed++
    }
    Write-Host ""
}

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  SVG Generation Complete!          " -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "  ✓ Success: $success" -ForegroundColor Green
Write-Host "  ✗ Failed:  $failed" -ForegroundColor Red
Write-Host "  Total:     $total" -ForegroundColor Cyan
Write-Host ""

Write-Host "Note: SVG files are scalable and can be used in any size without quality loss." -ForegroundColor Cyan
