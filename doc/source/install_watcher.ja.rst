========================
Watcher インストール手順
========================

Watcherをソースコードからインストールする手順です。
IP、パスワードなどは置き換えてください。

前提条件
========

* CentOS Linux release 7.3.1611 (Core)
* Watcher 0.33.0

インストール
============

OSパッケージをインストール
--------------------------

.. code-block:: sh

    $ sudo yum install gcc python-devel libxml2-devel libxslt-devel mariadb-devel

virtualenv環境作成
------------------

.. code-block:: sh

    $ sudo yum install python-pip
    $ sudo pip install virtualenv
    $ sudo pip install virtualenvwrapper
    
    $ echo 'export WORKON_HOME=$HOME/.virtualenvs' >> ~/.bashrc
    $ echo 'export PROJECT_HOME=$HOME/Devel' >> ~/.bashrc
    $ echo 'source /usr/bin/virtualenvwrapper.sh' >> ~/.bashrc
    
    $ source ~/.bashrc
    
    $ mkvirtualenv watcher
    
Watcherインストール
-------------------

.. code-block:: sh

    $ git clone https://git.openstack.org/openstack/watcher
    $ cd watcher/
    $ git checkout -b 0.33.0 refs/tags/0.33.0
    $ python setup.py install
    $ pip install -r ./requirements.txt
    $ pip install -r ./test-requirements.txt
    
設定ファイル作成
----------------

.. code-block:: sh

    $ pip install tox
    $ tox -econfig
    $ sudo mkdir /etc/watcher
    $ sudo cp etc/watcher/watcher.conf.sample /etc/watcher/
    $ sudo mkdir /var/log/watcher
    $ sudo chown <user>:<group> /var/log/watcher
    
設定ファイル編集
----------------

以下の通り編集します。

.. code-block:: sh

    $ diff watcher.conf watcher.conf.sample
    10c10
    < debug = true
    ---
    > #debug = false
    43d42
    < log_dir = /var/log/watcher
    293d291
    < control_exchange = watcher
    414c412
    < host = 192.168.11.32
    ---
    > #host = 127.0.0.1
    551d548
    < connection = mysql://watcher:password@192.168.11.32/watcher?charset=utf8
    821,828d817
    < auth_type = password
    < auth_uri = http://192.168.11.32:5000
    < auth_url = http://192.168.11.32:35357
    < username = watcher
    < password = password
    < project_domain_name = Default
    < user_domain_name = Default
    < project_name = services
    1175c1164
    < rabbit_host = 192.168.11.32
    ---
    > #rabbit_host = localhost
    1192c1181
    < rabbit_hosts = 192.168.11.32:5672
    ---
    > #rabbit_hosts = $rabbit_host:$rabbit_port
    1203c1192
    < rabbit_userid = guest
    ---
    > #rabbit_userid = guest
    1210c1199
    < rabbit_password = guest
    ---
    > #rabbit_password = guest
    1680,1687d1668
    < auth_type = password
    < auth_uri = http://192.168.11.32:5000
    < auth_url = http://192.168.11.32:35357
    < username = watcher
    < password = password
    < project_domain_name = Default
    < user_domain_name = Default
    < project_name = services
    

Watcherエンドポイント作成
-------------------------

.. code-block:: sh

    $ source keystonerc_admin
    $ openstack user create --password password --email watcher@example.com --project=services watcher
    $ openstack role add --project services --user watcher admin
    $ openstack service create --name watcher --description="Infrastructure Optimization service" infra-optim
    $ openstack endpoint create --region RegionOne infra-optim public http://192.168.11.32:9322
    $ openstack endpoint create --region RegionOne infra-optim internal http://192.168.11.32:9322
    $ openstack endpoint create --region RegionOne infra-optim admin http://192.168.11.32:9322

Watcherデータベース作成
-------------------------

.. code-block:: sh

    $ pip install mysql-python
    
    $ mysql -u root -p
    MariaDB [(none)]> CREATE DATABASE watcher CHARACTER SET utf8;
    MariaDB [(none)]> GRANT ALL PRIVILEGES ON watcher.* TO 'watcher'@'localhost' IDENTIFIED BY 'password';
    MariaDB [(none)]> GRANT ALL PRIVILEGES ON watcher.* TO 'watcher'@'%' IDENTIFIED BY 'password';
    MariaDB [(none)]> exit
    Bye
    $ watcher-db-manage --config-file /etc/watcher/watcher.conf create_schema

ポリシーファイル作成
--------------------

.. code-block:: sh

    $ sudo cp etc/watcher/policy.json /etc/watcher

サービス起動
------------

.. code-block:: sh

    $ watcher-api &
    $ watcher-decision-engine &
    $ watcher-applier &
    
Watcherクライアントインストール
--------------------------------

$ pip install python-watcherclient

動作確認
========

.. code-block:: sh

    $ watcher goal list
    +--------------------------------------+----------------------+----------------------+
    | UUID                                 | Name                 | Display name         |
    +--------------------------------------+----------------------+----------------------+
    | 0c2dc90a-835a-4b84-afca-5dffff9ad246 | dummy                | Dummy goal           |
    | 666bd7ba-93c5-4038-8179-1860b2dc4786 | workload_balancing   | Workload Balancing   |
    | 27580fd7-67e9-43e6-a38d-3359f27484de | server_consolidation | Server Consolidation |
    | 88a3df95-b14d-4208-b462-370893a4aa13 | thermal_optimization | Thermal Optimization |
    | 37986b34-6d11-489d-bacc-03839457ee76 | airflow_optimization | Airflow Optimization |
    | 62e59a66-1b92-4d7b-8deb-d8c65817a225 | unclassified         | Unclassified         |
    +--------------------------------------+----------------------+----------------------+



