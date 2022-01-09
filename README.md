# Dom.ru customer check

<img src="https://user-images.githubusercontent.com/31013580/148692070-7ba0f25b-bf82-4448-9967-f24bad7f8538.png" width="500">

Dom.ru is one of the largest Russian ISP owned by [ERTelecom](https://en.wikipedia.org/wiki/ERTelecom). This script allows you to check for an account by phone number and get information about the account (parts of physical addresses, emails, etc.). 

## Usage

**Only phones as targets are supported for now!**

```sh
# without installing
$ ./run.py <target>

# as a package

$ python3 -m domru-customer-check <target>
# or simply
$ domru_customer_check <target>
```

<details>
<summary>Targets</summary>

Specify targets one or more times:
```sh
$ domru_customer_check 79194108310 79876543210

Collected 57 domains
100%|████████████████████████████████| 114/114 [00:08<00:00, 12.69it/s]
Target: 79194108310 (sbor)
Results found: 1
1) Contact Id: 9644224
Contact Type: 2
Agreement Id: 10557305
Row: ********6538
Address: Санкт-Петербург, Ш*************************, ******, 29, п.1

------------------------------
Target: 79194108310 (interzet)
Results found: 1
1) Contact Id: 9644224
Contact Type: 2
Agreement Id: 10557305
Row: ********6538
Address: Санкт-Петербург, Ш******************************, ******, 29, п.1

------------------------------
Target: 79876543210 (dzr)
Results found: 1
1) Contact Id: 4453093
Contact Type: 2
Agreement Id: 3291977
Row: ********0493
Address: Нижний Новгород, П**************************, **, 5, п.1

------------------------------
Target: 79876543210 (nn)
Results found: 1
1) Contact Id: 4453093
Contact Type: 2
Agreement Id: 3291977
Row: ********0493
Address: Нижний Новгород, П****************************, **, 5, п.1

------------------------------
Target: 79876543210 (tmn)
Results found: 3
1) Contact Id: 9847820
Contact Type: 2
Agreement Id: 2106611
Row: ********6127
Address: Тюмень, К**************************, **, 24, п.1

2) Contact Id: 9858960
Contact Type: 2
Agreement Id: 2112488
Row: ********0138
Address: Исетское  С, И*****************, ***********, 6, 1, п.1

3) Contact Id: 9882656
Contact Type: 2
Agreement Id: 2158682
Row: ********5413
Address: Тюмень, П*****************, *****, 61, п.1

------------------------------
Total found: 7
```

Or use a file with targets list:
```sh
$ domru_customer_check --target-list targets.txt
```

Or combine tool with other through input/output pipelining:
```sh
$ cat list.txt | domru_customer_check --targets-from-stdin
```
</details>

<details>
<summary>Reports</summary>

The skeleton implements CSV reports:

![telegram-cloud-photo-size-2-5393582422823647056-y](https://user-images.githubusercontent.com/31013580/148692023-d1146588-4b42-431f-81f1-4d02517d2597.jpg)
  
```sh
$ domru_customer_check 79194108310 79876543210 -oC results.csv
...
Results were saved to file results.csv

$ head -n 4 results.csv
"Target","Row","Address","Contact Id","Contact Type","Agreement Id"
"79194108310 (interzet)","********6538","Санкт-Петербург, Ш*****************, ******, 29, п.1","9644224","2","10557305"
"79194108310 (sbor)","********6538","Санкт-Петербург, Ш*************************, ******, 29, п.1","9644224","2","10557305"
"79876543210 (dzr)","********0493","Нижний Новгород, П**********************, **, 5, п.1","4453093","2","3291977"
```

And can save console output to text file separately:
```sh
domru_customer_check 79194108310 79876543210 -oT results.txt
...
$ head -n 7 results.txt
Target: 79194108310 (interzet)
Results found: 1
1) Contact Id: 9644224
Contact Type: 2
Agreement Id: 10557305
Row: ********6538
Address: Санкт-Петербург, Ш*************************, ******, 29, п.1
```
</details>

<details>
<summary>Proxy</summary>

The tool supports proxy:
```sh
$ domru_customer_check www.google.com --proxy http://localhost:8080
```
</details>

## Installation

Make sure you have Python3 and pip installed.


<details>
<summary>Manually</summary>

1. Clone or [download](https://github.com/soxoj/domru-customer-check/archive/refs/heads/main.zip) respository
```sh
$ git clone git@github.com:soxoj/domru-customer-check.git
```

2. Install dependencies
```sh
$ pip3 install -r requirements.txt
```
</details>

<details>
<summary>As a the package</summary>

You can clone/download repo and install it from the directory to use as a Python package.
```sh
$ pip3 install .
```
</details>
