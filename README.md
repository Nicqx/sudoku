# Sudoku

Flask/Gunicorn alapú Sudoku, Redis sessiontárolással. Erőforrások: `sudoku-app` Deployment és Service (`9097`); publikus útvonal: `/sudoku/`.

## Telepítés és frissítés

Előfeltétel: Docker, Git, Bash, működő k3s, Redis és ingress.

```bash
cd ~/codes/sudoku
git pull --ff-only
KUBECTL='sudo k3s kubectl' ./update.sh --target nuc --dry-run
KUBECTL='sudo k3s kubectl' ./update.sh --target nuc
```

A script natív image-et épít/importál, alkalmazza a manifestet és megvárja a rolloutot. Manifestmentések: `~/.local/state/nicqx-apps/nuc/sudoku-app/`.

## Ellenőrzés

```bash
sudo k3s kubectl get pod,service -n default -l app=sudoku-app -o wide
sudo k3s kubectl logs deployment/sudoku-app -n default --tail=50
curl -fsSI https://pmqxyz.hopto.org/sudoku/ | head -n 1
```

## Migráció

A konténer állapotmentes. Előbb a `redis` repo eljárásával migráld a játékadatokat (az új kód `sudoku:session` prefixet használ és a régi formátumot is olvassa), majd klónozd ezt a repót és futtasd az update-et. Külön PVC nincs.

## Leállítás, rollback, eltávolítás

```bash
sudo k3s kubectl scale deployment/sudoku-app -n default --replicas=0
sudo k3s kubectl scale deployment/sudoku-app -n default --replicas=1
sudo k3s kubectl apply -f /teljes/ut/korabbi-manifest.yaml
sudo k3s kubectl rollout status deployment/sudoku-app -n default --timeout=180s
sudo k3s kubectl delete deployment/sudoku-app service/sudoku-app -n default
```

Az eltávolítás nem töröl Redis-adatot vagy az `ingress` repo által kezelt szabályt. Redis-kulcsot csak mentés után törölj.
