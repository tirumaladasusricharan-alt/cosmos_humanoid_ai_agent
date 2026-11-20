$ErrorActionPreference = "Stop"
$env:COSMOS_STRICT_RAM_ONLY = "1"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  COSMOS Dual-Engine | Strict RAM-Only Mode " -ForegroundColor Cyan
Write-Host "  Creator: Sri Charan Tirumaladasu          " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# --- Nuance API Key (nk_) ---
if (-not $env:NUANCE_API_KEY) {
    $secNuance = Read-Host "Enter rotated NUANCE_API_KEY (nk_...)" -AsSecureString
    $env:NUANCE_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secNuance)
    )
}

# --- Groq API Key (gsk_) ---
if (-not $env:GROQ_API_KEY) {
    $secGroq = Read-Host "Enter GROQ_API_KEY (gsk_...)" -AsSecureString
    $env:GROQ_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secGroq)
    )
}

# --- Model defaults ---
if (-not $env:COSMOS_GROQ_MODEL) { $env:COSMOS_GROQ_MODEL = "openai/gpt-oss-120b" }
if (-not $env:COSMOS_OLLAMA_MODEL) { $env:COSMOS_OLLAMA_MODEL = "llama3.1:8b" }

Write-Host ""
Write-Host "[COSMOS] Nuance key set: $( if ($env:NUANCE_API_KEY) { 'YES (nk_...)' } else { 'NO' } )" -ForegroundColor Green
Write-Host "[COSMOS] Groq key set:   $( if ($env:GROQ_API_KEY) { 'YES (gsk_...)' } else { 'NO' } )" -ForegroundColor Green
Write-Host "[COSMOS] Groq model:     $env:COSMOS_GROQ_MODEL" -ForegroundColor Green
Write-Host "[COSMOS] Ollama model:   $env:COSMOS_OLLAMA_MODEL" -ForegroundColor Green
Write-Host ""
Write-Host "[COSMOS] Starting Dual-Engine Bridge in strict RAM-only mode on http://127.0.0.1:8000 ..." -ForegroundColor Yellow
Write-Host ""

Set-Location -Path $PSScriptRoot\Jarvis_Setup_Package
uvicorn cosmos_nuance_bridge:app --host 127.0.0.1 --port 8000 --reload
