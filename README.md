# MariaDB 01–03 demo materials

這是 4-learn MariaDB 課程 01–03 的教師／環境準備配套。每位學生在自己的 Ubuntu VM 內執行 MariaDB server；Windows 只透過 SSH 進入 VM，不連老師的 MariaDB server。

## 教師／環境管理者初始化

在 VM 內 clone 這個 repo，再執行：

```bash
git clone https://github.com/4-learn/mariadb-demo.git
cd mariadb-demo
python3 prepare_lab.py
```

不要用 `sudo python3`。程式會透過 sudo 執行必要的 root socket SQL，但會把每台 VM 的 reader 憑證寫在使用者家目錄，權限為 `0600`。

它會建立 `mariadb_course`、`products-v1` 與 `course_reader@localhost`，產生 `~/mariadb-course-reader.cnf`。這不是學生 Workshop 的操作；教師先在每台 VM 初始化並建立可回復的 01–03 checkpoint。

## 學生進入方式

學生從 Windows PowerShell 進入自己的 VM：

```powershell
ssh <ubuntu-user>@<vm-host-or-ip>
```

進入 Ubuntu 後，確認教師已完成初始化，再依 HackMD Ch1 的 socket 登入命令操作。學生不需要連線到教師的 MariaDB server，也不需要開放 3306。
