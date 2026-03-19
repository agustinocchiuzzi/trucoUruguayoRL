# 🚀 PRÓXIMOS PASOS - Entrenar el Agente de RL

## 📋 Hoja de Ruta

### Fase 1: Testing Actual (HECHO)
- [x] Flujo correcto de turnos implementado
- [x] Agente básico con decisiones aleatorias
- [x] Jugar contra el agente funcionando
- **PRÓXIMO**: Validar flujo jugando varias sesiones

### Fase 2: Mejora de Lógica (PRÓXIMA)
- [ ] Agente evalúa su posición antes de responder
- [ ] Calcula probabilidades simples de ganar
- [ ] Mejora en selección de cartas
- Tiempo estimado: 1-2 horas

### Fase 3: Entrenamiento RL (LONG-TERM)
- [ ] Usar `truco_env.py` como entorno
- [ ] Entrenar con PPO (stable-baselines3)
- [ ] Almacenar modelo entrenado
- Tiempo estimado: 24-48 horas de entrenamiento

### Fase 4: Self-Play (ADVANCED)
- [ ] Cargar 2 modelos entrenados
- [ ] Jugarlos uno contra otro
- [ ] Mejorar iterativamente
- Tiempo estimado: 1 semana+

---

## 🔧 Fase 2 - Mejora de Lógica (HOY)

### Archivo: `truco_rl/agent_improved.py` (crear nuevo)

```python
class ImprovedAgent:
    """Agente con lógica mejorada (no RL aún)"""
    
    def decide_action(self, truco):
        player = 0
        
        # PRIORIDAD 1: Responder cantos
        if self._should_respond_truco(truco, player):
            return self._smart_respond_truco(truco, player)
        
        if self._should_respond_envido(truco, player):
            return self._smart_respond_envido(truco, player)
        
        if self._should_respond_flower(truco, player):
            return self._smart_respond_flower(truco, player)
        
        # PRIORIDAD 2: Mi turno - decidir si cantar o jugar
        if truco.turn == player and not truco.hand_over:
            hand = truco.hand_of(player)
            
            # Si tengo flor fuerte, cancelo canto rival si puedo
            if player in truco.flowers_declared and not truco.flower_resolved:
                own_flower = truco.flower_value_of(player)
                if own_flower > 35:  # flor fuerte
                    return ('call_flower', 'la_mia')
            
            # Si tengo buen envido, canto
            env = truco.envido_of(player)
            if env != -1 and env > 28 and not truco.envido_state:
                return ('call_envido', 'envido')
            
            # Sino, juego carta estratégicaggg
            return self._play_smart_card(truco, player)
    
    def _smart_respond_envido(self, truco, player):
        """Responde al envido evaluando probabilidades"""
        own_env = truco.envido_of(player)
        rival_env = truco.envido_of(1 - player)
        
        # Si tengo flor, SIEMPRE no quiero
        if own_env == -1:
            return ('respond_envido', 'no_quiero')
        
        # Si voy ganando bastante, quiero
        if own_env > rival_env + 3:
            return ('respond_envido', 'quiero')
        
        # Si voy perdiendo, no quiero
        if own_env < rival_env - 3:
            return ('respond_envido', 'no_quiero')
        
        # Si es cercano, 50/50
        return ('respond_envido', 'quiero' if random.random() < 0.5 else 'no_quiero')
    
    def _play_smart_card(self, truco, player):
        """Selecciona carta más estratégica"""
        hand = truco.hand_of(player)
        
        if not truco.played[player]:  # Primera carta de la baza
            # Juega la más baja para ahorrar
            return ('play_card', self._weakest_card(hand, truco.sample))
        
        else:  # Respondiendo cartas del rival
            last_rival = truco.played[1 - player][-1]
            rival_value = last_rival.value(truco.sample)
            
            # Si puedo ganar con poco, gano
            winning_card = self._lowest_winning_card(hand, rival_value, truco.sample)
            if winning_card is not None:
                return ('play_card', winning_card)
            
            # Sino, juego la más baja
            return ('play_card', self._weakest_card(hand, truco.sample))
    
    def _weakest_card(self, hand, sample):
        """Retorna índice de la carta más débil"""
        min_idx = 0
        for i in range(1, len(hand)):
            if hand[i].value(sample) < hand[min_idx].value(sample):
                min_idx = i
        return min_idx
    
    def _lowest_winning_card(self, hand, rival_value, sample):
        """Retorna índice de la carta ganadora más baja, o None"""
        candidates = [
            i for i in range(len(hand))
            if hand[i].value(sample) > rival_value
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda i: hand[i].value(sample))
```

### Cómo Integrar:

1. Copiar `ImprovedAgent` a `Main.py`
2. Cambiar `agent = RLAgent()` → `agent = ImprovedAgent()`
3. Probar varias sesiones
4. Ajustar umbrales (28, 35, etc.)

---

## 🧠 Fase 3 - Entrenamiento con RL

### Verificar que existe:
```bash
cat truco_env.py
```

### Crear script de entrenamiento: `train_agent.py`

```python
from stable_baselines3 import PPO
from truco_env import TrucoEnv
import os

# Crear entorno
env = TrucoEnv(opponent="random")

# Crear modelo
model = PPO(
    "MlpPolicy",
    env,
    learning_rate=1e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    verbose=1
)

# Entrenar
model.learn(total_timesteps=500_000)

# Guardar
model.save("./models/ppo_agent_v1")
print("✓ Modelo guardado en ./models/ppo_agent_v1")
```

### Ejecución:
```bash
mkdir models
python train_agent.py
```

### Tiempo estimado:
- Máquina normal: 2-4 horas
- GPU: 30-60 minutos

---

## 🎮 Fase 4 - Usar Modelo Entrenado

### Modificar `Main.py`:

```python
from stable_baselines3 import PPO

class TrainedRLAgent:
    def __init__(self, model_path="./models/ppo_agent_v1"):
        self.model = PPO.load(model_path)
    
    def decide_action(self, truco):
        # Convertir estado a observación
        obs = ... # compatibilidad con truco_env.py
        action, _ = self.model.predict(obs, deterministic=False)
        # Convertir acción a formato legible
        return self._action_to_command(action)
```

### Cambiar en play_hand():
```python
# agent = RLAgent()  # ← Cambiar esto
agent = TrainedRLAgent("./models/ppo_agent_v1")
```

---

## 📊 Métrica de Progreso

```python
# Agregar al final de play_hand():
stats = {
    'agent_wins': 0,
    'human_wins': 0,
    'avg_points_per_hand': 0
}

# Guardaría en stats.json
```

---

##  ⚡️ Optimizaciones Futuras

### 1. **Double DQN** (Más estable)
```python
from stable_baselines3 import DQN
model = DQN("MlpPolicy", env)
```

### 2. **Multi-Agent** (Self-Play)
```python
# 2 agentes propios jugando entre sí
env_self = TrucoEnvSelfPlay(agent1_model, agent2_model)
```

### 3. **Curriculum Learning**
```python
# Entrenar primero contra principiante
# Luego contra medio
# Luego contra experto
```

### 4. **Imitation Learning**
```python
# Aprender de un jugador experto humano
# Agent observa movimientos óptimos
```

---

## 🎯 Checklist de Validación

Antes de entrenar, verifica que:

- [ ] Flujo de turnos funciona perfecto
- [ ] No hay bugs en respuestas
- [ ] Agente simple juega completo
- [ ] `truco_env.py` funciona
- [ ] stable-baselines3 instalado (`pip install stable-baselines3`)
- [ ] Carpeta `models/` existe

---

## 📝 Notas Técnicas

### Estado del Entorno (`truco_env.py`)
- **Observación** (135 features): cartas, puntos, estado cantos, etc.
- **Acciones** (11 posibles): jugar carta, envido, truco, etc.
- **Recompensa**: +1 si gana mano, -1 si pierde

### Hiperparámetros Recomendados
```python
PPO(
    learning_rate=1e-4,      # Aprendizaje lento = más estable
    n_steps=2048,            # Experiencias antes de actualizar
    batch_size=64,           # Tamaño del batch
    n_epochs=10,             # Actualizaciones por batch
    gamma=0.99,              # Descuento futuro
    gae_lambda=0.95          # GAE lambda
)
```

---

## 🔗 Referencias

- **Stable-Baselines3**: https://stable-baselines3.readthedocs.io
- **OpenAI Gym**: https://gymnasium.farama.org
- **PPO Paper**: https://arxiv.org/abs/1707.06347

---

**Última actualización**: 19 de Marzo, 2026
