# hive-builder-template

Github Codespaces を用いて hive-builder を利用する際のテンプレートレポジトリです。
hive-builder 本体についての詳細な利用法については[ドキュメント](https://hive-builder.readthedocs.io/ja/latest/)を参照して下さい。

# 構築手順
以下に記す手順に従うことで Codespaces の開発コンテナに hive-builder のマザー環境を構築することができます。

## レポジトリを作成する

codespaces を起動するためのレポジトリを作成します。
本レポジトリのトップページの右上にある **Use this template** を押して、**Create a new repository**を選択することで、レポジトリ作成ページに移動します。

レポジトリ名などの必要な情報を入力してレポジトリを作成して下さい。

## Codespaces を作成する
作成したレポジトリのトップページから **Code** を押して、 **Codespaces** タブのプラスボタンを押すことで Codespaces が作成できます。

### devcontainer

Codespaces は `.devcontainer` フォルダを参照して開発コンテナを作成します。
開発コンテナは大まかには以下の流れに従ってビルドされます。

1. `mcr.microsoft.com/vscode/devcontainers/python:3`をベースイメージとしてpull する
1. 各種パッケージをインストールする
1. python の仮想環境を`/opt/hive`に作成する
1. 仮想環境にhive-builder をインストールする
1. systemd でコンテナを起動する

上記の処理に 2~3 分ほど時間がかかります。 
また、開発コンテナ作成時に `ansible-galaxy` のパッケージインストールが行われます。
この影響で、コンテナ作成完了後も約5分ほど hive-builder を利用できません。

## プロジェクトを編集する
開発コンテナのワークスペースフォルダがそのまま hive-builder のプロジェクトディレクトリとなっています。

また、デフォルトで `tmpl`という名前の hive 定義とサービス定義のサンプルが入っています。
これを編集することで hive-builder を用いた構築が利用できます。

以上の手順終了後はこのファイルを適宜削除/修正してREADME.mdを記述して下さい。

# setup
hive-builder を利用する上で利便性を向上させるためのスクリプトを`setup`ディレクトリ配下に置いています。
それぞれ使い方について説明します。

## init.py

hive.yml の記述、依存パッケージのインストール、hive-builderの変数設定等を補助するPythonコードです。
最初にベースとなる項目について質問し、それを回答することで hive.ymlが上書きされます。
プロバイダがvagrantだったときは後述する [Vagrant](#vagrantのインストール)と[Squid](#squid-のインストール)のインストールも自動で行われる他、stage変数の設定も行われます。


## 秘密情報の共有

IaaSを用いて構築を行った時に生成された秘密情報を共有することができます。
以下にその手順について記述します。

### アップロード側

hive-builder で構築を行い、その秘密情報を共有したいユーザは、`setup/encrypt_secrets.py`を実行して下さい。

これにより、ワークスペースフォルダ配下に`secrets.gpg`が生成されます。
これをレポジトリにアップロードして下さい。

#### `encrypt_secrets.py` の詳細

`encrypt_secrets.py` では以下の操作を順に実行します。

1. 秘密情報を`/tmp/secrets` ディレクトリ配下に集める
1. secrets をzipで圧縮する
1. ランダムな文字列を生成する
1. 生成した文字列をパスワードとして、圧縮したzipファイルを GPG で暗号化する
1. パスワードを Github Secrets の Codespaces 領域に `HBSEC_PASSPHRASE`として保存する
1. `/tmp` 配下に置いていたディレクトリを削除する

### ダウンロード側

レポジトリに secrets.gpg が存在し、これを使って秘密情報を復号したいユーザは`setup/decrypt_secrets.py`を実行して下さい。

これにより、ワークスペースフォルダ配下に秘密情報ファイルが配置されます。
また、すでに同名のファイルが存在した場合は上書きの確認が行われます。

#### `decrypt_secrets.py` の詳細

`decrypt_secrets.py` では以下の操作を順に実行します。

1. `HBSEC_PASSPHRASE`環境変数を参照して`secrets.gpg`の復号を行う
1. zipファイルが生成されるのでこれを解凍する
1. ファイルを適切な位置にコピーする

### 秘密情報の削除

秘密情報の共有をやめたい場合は、レポジトリの `secrets.gpg`を削除して下さい。また、`setup/delete_hbsec_secrets.py`を実行することで`HBSEC_`という接頭辞の Github Secrets を全て削除できます。

# Vagrant の利用

本レポジトリを用いて Vagrant を利用する場合、Vagrant コンテナ内から外部ネットワークと Vagrant内部ネットワークには接続することができません。
このため、外部ネットワークに接続する際は Squid などのプロキシサーバに接続し、Vagrant内部ネットワークは利用しない1台構成(number_of_hosts を1に設定する構成)にとどめて下さい。

## Vagrantのインストール

`setup/scripts`配下に存在する`install-vagrant.sh`を実行することで開発コンテナに Vagrant をインストールすることができます。

## Squid のインストール

`setup/scripts`配下に存在する`install-squid.sh`を実行することで開発コンテナに Squid をインストールすることができます。

Squid の設定を変更したい場合は `setup/files`配下にある`squid.conf`を編集してから再度実行することで反映できます。

# vscode によるサポート

vscodeの機能を用いて hive-builder の構築のサポートを行なっています。以下に紹介していきます。

## Ansible Playbook の記述

`roles` ディレクトリ配下に存在するAnsible Playbook の記述をサポートする各種拡張機能が導入されています。

validation チェックは ansible-lint という python パッケージにより行われており、これのコンフィグYAMLは `.vscode/configs/ansible-lint.yml` を参照しています。ansible-lintの設定例については[公式ドキュメント](https://ansible.readthedocs.io/projects/lint/configuring/#specifying-configuration-files)を参照して下さい。
そもそも validation チェックが必要ないという場合は `.vscode/settings.json`の`ansible.validation.lint.enabled`を`false`に設定して下さい。

### キーボードショートカットの追加

ansible 拡張機能には自動修正機能がついていません。
ansible-lint による自動修正機能を使いたい場合はキーボードショートカットを追加して下さい。

`.vscode/keybindings-example.json`をキーボードショートカットの`keybindings.json`にコピーペーストすることで、 Playbook のyamlファイルを開いている時に`shift + alt + f`で自動修正タスクが実行されるようになります。

## JSON Schema
inventory 配下に存在するhive定義yamlや、サービス定義yamlに対して JSON Schema が適用されています。デフォルトの設定では `inventory/hive.yml` に対して hive定義yaml の JSON Schema を適用し、それ以外の `inventory` 配下に存在する `yml` ファイルに対してサービス定義yaml の JSON Schema を適用します。 

## ローカルポートフォワーディング

vscode を用いたローカルポートフォワーディングも可能です。
建てたサービスコンテナにブラウザでアクセスしたい場合は`hive ssh -L {開発コンテナポート}:{リモートホスト}:{リモートポート}`でポートフォワーディングが可能です。
ポートタブに新しくブラウザ側ポートのリンクが追加されているので、これをクリックしてアクセスすることができます。