# MariaDB 01–04 demo and practice materials

這是 4-learn MariaDB 課程 01–03 的教師／環境準備配套。每位學生在自己的 Ubuntu VM 內執行 MariaDB server；Windows 只透過 SSH 進入 VM，不連老師的 MariaDB server。

## 01–03 基礎環境初始化

在 VM 內 clone 這個 repo，再執行：

```bash
git clone https://github.com/4-learn/mariadb-demo.git
cd mariadb-demo
python3 prepare_lab.py
```

不要用 `sudo python3`。程式會透過 sudo 執行必要的 root socket SQL，但會把每台 VM 的 reader 憑證寫在使用者家目錄，權限為 `0600`。

它會建立 `mariadb_course`、`products-v1` 與 `course_reader@localhost`，產生 `~/mariadb-course-reader.cnf`。這不是學生 Workshop 的操作；教師先在每台 VM 初始化並建立可回復的 01–03 checkpoint。


## 04 起的學生練習環境

教師示範完成後，學生在自己的 Ubuntu VM 執行下列命令，建立獨立的 `mariadb_workshop_2026` 練習資料庫。這不會修改 `mariadb_course`。

```bash
python3 prepare_workshop.py
```

腳本會建立 `mariadb_workshop_2026`、`mariadb_restore_2026`、`course_editor@localhost`、`course_app@localhost`，並匯入 `products-v1`、`sop-v1`。它會產生權限為 `0600` 的私人設定檔；若資料庫、帳號或設定檔已存在，腳本會停止，不要刪除資料後重跑。

這是練習環境初始化工具，不是考試答案。第 04 節開始使用隔離的 Workshop 資料庫；學生不連教師的 MariaDB server。

## 學生進入方式

學生從 Windows PowerShell 進入自己的 VM：

```powershell
ssh <ubuntu-user>@<vm-host-or-ip>
```

進入 Ubuntu 後，確認教師已完成初始化，再依 HackMD Ch1 的 socket 登入命令操作。學生不需要連線到教師的 MariaDB server，也不需要開放 3306。

## 已完成初始化時

`git clone` 與 `python3 prepare_lab.py` 只做一次。完成後直接執行教材的驗證命令；若初始化程式因資料庫、帳號或憑證檔已存在而停止，不要刪除資料重跑。
