# Tools 使い方

## TL;DR

-   `execute_test.sh`
    -   `create_test_env.py` 生成したインプットを元に、
        watcher の audit を作成するスクリプト。
-   `create_test_env.py`
    -   Zone マイグレーションのテスト環境を作成するスクリプト。
-   `delete_test_env.py`
    -   上記スクリプトで作成したテスト環境を削除するスクリプト。

## execute_test.sh

audit を作成し、Zone マイグレーションを実施します。

### 使い方

    $ bash execute_test.sh input.json \
                           ${OS_WATCHER_GOAL_ID} \
                           ${OS_WATCHER_STRATEGY_ID}

-   `input.json`:
    `create_test_env.py` で生成したパラメータファイル。
-   `${OS_WATCHER_GOAL_ID}`:
    Watcher の Goal の ID。 (デフォルト: `${OS_WATCHER_GOAL_ID}`)
-   `${OS_WATCHER_STRATEGY_ID}`:
    Watcher の Starategy の ID。 (デフォルト: `${OS_WATCHER_STRATEGY_ID}`)

内部では　`audit audit create`　を呼んでいるだけ。

## create_test_env.py

### 使い方

    $ python create_test_env.py `テスト環境定義ファイル` > input.json

以上でテスト環境定義ファイルで定義したテスト用環境が作成され、
Zone マイグレーションで利用する Watcher に渡すパラメータファイルが標準出力に出力される。

### 事前条件

-   admin ユーザが作成されていること。
-   nova 及び cinder にターゲットとなる availability_zone が作成されていること。
-   移動対象となる VM 及びボリュームを配置するテナントが作成されていること。
-   移動対象となる VM が属するネットワークが作成されていること。

`テスト環境定義ファイル` に以下の形で事前環境を記述しておく必要がある。

```yaml
env:
  availability_zone:     # マイグレーションする Zone の指定。
    nova: nova
    cinder: nova
  admin:                 # 事前に登録された admin ユーザの認証情報。
    auth_url: 'http://192.168.11.197:5000/v3/'
    password: openstack
    username: admin
    user_domain_id: default
    project_name: admin
    project_domain_id: default
---
```

### 制限事項

-   対象となるテナントはネットワークを二つ以上持つことができない。
-   VM 作成時に keypair を指定することができない。
-   VM 及び Volume の名前はユニークである必要がある。
-   `create_test_env.py` を環境を削除する前に同じ `テスト環境定義ファイル` で二度実行した際の結果は未定義。

### 機能

-   ユーザ作成
-   VM 作成
-   Volume 作成

#### ユーザ作成

後の VM 及び Volume を作成するユーザを作成することができる。
以下が `テスト環境定義ファイル` での作成するユーザの定義である。

```yaml
test1:                # ユーザ名 (ユニーク)
  password: password  # パスワード (必須)
  project: demo       # 所属するテナント名またはID (必須)
  domain: default     # 所属するドメイン名またはID (必須)
  roles: [admin]      # プロジェクトでの role。admin であることが推奨。 (必須)
---
```

プロジェクト及びドメイン、ロールは事前に存在する必要がある。
また、ロールがメンバーであった場合、作成する VM 及び Volume の移動元を指定することができない。

#### VM 作成

以下に `テスト環境定義ファイル` で VM を作成する際の定義方法を示す。

```yaml
instance1:                        # VM名 (ユニーク)
  status: active                  # ステータス (active/shutoff)(オプション)
  src_hostname: compute01         # 移動元コンピュート名 (オプション)
  dst_hostname: compute02         # 移動先コンピュート名 (オプション)
  flavor: m1.small                # フレーバー名 (必須)
  image: cirros-0.3.4-x86_64-uec  # イメージ名 (必須)
  user: test1                     # ユーザ名 (必須)
  output: ignore                  # 出力制御フラグ (オプション)
---
```

-   `ステータス`: 稼働中か、シャットダウンされた VM かどうかを定義する。
    shutoff を指定した場合、boot したのちに VM が ACTIVE なステータスになるのを待ったのちに、
    stop を行う。
-   `フレーバ名`: 事前に作成しておく必要がある。
-   `イメージ名`: 事前に登録しておく必要がある。
-   `ユーザ名`: 上記ユーザ作成セクションで定義されたユーザ名である必要がある。
-   `出力制御フラグ`: `ignore` が指定された場合、
    Watcher に渡すパラメータファイルに作成されたインスタンスが含まれなくなる。
    このフラグは Zone マイグレーションで `in-use` であるボリュームのみのマイグレーションをテストしたい時に有用。
    (`in-use` であるボリュームにはアタッチ先の VM が必須であるため。)

#### Volume 作成

以下に `テスト環境定義ファイル` で Volume を作成する際の定義方法を示す。

```yaml
volume1:                  # Volume名 (ユニーク)
  src_hostname: 'controller@lvmdriver-1#lvmdriver-1'  # 移動元プール名 (オプション)
  dst_hostname: 'controller@lvmdriver-2#lvmdriver-2'  # 移動先プール名 (オプション)
  attached_to: instance1  # アタッチ先インスタンス名 (オプション)
  type: lvmdriver-1       # ボリュームタイプ　(オプション)
  size: 1                 # ボリュームサイズ (オプション)
  user: test1             # ユーザ名 (必須)
  output: ignore          # 出力制御フラグ (オプション)
---
```

-   `移動元プール名`: cinder は基本的に移動元プール名を指定して volume を作成することができない。
    そのため、本ツールでは、移動元プール名が指定されていた場合は、
    一旦起動したのちにプール名を確認後、移動元プールに `cinder migrate` を試みる。
-   `移動先プール名`: **volume に `attached_to` を指定していなかった場合必須。**
-   `アタッチ先インスタンス名`:　VM に作成したボリュームをアタッチしたかった場合に指定する。
    上記の VM 作成セクションで定義された VM 名である必要がある。
-   `ユーザ名`: 上記ユーザ作成セクションで定義されたユーザ名である必要がある。
-   `出力制御フラグ`: `ignore` が指定された場合、
    Watcher に渡すパラメータファイルに作成されたインスタンスが含まれなくなる。

#### `テスト環境定義ファイル`　例

-   [2台のVMをライブマイグレートする際の環境](tests/00-live-migrate-2.yaml)
-   [1台のVMをライブマイグレート,1台のVMをコールドマイグレートする際の環境](tests/01-mix-migrate-2.yaml)
-   [2台のボリュームをマイグレートする際の環境](tests/02-volume-migrate-2.yaml)
-   [2台のボリュームをボリュームアップデートする際の環境](tests/03-volume-update.yaml)

## delete_test_env.py

### 使い方

    $ python delete_test_env.py `テスト環境定義ファイル`

以上で、テスト環境定義ファイルで定義されたVM及びボリュームが削除される。
