# Sample AIWolf Python agent using aiwolf package
Sample AIWolf agent written in Python using [aiwolf package](https://github.com/AIWolfSharp/aiwolf-python).
## Prerequisites
* Python 3.8
* [aiwolf package]((https://github.com/AIWolfSharp/aiwolf-python)). 
You can install aiwolf package as follows,
```
pip install git+https://github.com/AIWolfSharp/aiwolf-python.git
```
## How to use
Suppose the AIWolf server at localhost is waiting a connection from an agent on port 10000.
You can connect this sample agent to the server as follows,
```
python start.py -h localhost -p 10000 -n name_you_like
```

## 参考試合の始め方
1. AutoStarter.iniファイルを書く  
game: 試合数  
view: true GUIで試合展開を確認できる。false 試合が一気に進み、ターミナルにログと試合結果が出力される


2. AutoStarter.shを実行する
```
./AutoStarter.sh
```
3. start.pyを実行する
```
python start.py -h localhost -p 10000 -n name_you_like
```