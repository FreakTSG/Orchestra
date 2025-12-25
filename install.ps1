# Orchestra Installation Script for Windows
# This script installs the Orchestra multi-agent coding environment

Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                               ║" -ForegroundColor Cyan
Write-Host "║     🎻 Orchestra - Multi-Agent AI Coding Environment          ║" -ForegroundColor Cyan
Write-Host "║                                                               ║" -ForegroundColor Cyan
Write-Host "║     Installation Script                                       ║" -ForegroundColor Cyan
Write-Host "║                                                               ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "🔍 Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Found $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found! Please install Python 3.8+ first." -ForegroundColor Red
    Write-Host "   Download from: https://www.python.org/downloads/" -ForegroundColor White
    exit 1
}

# Check Python version
Write-Host "🔍 Checking Python version..." -ForegroundColor Yellow
$versionOutput = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$version = [version]$versionOutput
if ($version -lt [version]"3.8") {
    Write-Host "❌ Python 3.8+ required. Found: $version" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Python version: $version" -ForegroundColor Green

# Check if pip is available
Write-Host "🔍 Checking pip availability..." -ForegroundColor Yellow
try {
    $pipVersion = pip --version 2>&1
    Write-Host "✓ pip is available" -ForegroundColor Green
} catch {
    Write-Host "❌ pip not found!" -ForegroundColor Red
    exit 1
}

# Install/Upgrade pip
Write-Host ""
Write-Host "📦 Upgrading pip to latest version..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install Orchestra in editable mode
Write-Host ""
Write-Host "📦 Installing Orchestra..." -ForegroundColor Yellow
Write-Host "   This will install Orchestra and its dependencies:" -ForegroundColor White
Write-Host "   - rich (terminal UI)" -ForegroundColor White
Write-Host "   - questionary (interactive prompts)" -ForegroundColor White
Write-Host "   - aiohttp (async HTTP)" -ForegroundColor White
Write-Host "   - python-dotenv (environment variables)" -ForegroundColor White
Write-Host ""

python -m pip install -e .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Installation failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Orchestra installed successfully!" -ForegroundColor Green

# Verify installation
Write-Host ""
Write-Host "🔍 Verifying installation..." -ForegroundColor Yellow
try {
    $orchestraHelp = orchestra --help 2>&1
    if ($?) {
        Write-Host "✓ 'orchestra' command is available!" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  'orchestra' command not found in PATH" -ForegroundColor Yellow
    Write-Host "   You may need to restart your terminal or add Python Scripts to PATH" -ForegroundColor White
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                                                               ║" -ForegroundColor Green
Write-Host "║     ✅ Installation Complete!                                  ║" -ForegroundColor Green
Write-Host "║                                                               ║" -ForegroundColor Green
Write-Host "║     Start using Orchestra:                                    ║" -ForegroundColor Green
Write-Host "║                                                               ║" -ForegroundColor Green
Write-Host "║     orchestra                                                 ║" -ForegroundColor Green
Write-Host "║                                                               ║" -ForegroundColor Green
Write-Host "║     Or from PowerShell:                                       ║" -ForegroundColor Green
Write-Host "║     python -m orchestra                                       ║" -ForegroundColor Green
Write-Host "║                                                               ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

# Check for AI CLI tools
Write-Host "🤖 Checking for AI CLI tools..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Orchestra works best with these AI CLI tools installed:" -ForegroundColor White
Write-Host ""

$tools = @(
    @{Name="Claude CLI"; Command="claude"; Install="irm https://claude.ai/install.ps1 | iex"},
    @{Name="Gemini CLI"; Command="gemini"; Install="npm install -g @google/gemini-cli"},
    @{Name="OpenAI Codex"; Command="codex"; Install="npm install -g @openai/codex"}
)

$installedCount = 0

foreach ($tool in $tools) {
    try {
        $null = Get-Command $tool.Command -ErrorAction Stop
        Write-Host "  ✓ $($tool.Name) - Installed" -ForegroundColor Green
        $installedCount++
    } catch {
        Write-Host "  ✗ $($tool.Name) - Not found" -ForegroundColor Red
        Write-Host "    Install: $($tool.Install)" -ForegroundColor Gray
    }
}

Write-Host ""
if ($installedCount -eq 0) {
    Write-Host "⚠️  No AI CLI tools detected. Orchestra will work, but won't have any agents." -ForegroundColor Yellow
    Write-Host "   Install at least one AI CLI tool for full functionality." -ForegroundColor Yellow
} else {
    Write-Host "✓ Detected $installedCount AI CLI tool(s)" -ForegroundColor Green
}

Write-Host ""
Write-Host "📚 For more information, visit: https://github.com/your-username/orchestra" -ForegroundColor Cyan
Write-Host ""
