# hive-procube-products

procubeの NetSoarerシリーズ製品である**IDManager, Webgate, Access Manager**の3つを自動構築する hive-builderインベントリを提供します。

## 動作環境

開発コンテナ(Github Codespaces)による動作確認を行なっています。
その他の環境で動かす場合は、pipコマンドでhive-builderをインストールして、install-collection サブコマンドでansibleコレクションをインストールして下さい。
```
python -m venv hive
source hive/bin/activate
pip install hive-builder

cd path/to/hive-procube-products
hive install-collection
```

## 前提条件

### procube クライアント証明書
procube製品を利用するためのNSSDCから発行されたクライアント証明書と秘密鍵が必要です。

### AWSのアクセスキー
デフォルトのhive.ymlの設定ではAWS上に3台のEC2インスタンスを構築します。
EC2インスタンスを構築する権限を持ったアカウントと、そのアクセスキーが必要です。

### ドメイン要件

親ドメイン（上位DNS）において、**NSレコード**および**グルーレコード**(ネームサーバーのAレコード)の設定変更が可能なドメインが必要です。
これらの設定によりPowerDNSへ権限委譲を行うことで、hive-builderを用いたDNSレコードの自動登録が可能になります。

### Googleメールアカウント
Access Managerのメール送信設定で使用するGmailのメールアドレスとアプリパスワードが必要です。

## 構築手順

以下に構築手順を記します。hive-builderのインストール方法とcollectionのインストール方法については前述の「動作環境」を参照して下さい。
hive-builderの基本的な使い方については、[hive-builder公式ドキュメント](https://hive-builder.readthedocs.io/ja/latest/)を参照して下さい。

### 1. hive変数の設定
デフォルトでは stage が private になっています。本番環境に構築する場合は stage を production に変更して下さい。
```
hive set stage production
```
また、AWSのアクセスキー、シークレットキーを設定します。
```
hive set aws_access_key_id: YOUR_AWS_ACCESS_KEY
hive set aws_secret_access_key YOUR_AWS_SECRET
```

### 2. secrets.ymlの作成

secrets.yml.example を参考にして secrets.yml をプロジェクトルートに作成します。

| キー名 | 説明 |
| --- | --- |
| acme_email | Let's Encryptの証明書を取得するためのメールアドレス(任意のメールアドレス) |
| nssdc_client_cert | NSSDCクライアント証明書 (PEM形式) |
| nssdc_client_key | NSSDCクライアント証明書の秘密鍵 (PEM形式) |
| saml_dummy_cert | SAML用の自己署名証明書 (PEM形式) |
| saml_dummy_key | SAML用の自己署名証明書の秘密鍵 (PEM形式) |
| saml_serial_number | SAML用の証明書のシリアル番号 |
| ldap_config_password | LDAPの設定用パスワード(任意の値)|
| idp_persistentid_salt | SAMLのPersistentID生成用のソルト(任意の値)|
| google_mail_user | Access Managerのメール送信設定で使用するGmailのメールアドレス |
| google_app_password | Access Managerのメール送信設定で使用するGmailのアプリパスワード |

#### saml_dummy_cert と saml_dummy_key の作成方法
以下のコマンドで自己署名証明書と秘密鍵を作成できます
```
openssl req -x509 -newkey rsa:2048 -keyout saml_dummy_key.pem -out saml_dummy_cert.pem -days 365 -nodes -subj "/CN=dummy"
```
saml_serial_number は16進数で上記証明書のシリアル番号を指定して下さい。
```
openssl x509 -in saml_dummy_cert.pem -noout -serial
```

### 3. inventoryの設定
inventory/hive.yml とinventory/group_vars/all.yml を開き、デフォルトの設定で問題ないかどうかを確認して下さい。
特に以下の設定項目については、必要に応じて変更して下さい。
| 変数名 | 説明 | パス |
| --- | --- | --- |
| name | 構築するシステムの名前。hive_nameで参照されます。 | inventory/hive.yml |
| stages.production.region | EC2インスタンスを構築するAWSリージョン | inventory/hive.yml |
| domain | 構築するシステムで使用するドメイン名 | inventory/group_vars/all.yml |

### 4. build-infraの実行

build-infra サブコマンドでAWS上にEC2インスタンスを構築します。
```
hive build-infra
```

### 5. 権限委譲設定
構築したEC2インスタンスのパブリックIPアドレスに対して、ドメインのNSレコードとAレコードを設定します。

[inventoryの設定](#3-inventoryの設定)で指定した`domain`が procube-products.procube-demo.jp である場合の例を示します。
対象サブドメイン(procube-products)の管理権限を本システムの3台のVMへ委譲します。親ドメイン(例: procube-demo.jp)のDNSサーバーに以下のNSレコードを追加して下さい。

| レコード名 | レコードタイプ | 値 |
| --- | --- | --- |
| procube-products | NS | ns0-procube-products.procube-demo.jp |
| procube-products | NS | ns1-procube-products.procube-demo.jp |
| procube-products | NS | ns2-procube-products.procube-demo.jp |
| ns0-procube-products | A | <EC2インスタンス1台目のパブリックIPアドレス> |
| ns1-procube-products | A | <EC2インスタンス2台目のパブリックIPアドレス> |
| ns2-procube-products | A | <EC2インスタンス3台目のパブリックIPアドレス> |

### 6. hive all の実行

hive all を実行することで自動構築が開始されます。
```
hive all
```
問題なく全てのタスクが完了すれば構築完了です。

タスク完了後もサービスの処理に時間がかかる場合があります。しばらく待ってから動作確認を行って下さい。

## 動作確認
設定したドメイン名にブラウザでアクセスし、AccessManagerのログイン画面が表示されることを確認して下さい。
例(domainがprocube-products.procube-demo.jp)の場合だと、以下のURLにアクセスします。

https://idm3.procube-products.procube-demo.jp

デフォルトの管理者アカウントは以下の通りです。
| ユーザー名 | パスワード |
| --- | --- |
| admin | adminp@ssword |

認証に成功するとOTPの設定画面が表示されます。OTPの設定を行い、ログインできることを確認して下さい。
IDManager V3 の管理画面にリダイレクトされます。