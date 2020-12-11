# Interfacce di programmazione

## Metodi che il Socket chiama per aggiornare GUI e ML

- `updateAccel(xyz)`
  - `xyz`: array di 3 float
- `updateGyro(xyz)`
  - `xyz`: array di 3 float
- `updateMagn(xyz)`
  - `xyz`: array di 3 float
- `updateIrDistance(dist1, dist2)`
  - `dist`: float
- `updateBatt(val)`
  - `val`: percentuale int
- `updateCpuTemp(val)`
  - `val`: temperatura float
- `updateRPMFeedback(val)`
  - `val`: rpm motori
- `setMLEnabled(val)`
  - _Avvia modalità automatica machine learning_
  - `val`: boolean, attivo o no

## Metodi che la GUI e il ML possono chiamare nel Socket

- `connect(ip)`
  - _Connetti il client_
  - `ip`: stringa
  - return boolean successo
- `disconnect()`
  - _Disconnetti client_
- `isConnected()`
  - return boolean valore
- `move(speed)`
  - _Movimento avanti continuo fino a stop_
  - `speed`: PWM (0-255), intero
- `moveRotate(speed, degPerMin)`
  - _Movimento combinato continuo fino a stop_
  - `speed`: PWM (0-255), intero, negativo per indietro
  - `degPerMin`: gradi al minuto di rotazione (velocità), intero, negativo per antiorario
- `rotate(angle)`
  - _Rotazione del rover su se stesso_
  - `angle`: int da -180 a 180
- `stop()`
  - _Ferma i movimenti continui_
- `setMLEnabled(val)`
  - _Avvia modalità automatica machine learning_
  - `val`: boolean, attivo o no
