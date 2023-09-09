# seccap-api-security
## 起動
```
$ git clone https://github.com/nokinsikasenbei-neo/seccap-api-security.git
$ cd seccap-api-security
$ docker-compose up --build -d
```
Webサイトには `http://localhost:5000`で、APIサーバ（仕様書）には`http://localhost:7000/docs`でアクセスできます。

## 終了
```
$ docker-compose down -v
```
