# PowerShell script to generate all Mermaid diagrams
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  Generating All Mermaid Diagrams  " -ForegroundColor Cyan
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
    
    Write-Host "[$num/$total] Generating $file..." -ForegroundColor Yellow
    
    $result = & mmdc -i "$file.mmd" -o "$file.png" -b transparent 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Success: $file.png created" -ForegroundColor Green
        $success++
    } else {
        Write-Host "   ✗ Failed: $file.mmd" -ForegroundColor Red
        Write-Host "   Error: $result" -ForegroundColor Red
        $failed++
    }
    Write-Host ""
}

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  Generation Complete!              " -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "  ✓ Success: $success" -ForegroundColor Green
Write-Host "  ✗ Failed:  $failed" -ForegroundColor Red
Write-Host "  Total:     $total" -ForegroundColor Cyan
Write-Host ""

if ($success -gt 0) {
    Write-Host "Check the docs/images/ folder for PNG files." -ForegroundColor Green
}

if ($failed -gt 0) {
    Write-Host "Some files failed to generate. Check errors above." -ForegroundColor Red
}
