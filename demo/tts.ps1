param(
    [Parameter(Mandatory=$true)][string]$TextFile,
    [Parameter(Mandatory=$true)][string]$OutputFile
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$demoVoice = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $english = $demoVoice.GetInstalledVoices() | Where-Object { $_.Enabled -and $_.VoiceInfo.Culture.Name -like 'en-*' } | Select-Object -First 1
    if (-not $english) { throw 'No local English SAPI voice installed. Use captions or manual narration.' }
    $demoVoice.SelectVoice($english.VoiceInfo.Name)
    $demoVoice.Rate = 0
    $demoVoice.SetOutputToWaveFile($OutputFile)
    $demoVoice.Speak([System.IO.File]::ReadAllText($TextFile))
    Write-Output $english.VoiceInfo.Name
} finally {
    $demoVoice.Dispose()
}
