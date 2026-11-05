#define MyAppName "Biểu Cắt - Tạo Marker Optitex"
#define MyAppExeName "Bieu_Cat_Tao_Marker_Opitex.exe"
#define MyAppVersion "3.0.28"

[Setup]
AppId={{4D51F6D5-7A5A-4D7A-9EB3-7B2D24683E33}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} V{#MyAppVersion}
AppPublisher=QUANGLAN SOFTWARE
VersionInfoDescription=Trình cài đặt {#MyAppName}
VersionInfoProductName={#MyAppName}
DefaultDirName={localappdata}\Programs\BieuCatTaoMarkerOpitex
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist_setup
OutputBaseFilename=SETUP_Bieu_Cat_Tao_Marker_Opitex
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\QUANGLAN.ico
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupLogging=yes
SetupIconFile=QUANGLAN.ico
ShowLanguageDialog=no
MissingMessagesWarning=no
NotRecognizedMessagesWarning=no

[Languages]
Name: "vietnamese"; MessagesFile: "compiler:Default.isl"

[Messages]
vietnamese.SetupAppTitle=Cài đặt
vietnamese.SetupWindowTitle=Cài đặt - %1
vietnamese.UninstallAppTitle=Gỡ cài đặt
vietnamese.UninstallAppFullTitle=Gỡ cài đặt - %1
vietnamese.InformationTitle=Thông tin
vietnamese.ConfirmTitle=Xác nhận
vietnamese.ErrorTitle=Lỗi

vietnamese.ButtonBack=< &Trước
vietnamese.ButtonNext=T&iếp >
vietnamese.ButtonInstall=&Cài đặt
vietnamese.ButtonOK=OK
vietnamese.ButtonCancel=Hủy
vietnamese.ButtonYes=&Có
vietnamese.ButtonNo=&Không
vietnamese.ButtonFinish=&Hoàn thành
vietnamese.ButtonBrowse=&Duyệt...
vietnamese.ButtonWizardBrowse=D&uyệt...
vietnamese.ButtonNewFolder=Tạ&o thư mục mới

vietnamese.ClickNext=Nhấn Tiếp để tiếp tục, hoặc Hủy để thoát cài đặt.
vietnamese.BrowseDialogTitle=Chọn thư mục
vietnamese.BrowseDialogLabel=Chọn một thư mục trong danh sách bên dưới rồi nhấn OK.
vietnamese.NewFolderName=Thư mục mới

vietnamese.WelcomeLabel1=Chào mừng đến với trình cài đặt [name]
vietnamese.WelcomeLabel2=Chương trình sẽ cài đặt [name/ver] trên máy tính của bạn.%n%nBạn nên đóng các chương trình khác trước khi tiếp tục.

vietnamese.WizardSelectDir=Chọn vị trí cài đặt
vietnamese.SelectDirDesc=Bạn muốn cài [name] ở đâu?
vietnamese.SelectDirLabel3=[name] sẽ được cài vào thư mục sau:
vietnamese.SelectDirBrowseLabel=Nhấn Tiếp để tiếp tục. Nếu muốn chọn thư mục khác, nhấn Duyệt.

vietnamese.WizardReady=Sẵn sàng cài đặt
vietnamese.ReadyLabel1=Trình cài đặt đã sẵn sàng cài [name] trên máy tính của bạn.
vietnamese.ReadyLabel2a=Nhấn Cài đặt để tiếp tục, hoặc nhấn Trước để xem lại hoặc thay đổi thiết lập.
vietnamese.ReadyLabel2b=Nhấn Cài đặt để bắt đầu.
vietnamese.ReadyMemoDir=Thư mục cài đặt:
vietnamese.ReadyMemoGroup=Thư mục Menu Start:
vietnamese.ReadyMemoTasks=Tác vụ bổ sung:

vietnamese.WizardPreparing=Chuẩn bị cài đặt
vietnamese.PreparingDesc=[name] đang được chuẩn bị để cài đặt trên máy tính của bạn.
vietnamese.CannotContinue=Không thể tiếp tục cài đặt. Nhấn Hủy để thoát.

vietnamese.WizardInstalling=Đang cài đặt
vietnamese.InstallingLabel=Vui lòng chờ trong khi [name] đang được cài đặt trên máy tính của bạn.

vietnamese.FinishedHeadingLabel=Hoàn thành cài đặt [name]
vietnamese.FinishedLabelNoIcons=[name] đã được cài đặt thành công trên máy tính của bạn.
vietnamese.FinishedLabel=[name] đã được cài đặt thành công. Bạn có thể mở chương trình từ biểu tượng trên Desktop.
vietnamese.ClickFinish=Nhấn Hoàn thành để đóng trình cài đặt.

vietnamese.ExitSetupTitle=Thoát cài đặt
vietnamese.ExitSetupMessage=Cài đặt chưa hoàn thành. Nếu thoát bây giờ, chương trình sẽ không được cài đặt.%n%nBạn có chắc muốn thoát không?

vietnamese.SetupAppRunningError=Trình cài đặt phát hiện %1 đang chạy.%n%nHãy đóng chương trình rồi nhấn OK để tiếp tục, hoặc nhấn Hủy để thoát.
vietnamese.UninstallAppRunningError=Trình gỡ cài đặt phát hiện %1 đang chạy.%n%nHãy đóng chương trình rồi nhấn OK để tiếp tục, hoặc nhấn Hủy để thoát.

vietnamese.DirExistsTitle=Thư mục đã tồn tại
vietnamese.DirExists=Thư mục:%n%n%1%n%nđã tồn tại. Bạn có muốn tiếp tục cài đặt vào thư mục này không?
vietnamese.DirDoesntExistTitle=Thư mục chưa tồn tại
vietnamese.DirDoesntExist=Thư mục:%n%n%1%n%nchưa tồn tại. Bạn có muốn tạo thư mục này không?
vietnamese.DiskSpaceWarningTitle=Không đủ dung lượng ổ đĩa

vietnamese.StatusClosingApplications=Đang đóng các chương trình...
vietnamese.StatusCreateDirs=Đang tạo thư mục...
vietnamese.StatusExtractFiles=Đang giải nén tệp...
vietnamese.StatusCreateIcons=Đang tạo biểu tượng...
vietnamese.StatusCreateRegistryEntries=Đang tạo thông tin hệ thống...
vietnamese.StatusSavingUninstall=Đang lưu thông tin gỡ cài đặt...
vietnamese.StatusRunProgram=Đang hoàn tất cài đặt...
vietnamese.StatusRollback=Đang hoàn tác thay đổi...

vietnamese.ConfirmUninstall=Bạn có muốn gỡ hoàn toàn %1 và các thành phần của chương trình không?
vietnamese.UninstallStatusLabel=Vui lòng chờ trong khi %1 đang được gỡ khỏi máy tính.
vietnamese.UninstalledAll=%1 đã được gỡ cài đặt thành công.
vietnamese.WizardUninstalling=Đang gỡ cài đặt
vietnamese.StatusUninstalling=Đang gỡ cài đặt %1...

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "QUANGLAN.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\QUANGLAN.ico"
Name: "{userprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\QUANGLAN.ico"
