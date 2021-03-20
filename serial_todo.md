# Da server a Teensy

- Ciao, chi sei? `>C`, risposta corretta `C4b7caa5d-2634-44f3-ad62-5ffb1e08d73f`
- Avanti di tot metri: `>M[metri]%`
- Avanti tutta fino stop: `>m%`
- Velocità max motori: `>V[pwm]%`
- Velocità max motori metri/s: `>v[metri al secondo]%`
- Ruota: `>A[gradi]%`, gradi rispetto al nord [-180°,180°]
- Avanti con rotazione: `>W[metri]%[gradi]%`
- Stop: `>S`

# Da Teensy a server

Inviati ciclicamente ogni tot millisecondi

- Accelerometro: `A[x]%[y]%[z]%`
- Giroscopio: `G[x]%[y]%[z]%`
- Magnetometro: `M[x]%[y]%[z]%`
- Temperatura: `T[gradi]%`
- Batteria: `B[volt]%`
- Log: qualunque cosa che inizia con `L`