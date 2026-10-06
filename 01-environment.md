# 01 環境確認：連進 MariaDB

> **定位**：在自己的 Ubuntu VM 安裝 MariaDB、準備課程資料，並用受限帳號登入。

## 學習目標

完成本節後，你應該能夠：

- 從 Windows SSH 進入自己的 VirtualBox Ubuntu VM
- 在 VM 內安裝並啟動 MariaDB 11.8
- 建立 `mariadb_course` 與 `course_reader`
- 使用 Unix socket 登入自己的 MariaDB server
- 分辨 client、server、database 與帳號

## 範例程式碼

- [公開 demo repo](https://github.com/4-learn/mariadb-demo)：安裝後用來建立本機課程資料。
- Workshop 是私有考試題庫，由教師個別授權，不放在公開講義中。

---

## 情境

你剛建立一台自己的 Ubuntu VM，要把它變成 MariaDB 練習環境。

教師會示範流程，但每位學生都要在自己的 VM 完成安裝、初始化與登入。你不會連到教師的 MariaDB server。

---

## 講解

### 1. 從 Windows 進入自己的 Ubuntu VM

在 Windows PowerShell 執行：

```powershell
ssh <ubuntu-user>@<vm-host-or-ip>
```

以下命令都在 Ubuntu VM 內執行。MariaDB server 也在這台 VM 內。

### 2. 安裝 MariaDB

先確認套件來源：

```bash
sudo apt update
apt-cache policy mariadb-server mariadb-client
```

本課使用 MariaDB 11.8，因為後續章節會使用 `VECTOR` 與 ANN。若 Candidate 不是 11.8，使用 MariaDB 官方 repository setup：

```bash
sudo apt install -y curl ca-certificates python3
curl -fLsS -o mariadb_repo_setup https://r.mariadb.com/downloads/mariadb_repo_setup
printf '%s  %s\n' 'b54c87edfe81b9837ef44a4a4f39383dd8df32776e6a18c0743a5d3ece044ac3' mariadb_repo_setup | sha256sum -c -
```

必須看到：

```text
mariadb_repo_setup: OK
```

若驗證失敗，停止並請教師確認，不要跳過驗證。

```bash
sudo bash ./mariadb_repo_setup --mariadb-server-version='mariadb-11.8' --skip-maxscale --skip-tools
sudo apt update
sudo apt install -y mariadb-server mariadb-client
sudo systemctl enable --now mariadb
```

確認版本與服務：

```bash
mariadb --version
systemctl is-active mariadb
```

### 3. 建立課程資料與受限帳號

第一次執行時，在 VM 內 clone 公開 demo repo：

```bash
git clone https://github.com/4-learn/mariadb-demo.git
cd mariadb-demo
python3 prepare_lab.py
```

這三行只執行一次。程式會在你的 VM 建立：

- `mariadb_course`
- `course_reader@localhost`
- `products-v1`
- `~/mariadb-course-reader.cnf`（權限 `0600`）

如果已經 clone 或初始化，不要重跑；直接進入既有的 `mariadb-demo` 目錄。不要使用 `sudo python3`。

### 4. 登入自己的 MariaDB server

使用初始化時產生的 `course_reader` 密碼，在提示出現時輸入：

```bash
mariadb --no-defaults --default-character-set=utf8mb4 --protocol=socket --user=course_reader --password mariadb_course
```

成功後會看到：

```text
MariaDB [mariadb_course]>
```

![image](https://hackmd.io/_uploads/BysyTmCcfg.png)

### 5. 分辨 client 與 server

在 Ubuntu shell 執行：

```bash
mariadb --version
```

這是 **client** 版本，不代表已登入 server。

![image](https://hackmd.io/_uploads/HJyG6mC5zx.png)

登入 MariaDB 後執行：

```sql
SELECT VERSION() AS server_version,
       DATABASE() AS current_database,
       CURRENT_USER() AS account;
```

查看目前 database 的所有資料表：

```sql
SHOW TABLES;
```

一次查看目前 database 的所有資料表與欄位：

```sql
SELECT TABLE_NAME,
       ORDINAL_POSITION,
       COLUMN_NAME,
       COLUMN_TYPE,
       IS_NULLABLE,
       COLUMN_KEY
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
ORDER BY TABLE_NAME, ORDINAL_POSITION;
```

`SHOW TABLES` 是快速查看資料表的指令；`information_schema.COLUMNS` 讓你一次看到每張表的欄位、順序、型別、NULL 設定與索引標記。

再查詢課程版本資料：

```sql
SELECT * FROM course_meta;
```

應看到：

```text
current_database: mariadb_course
account:          course_reader@localhost
dataset_version:  products-v1
```

### 6. 取消未完成的 SQL 並離開

在 MariaDB 提示字元輸入以下第一行，不要加分號：

```sql
SELECT VERSION()
```

看到 `->` 後輸入：

```text
\c
```

回到提示字元後離開：

```text
exit;
```

---

## Workshop

### 題目

在自己的 Ubuntu VM 完成以下任務：

1. 從 Windows SSH 登入 Ubuntu。
2. 確認 MariaDB server 正在執行。
3. 使用 `course_reader` 登入 `mariadb_course`。
4. 執行環境查詢。
5. 使用 `SHOW TABLES;` 查看所有資料表。
6. 使用 `information_schema.COLUMNS` 一次查看所有資料表與欄位。
7. 執行 `SELECT * FROM course_meta;`。
8. 使用 `\c` 取消一段未完成的 SQL。
9. 使用 `exit;` 回到 Ubuntu shell。

### 預期輸出

```text
server_version：11.8.x
current_database：mariadb_course
account：course_reader@localhost
dataset_version：products-v1
取消未完成 SQL：成功回到 MariaDB prompt
離開後：回到 Ubuntu shell
```

### 交件

記錄以上結果，不要交密碼、`mariadb-course-reader.cnf` 內容或完整敏感畫面。

### 解答

- [Workshop repo](https://github.com/4-learn/mariadb-workshop)：目前為私有考試題庫；課程結束後會公開，請保留此連結。
