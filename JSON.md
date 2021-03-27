# Pacchetti JSON

## Rover > client

- `updateAccel: [x, y, z]`
  - `xyz`: array di 3 float
- `updateGyro: [x, y, z]`
  - `xyz`: array di 3 float
- `updateMagn: [x, y, z]`
  - `xyz`: array di 3 float
- `updateIrDistance: [dist1, dist2]`
  - `dist`: float
- `updateBatt: val`
  - `val`: percentuale int
- `updateCpuTemp: val`
  - `val`: temperatura float
- `updateRPMFeedback: val`
  - `val`: rpm motori
- `setMLEnabled: val`
  - _Avvia modalità automatica machine learning_
  - `val`: boolean, attivo o no

## Client > rover

- `move: dist`
  - _Movimento avanti con distanza_
  - `dist`: in metri
- `moveTime: ms`
  - Muoviti per tot millisecondi
- `setSpeed: speed`
  - `speed`: metri al secondo
- `moveRotate: [dist, degPerMin]`
  - `dist`: distanza in metri
  - `degPerMin`: gradi al minuto di rotazione (velocità), intero, negativo per antiorario
- `rotate: angle`
  - _Rotazione del rover su se stesso_
  - `angle`: int da -180 a 180
- `stop: true`
  - _Ferma i movimenti continui_
- `setMLEnabled: val`
  - _Avvia modalità automatica machine learning_
  - `val`: boolean, attivo o no
