# Test all examples and record results
# Usage: .\scripts\test_examples.ps1

$results = @()
$workingDir = "c:\ushak-projects\ToolWeaver"

# Get all example folders
$examples = Get-ChildItem -Path "$workingDir\examples" -Directory | 
Where-Object { $_.Name -match '^\d' } | 
Sort-Object Name

foreach ($example in $examples) {
    $exampleNum = $example.Name.Split('-')[0]
    $pythonFile = Get-ChildItem -Path $example.FullName -Filter "*.py" -File | 
    Where-Object { $_.Name -ne '__init__.py' -and $_.Name -ne 'conftest.py' } |
    Select-Object -First 1
    
    if (!$pythonFile) {
        $results += [PSCustomObject]@{
            Number = $exampleNum
            Name   = $example.Name
            Status = "SKIP"
            Error  = "No Python file found"
        }
        continue
    }
    
    Write-Host "`n=== Testing $($example.Name) ===" -ForegroundColor Cyan
    Write-Host "File: $($pythonFile.Name)"
    
    try {
        $output = & python "$($pythonFile.FullName)" 2>&1 | Select-Object -First 100 | Out-String
        
        if ($LASTEXITCODE -eq 0) {
            $results += [PSCustomObject]@{
                Number = $exampleNum
                Name   = $example.Name
                Status = "✅ PASS"
                Error  = ""
            }
            Write-Host "✅ PASS" -ForegroundColor Green
        }
        else {
            # Check for common errors
            $errorType = switch -Regex ($output) {
                "ModuleNotFoundError" { "Missing module" }
                "ImportError" { "Import error" }
                "NameError" { "Name error" }
                "TypeError" { "Type error" }
                "AttributeError" { "Attribute error" }
                default { "Runtime error" }
            }
            
            $results += [PSCustomObject]@{
                Number = $exampleNum
                Name   = $example.Name
                Status = "❌ FAIL"
                Error  = $errorType
            }
            Write-Host "❌ FAIL: $errorType" -ForegroundColor Red
        }
    }
    catch {
        $results += [PSCustomObject]@{
            Number = $exampleNum
            Name   = $example.Name
            Status = "❌ ERROR"
            Error  = $_.Exception.Message
        }
        Write-Host "❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Summary
Write-Host "`n`n=== SUMMARY ===" -ForegroundColor Yellow
$results | Format-Table -AutoSize

$passCount = ($results | Where-Object { $_.Status -eq "✅ PASS" }).Count
$failCount = ($results | Where-Object { $_.Status -like "❌*" }).Count
$skipCount = ($results | Where-Object { $_.Status -eq "SKIP" }).Count
$total = $results.Count

Write-Host "`nResults: $passCount passed, $failCount failed, $skipCount skipped out of $total" -ForegroundColor Cyan
Write-Host "Pass rate: $([math]::Round($passCount * 100 / $total, 1))%`n"

# Save results
$results | Export-Csv -Path "$workingDir\docs\internal\examples_test_results.csv" -NoTypeInformation
Write-Host "Results saved to docs\internal\examples_test_results.csv"
