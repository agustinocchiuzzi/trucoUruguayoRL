# 🚀 COMANDOS RÁPIDOS - ENTRENAMIENTO RL

## 🎯 Inicio Rápido (5 minutos)

### 1. Ver cómo funciona el entrenamiento
```bash
cd truco_rl
python demo_entrenamiento.py
```
**Resultado**: Te muestra un entrenamiento de 10k timesteps en ~2 minutos.

---

## 🔥 Entrenamientos Principales

### 2. Entrenar modelo pequeño (30 minutos)
```bash
python train_enhanced.py --steps 50000 --nombre mi_agente_50k
```
**Salida**: Archivo `mi_agente_50k.zip` con Win Rate ~55-60%

### 3. Entrenar modelo mediano (1 hora)
```bash
python train_enhanced.py --steps 100000 --nombre mi_agente_100k
```
**Salida**: Archivo `mi_agente_100k.zip` con Win Rate ~60-65%

### 4. Entrenar modelo bueno (2 horas)
```bash
python train_enhanced.py --steps 250000 --nombre mi_agente_250k
```
**Salida**: Archivo `mi_agente_250k.zip` con Win Rate ~65-70%

### 5. Entrenar modelo excelente (3-4 horas)
```bash
python train_enhanced.py --steps 500000 --nombre mi_agente_500k
```
**Salida**: Archivo `mi_agente_500k.zip` con Win Rate ~70-75%

---

## 📊 Evaluación y Testing

### Ver progreso después del entrenamiento
```bash
python train_enhanced.py --eval-only mi_agente_100k --n-eval 500
```
**Resultado**: Tabla detallada con Win Rate, victorias, derrotas, empates.

### Comparar dos modelos
```bash
# Modelo 1
python train_enhanced.py --eval-only agente_v1 --n-eval 500

# Modelo 2
python train_enhanced.py --eval-only agente_v2 --n-eval 500
```
**Resultado**: El que tenga mayor Win Rate es mejor.

---

## 🎮 Jugar

### Jugar contra el agente entrenado
```bash
python play_with_trained_agent.py --model mi_agente_100k
```
**Resultado**: Interfaz interactiva para jugar contra el modelo.

### Jugar contra agente aleatorio (original)
```bash
python Main.py
```
**Resultado**: Juego normal.

---

## 🔄 Self-Play (Avanzado)

### Entrenar generación 2 contra generación 1
```bash
# Primero entrena v1
python train_enhanced.py --steps 100000 --nombre agent_v1

# Luego entrena v2 contra v1
python train_enhanced.py --selfplay agent_v1 --steps 100000
```

### Entrenar generación 3 contra generación 2
```bash
python train_enhanced.py --selfplay agent_v2 --steps 100000
```

---

## 📈 Monitoreo en Tiempo Real

### Durante entrenamiento
Se actualiza cada 20,000 timesteps automáticamente:
```
📊 PROGRESO
   Timesteps:      20,000
   Manos jugadas:      640
   Victorias:         380
   Win Rate:        59.4%
```

### Ver en TensorBoard (no obligatorio)
```bash
tensorboard --logdir=./logs
# Abre: http://localhost:6006
```

---

## 🗂️ Gestión de Archivos

### Listar modelos guardados
```bash
dir *.zip
```

### Renombrar modelo
```bash
ren antiguo_nombre.zip nuevo_nombre.zip
```

### Eliminar modelo
```bash
del nombre_modelo.zip
```

---

## 🎯 Plan de Entrenamiento Recomendado

### Día 1: Exploración (30 minutos total)
```bash
# Entrenar 3 versiones pequeñas
python train_enhanced.py --steps 50000 --nombre v1_50k
python train_enhanced.py --steps 50000 --nombre v2_50k
python train_enhanced.py --steps 100000 --nombre v3_100k
```

### Día 2: Mejora (1-2 horas)
```bash
# Evaluar cuál es mejor
python train_enhanced.py --eval-only v1_50k --n-eval 500
python train_enhanced.py --eval-only v3_100k --n-eval 500

# Entrenar el mejor más
python train_enhanced.py --steps 250000 --nombre best_250k
```

### Día 3: Self-Play (1-2 horas, opcional)
```bash
# Mejorar aún más contra sí mismo
python train_enhanced.py --selfplay best_250k --steps 250000
```

---

## 📊 Tabla de Referencia

| Comando | Tiempo | Win Rate | Uso |
|---------|--------|----------|-----|
| `demo_entrenamiento.py` | 2 min | ~50% | Entender cómo funciona |
| `--steps 50000` | 30 min | 55-60% | Primer modelo rápido |
| `--steps 100000` | 60 min | 60-65% | Modelo bueno |
| `--steps 250000` | 2 horas | 65-70% | Modelo muy bueno |
| `--steps 500000` | 4 horas | 70-75% | Modelo excelente |
| `--steps 1000000` | 8 horas | 75%+ | Modelo maestro |

---

## 🆘 Problemas Comunes

### "No module named 'stable_baselines3'"
```bash
pip install stable-baselines3 gymnasium
```

### El training es muy lento
```bash
# Reducir timesteps para testing
python train_enhanced.py --steps 10000 --nombre test
```

### Win Rate no mejora
```bash
# Entrenar más (mínimo 100k)
python train_enhanced.py --steps 100000 --nombre agente
```

### No puedo jugar contra el modelo
```bash
# Asegúrate que el archivo existe y está en truco_rl/
dir mi_agente_100k.zip  # o ls mi_agente_100k.zip en Linux
```

---

## 📚 Leer Más

**Guía completa**: `GUIA_ENTRENAMIENTO_RL.md`
- Conceptos básicos de RL
- Hiperparámetros explicados
- Self-play detallado
- Troubleshooting avanzado

---

## 💡 Tips Pro

1. **Guardar checkpoints**: Entrenar en etapas (50k → 100k → 250k → 500k)
2. **Self-play es poderoso**: Produce agentes mucho más fuertes
3. **Evaluar frecuentemente**: Ver progreso motiva a seguir
4. **Documentar**: Guardar qué parámetros usaste para cada modelo
5. **Experimento**: Cambiar learning_rate de 3e-4 a 1e-4 o 5e-4 para ver qué funciona

---

## 🎓 Aprender Más

- **Stable-baselines3**: https://stable-baselines3.readthedocs.io/
- **PPO**: https://arxiv.org/abs/1707.06347
- **Gymnasium**: https://gymnasium.farama.org/

---

**¡Diviértete entrenando!** 🚀
