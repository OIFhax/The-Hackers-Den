<#
.SYNOPSIS
    PowerShell script to clone macOS Security repositories and generate CIS baseline, guidance, and compliance scripts.

.DESCRIPTION
    This script performs the following operations:
    1. Checks for and installs required dependencies (Git and Python)
    2. Cleans up existing repository directories
    3. Clones the macOS Security repository (Sequoia branch) and its wiki
    4. Generates baseline, guidance, and compliance files for all CIS levels

.NOTES
    Author: Script Generator
    Date: $(Get-Date -Format "yyyy-MM-dd")
    Requirements: PowerShell 5.1+, Internet connection, Administrator privileges for installing dependencies
#>

# Script configuration
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"  # Speeds up web requests
$LogFile = "macos_security_setup.log"
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Repository information
$RepoUrl = "https://github.com/usnistgov/macos_security.git"
$WikiUrl = "https://github.com/usnistgov/macos_security.wiki.git"
$RepoBranch = "sequoia"
$RepoDir = "macos_security-sequoia"
$WikiDir = "macos_security.wiki"

# CIS levels to process
$CisLevels = @{
    "cis_lvl1.yaml" = "CIS Level 1"
    "cis_lvl2.yaml" = "CIS Level 2"
}

# Logging function
function Write-Log {
    param (
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    
    # Write to console with color based on level
    switch ($Level) {
        "ERROR" { Write-Host $LogEntry -ForegroundColor Red }
        "WARNING" { Write-Host $LogEntry -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $LogEntry -ForegroundColor Green }
        default { Write-Host $LogEntry }
    }
    
    # Append to log file
    Add-Content -Path $LogFile -Value $LogEntry
}

# Function to check if a command exists
function Test-CommandExists {
    param (
        [string]$Command
    )
    
    $exists = $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
    return $exists
}

# Function to check and install dependencies
function Check-Dependencies {
    Write-Log "Checking dependencies..."
    
    # Check Git
    if (-not (Test-CommandExists "git")) {
        Write-Log "Git is not installed. Installing Git..." "WARNING"
        try {
            # Try using winget first
            if (Test-CommandExists "winget") {
                Write-Log "Installing Git using winget..."
                winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
            }
            # Fall back to chocolatey if available
            elseif (Test-CommandExists "choco") {
                Write-Log "Installing Git using Chocolatey..."
                choco install git -y
            }
            else {
                throw "No package manager found to install Git. Please install Git manually."
            }
            
            # Refresh environment variables
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            
            if (-not (Test-CommandExists "git")) {
                throw "Git installation failed. Please install Git manually."
            }
            
            Write-Log "Git installed successfully." "SUCCESS"
        }
        catch {
            Write-Log "Failed to install Git`: $_" "ERROR"
            throw "Git installation failed`: $_"
        }
    }
    else {
        Write-Log "Git is already installed."
    }
    
    # Check Python 3
    $pythonInstalled = $false
    $python3Commands = @("python3", "py -3", "python")
    $pythonCommand = ""
    
    foreach ($cmd in $python3Commands) {
        try {
            $version = Invoke-Expression "$cmd --version 2>&1"
            if ($version -match "Python 3") {
                $pythonInstalled = $true
                $pythonCommand = $cmd
                Write-Log "Python 3 found: $version using command: $cmd"
                break
            }
        }
        catch {
            # Command failed, try next one
            continue
        }
    }
    
    if (-not $pythonInstalled) {
        Write-Log "Python 3 is not installed. Installing Python 3..." "WARNING"
        try {
            # Try using winget first
            if (Test-CommandExists "winget") {
                Write-Log "Installing Python 3 using winget..."
                winget install --id Python.Python.3 -e --accept-source-agreements --accept-package-agreements
            }
            # Fall back to chocolatey if available
            elseif (Test-CommandExists "choco") {
                Write-Log "Installing Python 3 using Chocolatey..."
                choco install python3 -y
            }
            else {
                throw "No package manager found to install Python 3. Please install Python 3 manually."
            }
            
            # Refresh environment variables
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            
            # Check if Python 3 is now installed
            foreach ($cmd in $python3Commands) {
                try {
                    $version = Invoke-Expression "$cmd --version 2>&1"
                    if ($version -match "Python 3") {
                        $pythonInstalled = $true
                        $pythonCommand = $cmd
                        Write-Log "Python 3 installed successfully: $version using command: $cmd" "SUCCESS"
                        break
                    }
                }
                catch {
                    # Command failed, try next one
                    continue
                }
            }
            
            if (-not $pythonInstalled) {
                throw "Python 3 installation failed. Please install Python 3 manually."
            }
        }
        catch {
            Write-Log "Failed to install Python 3`: $_" "ERROR"
            throw "Python 3 installation failed`: $_"
        }
    }
    else {
        Write-Log "Python 3 is already installed: $($version)"
    }
    
    # Store the Python command for later use
    if ($pythonCommand -eq "py -3") {
        $global:PythonCmd = "py"
        $global:PythonArgs = "-3"
    } else {
        $global:PythonCmd = $pythonCommand
        $global:PythonArgs = ""
    }
    
    Write-Log "All dependencies are satisfied." "SUCCESS"
}

# Function to clean up existing directories
function Clean-Directories {
    Write-Log "Cleaning up existing directories..."
    
    # Check and remove repository directory
    if (Test-Path $RepoDir) {
        Write-Log "Removing existing repository directory: $RepoDir" "WARNING"
        try {
            Remove-Item -Path $RepoDir -Recurse -Force
            Write-Log "Repository directory removed successfully."
        }
        catch {
            Write-Log "Failed to remove repository directory`: $_" "ERROR"
            throw "Failed to remove repository directory`: $_"
        }
    }
    
    # Check and remove wiki directory
    if (Test-Path $WikiDir) {
        Write-Log "Removing existing wiki directory: $WikiDir" "WARNING"
        try {
            Remove-Item -Path $WikiDir -Recurse -Force
            Write-Log "Wiki directory removed successfully."
        }
        catch {
            Write-Log "Failed to remove wiki directory`: $_" "ERROR"
            throw "Failed to remove wiki directory`: $_"
        }
    }
    
    Write-Log "Directory cleanup completed." "SUCCESS"
}

# Function to clone repositories
function Clone-Repositories {
    Write-Log "Cloning repositories..."
    
    # Clone main repository (Sequoia branch)
    try {
        Write-Log "Cloning main repository (branch: $RepoBranch)..."
        git clone -b $RepoBranch $RepoUrl $RepoDir
        if (-not $?) { throw "Git clone failed with exit code $LASTEXITCODE" }
        Write-Log "Main repository cloned successfully." "SUCCESS"
    }
    catch {
        Write-Log "Failed to clone main repository`: $_" "ERROR"
        throw "Failed to clone main repository`: $_"
    }
    
    # Clone wiki repository
    try {
        Write-Log "Cloning wiki repository..."
        git clone $WikiUrl $WikiDir
        if (-not $?) { throw "Git clone failed with exit code $LASTEXITCODE" }
        Write-Log "Wiki repository cloned successfully." "SUCCESS"
    }
    catch {
        Write-Log "Failed to clone wiki repository`: $_" "ERROR"
        throw "Failed to clone wiki repository`: $_"
    }
    
    Write-Log "All repositories cloned successfully." "SUCCESS"
}

# Function to install Python dependencies
function Install-PythonDependencies {
    Write-Log "Installing required Python packages..."
    
    try {
        # Change to repository directory
        Push-Location $RepoDir
        
        # Install required packages
        Write-Log "Installing PyYAML package..."
        if ($global:PythonArgs) {
            & $global:PythonCmd $global:PythonArgs -m pip install pyyaml
        } else {
            & $global:PythonCmd -m pip install pyyaml
        }
        if (-not $?) { throw "Failed to install PyYAML package with exit code $LASTEXITCODE" }
        
        # Check if requirements.txt exists and install dependencies
        if (Test-Path "requirements.txt") {
            Write-Log "Installing dependencies from requirements.txt..."
            if ($global:PythonArgs) {
                & $global:PythonCmd $global:PythonArgs -m pip install -r requirements.txt
            } else {
                & $global:PythonCmd -m pip install -r requirements.txt
            }
            if (-not $?) { throw "Failed to install dependencies from requirements.txt with exit code $LASTEXITCODE" }
        }
        
        Write-Log "Python dependencies installed successfully." "SUCCESS"
    }
    catch {
        Write-Log "Failed to install Python dependencies`: $_" "ERROR"
        throw "Failed to install Python dependencies`: $_"
    }
    finally {
        # Return to original directory
        Pop-Location
    }
}

# Function to generate security files
function Generate-SecurityFiles {
    Write-Log "Generating security files..."
    
    # Change to repository directory
    try {
        Push-Location $RepoDir
        Write-Log "Changed to repository directory: $RepoDir"
        
        # Set environment variables for Python encoding
        $env:PYTHONIOENCODING = "utf-8"
        $env:PYTHONUTF8 = "1"
        Write-Log "Set Python encoding environment variables to handle encoding issues."
        
        # Process each CIS level
        foreach ($yamlFile in $CisLevels.Keys) {
            $description = $CisLevels[$yamlFile]
            $baselinePath = "baselines/$yamlFile"
            Write-Log "Processing $description ($yamlFile)..."
            
            try {
                # Generate guidance and compliance scripts
                Write-Log "Generating guidance and compliance scripts for $description..."
                
                # Copy the wrapper script to the repository directory if it doesn't exist
                if (-not (Test-Path "generate_wrapper.py")) {
                    Copy-Item -Path "../generate_wrapper.py" -Destination "generate_wrapper.py" -Force
                    Write-Log "Copied generate_wrapper.py to the repository directory."
                }
                
                if ($global:PythonArgs) {
                    & $global:PythonCmd $global:PythonArgs generate_wrapper.py -p -s -x $baselinePath
                } else {
                    & $global:PythonCmd generate_wrapper.py -p -s -x $baselinePath
                }
                
                # Check if the build directory exists and contains the expected files
                $buildDir = "build/$($yamlFile -replace '\.yaml$', '')"
                if (Test-Path $buildDir) {
                    $complianceScript = Join-Path $buildDir "$($yamlFile -replace '\.yaml$', '')_compliance.sh"
                    $adocFile = Join-Path $buildDir "$($yamlFile -replace '\.yaml$', '').adoc"
                    $xlsFile = Join-Path $buildDir "$($yamlFile -replace '\.yaml$', '').xls"
                    
                    if ((Test-Path $complianceScript) -and (Test-Path $adocFile) -and (Test-Path $xlsFile)) {
                        Write-Log "Successfully generated all files for $description." "SUCCESS"
                        Write-Log "Note: The asciidoctor error can be ignored. The .adoc files have been generated successfully." "INFO"
                    } else {
                        throw "Some expected files were not generated for $description"
                    }
                } else {
                    throw "Build directory not found for $description"
                }
            }
            catch {
                Write-Log "Failed to generate files for $description`: $_" "ERROR"
                # Continue with next CIS level instead of stopping completely
                continue
            }
        }
        
        # Check if build directory exists and contains files
        if (Test-Path "build") {
            $outputFiles = Get-ChildItem -Path "build" -Recurse | Measure-Object
            Write-Log "Generated $($outputFiles.Count) files in the build directory." "SUCCESS"
        }
        else {
            Write-Log "Build directory not found. File generation may have failed." "WARNING"
        }
    }
    catch {
        Write-Log "Error during file generation`: $_" "ERROR"
        throw "Error during file generation`: $_"
    }
    finally {
        # Return to original directory
        Pop-Location
        Write-Log "Returned to original directory."
    }
}

# Main script execution
try {
    Write-Log "=== macOS Security Setup Script Started ===" "INFO"
    
    # Check and install dependencies
    Check-Dependencies
    
    # Clean up existing directories
    Clean-Directories
    
    # Clone repositories
    Clone-Repositories
    
    # Install Python dependencies
    Install-PythonDependencies
    
    # Generate security files
    Generate-SecurityFiles
    
    # Final success message
    Write-Log "=== macOS Security Setup Script Completed Successfully ===" "SUCCESS"
    Write-Log "Generated files are located in the '$RepoDir/build' directory." "SUCCESS"
}
catch {
    Write-Log "=== Script execution failed`: $_ ===" "ERROR"
    exit 1
}
