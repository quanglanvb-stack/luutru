$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Source = Join-Path $Root "Bieu_Cat_Tao_Marker_Opitex.py"
$BuildBat = Join-Path $Root "BUILD_EXE_CORE.bat"
$Exe = Join-Path $Root "dist\Bieu_Cat_Tao_Marker_Opitex.exe"
$ConfigDest = Join-Path $Root "NOI_PHAT_HANH.txt"
$Url = "https://update.quanglan.io.vn/update/cutting/Bieu_Cat_Tao_Marker_Opitex.exe"

function Show-Error([string]$Message) {
    [System.Windows.Forms.MessageBox]::Show(
        $Message,
        "QUANGLAN - Lỗi",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
    ) | Out-Null
    exit 1
}

function Read-VersionFromSource {
    $txt = [System.IO.File]::ReadAllText($Source)
    $m = [regex]::Match($txt, 'APP_VERSION\s*=\s*["'']([^"'']+)["'']')
    if (-not $m.Success) { Show-Error "Không tìm thấy APP_VERSION." }
    return $m.Groups[1].Value.Trim()
}

function Get-SuggestedVersion([string]$Version) {
    $m = [regex]::Match($Version, '^(\d+)\.(\d+)\.(\d+)$')
    if ($m.Success) {
        return ($m.Groups[1].Value + "." + $m.Groups[2].Value + "." + ([int]$m.Groups[3].Value + 1))
    }
    return $Version
}

function Set-Version([string]$Version) {
    $txt = [System.IO.File]::ReadAllText($Source)
    $txt = [regex]::Replace(
        $txt,
        'APP_VERSION\s*=\s*["''][^"'']+["'']',
        ('APP_VERSION = "' + $Version + '"'),
        1
    )
    [System.IO.File]::WriteAllText($Source,$txt,(New-Object System.Text.UTF8Encoding($true)))

    $Iss = Join-Path $Root "BIEU_CAT_TAO_MARKER_OPITEX_SETUP.iss"
    if(Test-Path $Iss) {
        $itxt = [System.IO.File]::ReadAllText($Iss)
        $itxt = [regex]::Replace(
            $itxt,
            '#define\s+MyAppVersion\s+"[^"]+"',
            ('#define MyAppVersion "' + $Version + '"'),
            1
        )
        [System.IO.File]::WriteAllText($Iss,$itxt,(New-Object System.Text.UTF8Encoding($true)))
    }
}

function Load-Dest {
    $default = "D:\2025\web\update\cutting"
    if(Test-Path $ConfigDest) {
        try {
            $saved = ([System.IO.File]::ReadAllText($ConfigDest)).Trim()
            if($saved) { return $saved }
        } catch {}
    }
    return $default
}

$current = Read-VersionFromSource
$suggested = Get-SuggestedVersion $current
$lastDest = Load-Dest

$form = New-Object System.Windows.Forms.Form
$form.Text = "QUANGLAN - Tạo bản cập nhật V3"
$form.StartPosition = "CenterScreen"
$form.Size = New-Object System.Drawing.Size(720,330)
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.Font = New-Object System.Drawing.Font("Segoe UI",10)

$title = New-Object System.Windows.Forms.Label
$title.Text = "Bieu Cat_Tao Marker Opitex - BUILD & PHÁT HÀNH"
$title.Font = New-Object System.Drawing.Font("Segoe UI",14,[System.Drawing.FontStyle]::Bold)
$title.AutoSize = $true
$title.Location = New-Object System.Drawing.Point(22,18)
$form.Controls.Add($title)

$sub = New-Object System.Windows.Forms.Label
$sub.Text = "Python 3.15  |  QUANGLAN SOFTWARE"
$sub.ForeColor = [System.Drawing.Color]::DimGray
$sub.AutoSize = $true
$sub.Location = New-Object System.Drawing.Point(25,52)
$form.Controls.Add($sub)

$l1 = New-Object System.Windows.Forms.Label
$l1.Text = "Version hiện tại:"
$l1.AutoSize = $true
$l1.Location = New-Object System.Drawing.Point(25,92)
$form.Controls.Add($l1)

$cbox = New-Object System.Windows.Forms.TextBox
$cbox.Text = $current
$cbox.ReadOnly = $true
$cbox.Location = New-Object System.Drawing.Point(160,88)
$cbox.Size = New-Object System.Drawing.Size(160,28)
$form.Controls.Add($cbox)

$l2 = New-Object System.Windows.Forms.Label
$l2.Text = "Version mới:"
$l2.AutoSize = $true
$l2.Location = New-Object System.Drawing.Point(25,132)
$form.Controls.Add($l2)

$vbox = New-Object System.Windows.Forms.TextBox
$vbox.Text = $suggested
$vbox.Location = New-Object System.Drawing.Point(160,128)
$vbox.Size = New-Object System.Drawing.Size(160,28)
$form.Controls.Add($vbox)

$sug = New-Object System.Windows.Forms.Label
$sug.Text = "Đề xuất: $suggested"
$sug.ForeColor = [System.Drawing.Color]::SeaGreen
$sug.AutoSize = $true
$sug.Location = New-Object System.Drawing.Point(335,132)
$form.Controls.Add($sug)

$l3 = New-Object System.Windows.Forms.Label
$l3.Text = "Nơi phát hành:"
$l3.AutoSize = $true
$l3.Location = New-Object System.Drawing.Point(25,176)
$form.Controls.Add($l3)

$dbox = New-Object System.Windows.Forms.TextBox
$dbox.Text = $lastDest
$dbox.Location = New-Object System.Drawing.Point(160,172)
$dbox.Size = New-Object System.Drawing.Size(420,28)
$form.Controls.Add($dbox)

$browse = New-Object System.Windows.Forms.Button
$browse.Text = "CHỌN..."
$browse.Location = New-Object System.Drawing.Point(590,170)
$browse.Size = New-Object System.Drawing.Size(90,32)
$browse.Add_Click({
    $dlg = New-Object System.Windows.Forms.FolderBrowserDialog
    $dlg.Description = "Chọn thư mục phát hành EXE + version.json"
    if(Test-Path $dbox.Text){ $dlg.SelectedPath = $dbox.Text }
    if($dlg.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK){
        $dbox.Text = $dlg.SelectedPath
    }
})
$form.Controls.Add($browse)

$hint = New-Object System.Windows.Forms.Label
$hint.Text = "Tự nhớ đường dẫn lần trước. Có thể bấm CHỌN... để đổi."
$hint.ForeColor = [System.Drawing.Color]::DimGray
$hint.AutoSize = $true
$hint.Location = New-Object System.Drawing.Point(160,205)
$form.Controls.Add($hint)

$ok = New-Object System.Windows.Forms.Button
$ok.Text = "BUILD & PHÁT HÀNH"
$ok.Font = New-Object System.Drawing.Font("Segoe UI",10,[System.Drawing.FontStyle]::Bold)
$ok.Location = New-Object System.Drawing.Point(400,240)
$ok.Size = New-Object System.Drawing.Size(180,40)
$ok.Add_Click({
    $v = $vbox.Text.Trim()
    $d = $dbox.Text.Trim().Trim('"')

    if($v -notmatch '^\d+\.\d+\.\d+([.-][A-Za-z0-9]+)?$'){
        [System.Windows.Forms.MessageBox]::Show("Version không đúng. Ví dụ: 3.0.1") | Out-Null
        return
    }
    if(-not $d){
        [System.Windows.Forms.MessageBox]::Show("Chưa chọn nơi phát hành.") | Out-Null
        return
    }
    $form.Tag = [pscustomobject]@{Version=$v;Destination=$d}
    $form.DialogResult = [System.Windows.Forms.DialogResult]::OK
    $form.Close()
})
$form.Controls.Add($ok)

$cancel = New-Object System.Windows.Forms.Button
$cancel.Text = "HỦY"
$cancel.Location = New-Object System.Drawing.Point(590,240)
$cancel.Size = New-Object System.Drawing.Size(90,40)
$cancel.Add_Click({$form.DialogResult=[System.Windows.Forms.DialogResult]::Cancel;$form.Close()})
$form.Controls.Add($cancel)

$form.AcceptButton = $ok
$form.CancelButton = $cancel

if($form.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK){ exit 0 }

$Version = [string]$form.Tag.Version
$Dest = [string]$form.Tag.Destination

New-Item -ItemType Directory -Path $Dest -Force | Out-Null
[System.IO.File]::WriteAllText($ConfigDest,$Dest,(New-Object System.Text.UTF8Encoding($false)))
Set-Version $Version

$progress = New-Object System.Windows.Forms.Form
$progress.Text = "QUANGLAN - Đang build V$Version"
$progress.StartPosition = "CenterScreen"
$progress.Size = New-Object System.Drawing.Size(560,180)
$progress.FormBorderStyle = "FixedDialog"
$progress.ControlBox = $false

$status = New-Object System.Windows.Forms.Label
$status.Text = "Đang BUILD EXE bằng Python 3.15..."
$status.TextAlign = "MiddleCenter"
$status.Location = New-Object System.Drawing.Point(20,25)
$status.Size = New-Object System.Drawing.Size(500,45)
$progress.Controls.Add($status)

$bar = New-Object System.Windows.Forms.ProgressBar
$bar.Style = "Marquee"
$bar.MarqueeAnimationSpeed = 25
$bar.Location = New-Object System.Drawing.Point(35,82)
$bar.Size = New-Object System.Drawing.Size(470,24)
$progress.Controls.Add($bar)

$progress.Show()
[System.Windows.Forms.Application]::DoEvents()

try {
    $BuildOut = Join-Path $Root "BUILD_STDOUT.txt"
    $BuildErr = Join-Path $Root "BUILD_STDERR.txt"
    $BuildLog = Join-Path $Root "BUILD_LOG.txt"

    foreach($f in @($BuildOut,$BuildErr,$BuildLog)){
        Remove-Item -Force $f -ErrorAction SilentlyContinue
    }

    $proc = Start-Process -FilePath "cmd.exe" `
        -ArgumentList @("/d","/c","call BUILD_EXE_CORE.bat") `
        -WorkingDirectory $Root `
        -RedirectStandardOutput $BuildOut `
        -RedirectStandardError $BuildErr `
        -Wait -PassThru -WindowStyle Hidden

    try {
        $all = @()
        if(Test-Path $BuildOut){$all += Get-Content $BuildOut}
        if(Test-Path $BuildErr){$all += Get-Content $BuildErr}
        $all | Set-Content $BuildLog -Encoding UTF8
    } catch {}

    if($proc.ExitCode -ne 0){
        $tail = ""
        if(Test-Path $BuildLog){
            $tail = ((Get-Content $BuildLog -Tail 30) -join "`r`n")
        }
        throw "BUILD EXE thất bại. Mã lỗi=$($proc.ExitCode)`r`n`r`n$tail"
    }

    if(-not (Test-Path $Exe)){ throw "Không tìm thấy EXE sau khi build." }

    $status.Text = "Đang tạo SHA256 + version.json..."
    [System.Windows.Forms.Application]::DoEvents()

    $Hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Exe).Hash.ToLower()
    $obj = [ordered]@{
        version = $Version
        download_url = $Url
        sha256 = $Hash
        required = $false
        notes = "Bieu Cat_Tao Marker Opitex V$Version"
    }
    $VersionFile = Join-Path $Root "version.json"
    [System.IO.File]::WriteAllText(
        $VersionFile,
        ($obj | ConvertTo-Json -Depth 4),
        (New-Object System.Text.UTF8Encoding($false))
    )

    $status.Text = "Đang backup bản cũ và phát hành..."
    [System.Windows.Forms.Application]::DoEvents()

    $DestExe = Join-Path $Dest "Bieu_Cat_Tao_Marker_Opitex.exe"
    $DestVersion = Join-Path $Dest "version.json"
    $Backup = Join-Path $Dest ("BACKUP_" + (Get-Date -Format "yyyyMMdd_HHmmss"))

    if((Test-Path $DestExe) -or (Test-Path $DestVersion)){
        New-Item -ItemType Directory -Path $Backup -Force | Out-Null
        if(Test-Path $DestExe){Copy-Item $DestExe (Join-Path $Backup "Bieu_Cat_Tao_Marker_Opitex.exe") -Force}
        if(Test-Path $DestVersion){Copy-Item $DestVersion (Join-Path $Backup "version.json") -Force}
    }

    Copy-Item $Exe $DestExe -Force
    Copy-Item $VersionFile $DestVersion -Force

    $progress.Close()
    [System.Windows.Forms.MessageBox]::Show(
        "PHÁT HÀNH THÀNH CÔNG!`n`nVersion: $Version`n`n$DestExe`n$DestVersion",
        "QUANGLAN - Thành công",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Information
    ) | Out-Null

    Start-Process explorer.exe $Dest
}
catch {
    try{$progress.Close()}catch{}
    Show-Error $_.Exception.Message
}
