docker build -t sudoku-app:0.2.0 .
docker save -o sudoku-app_0.2.0.tar sudoku-app:0.2.0
sudo k3s ctr images import sudoku-app_0.2.0.tar
kubectl apply -f sudoku-deployment.yaml
kubectl rollout status deployment/sudoku-app --timeout=5m

Sudoku App for Kubernetes

Ez a projekt egy webes Sudoku alkalmazás, amely Kubernetes alatt futtatható, és a meglévő Redis példányt használja session tárolásra.

Főbb jellemzők

- Webes Sudoku játék
- Felugró számválasztó üres mezőre kattintáskor
- Csak a szabályosan beírható számok jelennek meg
- Session tárolás Redisben
- Docker image-ből fut Kubernetes alatt
- Egyszerű manuális build és deploy shell scriptek nélkül

Könyvtárstruktúra

sudoku-app/
├─ app.py
├─ sudoku.py
├─ puzzles.json
├─ requirements.txt
├─ Dockerfile
├─ README.md
├─ templates/
│  └─ index.html
├─ static/
│  ├─ styles.css
│  └─ app.js
└─ k8s/
   ├─ sudoku-app-deployment.yaml
   └─ sudoku-app-service.yaml

Előfeltételek

Szükséges eszközök:
- Docker
- Kubernetes / k3s
- kubectl
- meglévő Redis a klaszterben

A Sudoku alkalmazás nem indít saját Redis példányt, hanem a már meglévőt használja.

Redis service név ellenőrzése

Először nézd meg, hogy mi a Redis service neve:

kubectl get svc

Példa:
- ha a service neve redis-master, akkor azt kell használni REDIS_HOST-nak
- a pod neve, például redis-master-0, nem feltétlenül ugyanaz, mint a service neve

A példák a redis-master service névvel számolnak.

Port

Az alkalmazás alapértelmezett portja:
9097

Elérés például:
http://<NODE-IP>:9097

Első telepítés

1. Lépj be a projekt könyvtárba:
cd sudoku-app

2. Docker image build:
docker build -t sudoku-app:0.1.0 .

3. Image export tar fájlba:
docker save -o sudoku-app_0.1.0.tar sudoku-app:0.1.0

4. Image import a k3s containerd-be:
sudo k3s ctr images import sudoku-app_0.1.0.tar

5. ConfigMap létrehozása a meglévő Redishez:
A példában a Redis service neve redis-master.

kubectl create configmap sudoku-config \
  --from-literal=APP_PORT=9097 \
  --from-literal=SESSION_BACKEND=redis \
  --from-literal=REDIS_HOST=redis-master \
  --from-literal=REDIS_PORT=6379 \
  --from-literal=SESSION_TTL_SECONDS=86400 \
  --dry-run=client -o yaml | kubectl apply -f -

Ha nálad a Redis service neve nem redis-master, akkor ezt az értéket cseréld a megfelelő névre.

6. Deployment és Service telepítése:
kubectl apply -f k8s/sudoku-app-deployment.yaml
kubectl apply -f k8s/sudoku-app-service.yaml

7. Rollout ellenőrzése:
kubectl rollout status deployment/sudoku-app --timeout=5m

8. Ellenőrzés:
kubectl get pods -o wide
kubectl get svc
kubectl logs deployment/sudoku-app --tail=50

Kódfrissítés deployolása

Javasolt minden új buildhez új image tag-et használni.
Példa: 0.1.1

1. Lépj be a projekt könyvtárba:
cd sudoku-app

2. Új image build:
docker build -t sudoku-app:0.1.1 .

3. Export tar-ba:
docker save -o sudoku-app_0.1.1.tar sudoku-app:0.1.1

4. Import a k3s-be:
sudo k3s ctr images import sudoku-app_0.1.1.tar

5. Deployment image frissítése:
kubectl set image deployment/sudoku-app sudoku-app=sudoku-app:0.1.1

6. Rollout figyelése:
kubectl rollout status deployment/sudoku-app --timeout=5m

7. Ellenőrzés:
kubectl get pods -o wide
kubectl logs deployment/sudoku-app --tail=50

Ha a konfiguráció változik

Ha például változik:
- a Redis host neve
- a port
- a session TTL
- más ConfigMap érték

akkor futtasd újra a ConfigMap létrehozó parancsot, majd indíts új rolloutot:

kubectl rollout restart deployment/sudoku-app
kubectl rollout status deployment/sudoku-app --timeout=5m

Fontos megjegyzés

Ehhez a verzióhoz nem kell külön Redis deployment vagy service.

Ezért ezeket nem kell használni:
kubectl apply -f k8s/sudoku-redis-deployment.yaml
kubectl apply -f k8s/sudoku-redis-service.yaml

Ha ilyen fájlok még benne vannak a projektben, figyelmen kívül hagyhatók vagy törölhetők.

Hibaellenőrzés

Podok állapota:
kubectl get pods -o wide

Deployment állapota:
kubectl describe deployment sudoku-app

Pod logok:
kubectl logs deployment/sudoku-app --tail=100

Service ellenőrzése:
kubectl get svc

Hasznos megjegyzések

- mindig új image tag-et használj frissítéskor
- ha ugyanazt a tag-et használod, nehezebb biztosan látni, hogy az új image fut-e
- ha a Redis service neve más, a REDIS_HOST értéket módosítani kell
- ha a 9097 port foglalt, a deployment, service és configmap portjait azonos értékre kell átírni

Egészségellenőrzés

Az alkalmazás rendelkezik health endpointtal:
/healthz

Például:
http://<NODE-IP>:9097/healthz

API végpontok

- GET /healthz
- POST /api/new-game
- GET /api/state
- POST /api/move
- POST /api/reset

Játéklogika

A Sudoku UI úgy működik, hogy:
- csak a nem fix mezők kattinthatók
- kattintásra felugró számválasztó jelenik meg
- a választható számok listájából kimaradnak azok, amelyek:
  - az adott sorban már szerepelnek
  - az adott oszlopban már szerepelnek
  - az adott 3x3 blokkban már szerepelnek

A backend ugyanígy validálja a lépést, tehát kliensoldali manipulációval sem lehet szabálytalan értéket eltárolni.

Verziózás javaslat

- 0.1.0 – első telepített verzió
- 0.1.1 – első javítás
- 0.1.2 – további javítás
- 0.2.0 – új funkciók

Külön parancsblokk – első telepítés

cd sudoku-app
kubectl get svc
docker build -t sudoku-app:0.1.0 .
docker save -o sudoku-app_0.1.0.tar sudoku-app:0.1.0
sudo k3s ctr images import sudoku-app_0.1.0.tar
kubectl create configmap sudoku-config \
  --from-literal=APP_PORT=9097 \
  --from-literal=SESSION_BACKEND=redis \
  --from-literal=REDIS_HOST=redis-master \
  --from-literal=REDIS_PORT=6379 \
  --from-literal=SESSION_TTL_SECONDS=86400 \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f k8s/sudoku-app-deployment.yaml
kubectl apply -f k8s/sudoku-app-service.yaml
kubectl rollout status deployment/sudoku-app --timeout=5m

Külön parancsblokk – frissítés

cd sudoku-app
docker build -t sudoku-app:0.1.1 .
docker save -o sudoku-app_0.1.1.tar sudoku-app:0.1.1
sudo k3s ctr images import sudoku-app_0.1.1.tar
kubectl set image deployment/sudoku-app sudoku-app=sudoku-app:0.1.1
kubectl rollout status deployment/sudoku-app --timeout=5m
