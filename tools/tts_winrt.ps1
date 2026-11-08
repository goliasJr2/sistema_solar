# =============================================================================
# tools/tts_winrt.ps1 — Sintetiza falas para .wav com as vozes do Windows (WinRT).
# Chamado por tools/gerar_vozes.py; não precisa de ser usado diretamente.
#
# Usa Windows.Media.SpeechSynthesis (vozes "OneCore"), que inclui vozes de
# português que a API clássica (System.Speech) não mostra, como a
# "Microsoft Helia" (pt-PT).
#
# Entrada: ficheiro JSON com uma lista de tarefas
#   [{"out": "caminho.wav", "voice": "Helia", "ssml": "<speak ...>...</speak>"}, ...]
# =============================================================================
param([Parameter(Mandatory = $true)][string]$Jobs)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows.Media.SpeechSynthesis, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.DataReader, Windows.Storage.Streams, ContentType = WindowsRuntime]

$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, [Type]$type) {
    $task = $asTask.MakeGenericMethod($type).Invoke($null, @($op))
    $task.Wait() | Out-Null
    $task.Result
}

$voices = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices
$synth = New-Object Windows.Media.SpeechSynthesis.SpeechSynthesizer
$list = Get-Content -Raw -Encoding UTF8 $Jobs | ConvertFrom-Json

foreach ($job in $list) {
    $voice = $voices | Where-Object { $_.DisplayName -like "*$($job.voice)*" } | Select-Object -First 1
    if (-not $voice) { Write-Output "ERRO voz não encontrada: $($job.voice)"; continue }
    $synth.Voice = $voice
    $stream = Await ($synth.SynthesizeSsmlToStreamAsync($job.ssml)) ([Windows.Media.SpeechSynthesis.SpeechSynthesisStream])
    $reader = New-Object Windows.Storage.Streams.DataReader($stream.GetInputStreamAt(0))
    $n = Await ($reader.LoadAsync([uint32]$stream.Size)) ([uint32])
    $bytes = New-Object byte[] $n
    $reader.ReadBytes($bytes)
    [IO.File]::WriteAllBytes($job.out, $bytes)
    Write-Output "OK $($job.out)"
}
