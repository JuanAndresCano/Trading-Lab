# Responsabilidades

| Archivo        | Qué hace                                                                      | Qué no hace                 |
| -------------- | ----------------------------------------------------------------------------- | --------------------------- |
| events.py      | Define mensajes del sistema sei.cmu                                           | No calcula señales ni PnL   |
| event_queue.py | Mueve eventos en orden vertoxquant                                            | No decide trading           |
| runner.py      | Coordina el flujo total quantstart                                            | No implementa estrategia    |
| loader.py      | Entrega datos al motor quantstart                                             | No analiza mercado          |
| base.py        | Define contrato común de estrategias users.exa.unicen.edu $+1$                | No contiene lógica concreta |
| mark2.py       | Implementa tu estrategia baseline quantjourney.substack                       | No guarda resultados        |
| portfolio.py   | Administra posiciones/capital y transforma señales en órdenes quantstart $+1$ | No carga datos              |
| simulator.py   | Simula ejecución realista interactivebrokers $+ 1$                            | No decide si entrar o no    |
