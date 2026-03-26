# Truco Uruguayo con Aprendizaje por Refuerzo

Un proyecto de inteligencia artificial en Python que entrena a un agente para jugar al Truco Uruguayo. El agente aprende de sus propias experiencias de juego mediante técnicas de aprendizaje por refuerzo.

## Estructura del proyecto

- **`truco_rl/`**: Carpeta principal con todo el código
  - `Card.py`: Define la estructura de las cartas
  - `Game.py` y `truco_engine.py`: Implementan las reglas del juego
  - `truco_env.py`: El entorno de juego que interactúa con el agente de IA
  - `train.py` y `train_enhanced.py`: Scripts para entrenar el agente
  - `play_with_trained_agent.py`: Permite jugar contra el agente entrenado
  - `demo_entrenamiento.py`: Demuestra el proceso de entrenamiento

## Cómo empezar

### Requisitos
- Python 3.7 o superior
- Las librerías necesarias (se instalan automáticamente)

### Entrenar un nuevo agente

Para entrenar un agente desde cero, ejecuta:
```
python -m truco_rl.train_enhanced
```

Este proceso puede tomar un tiempo mientras el agente juega miles o millones de partidas para aprender.

### Jugar contra un agente entrenado

Una vez que tengas al agente entrenado:
```
python -m truco_rl.play_with_trained_agent
```

## ¿Cómo funciona?

1. El agente comienza sin conocimientos
2. Juega partidas contra sí mismo o contra oponentes
3. Recibe recompensas positivas por ganar y negativas por perder
4. Utiliza estas recompensas para ajustar su estrategia
5. Después de muchas partidas, desarrolla una estrategia efectiva
