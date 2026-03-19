# JARVIS Cluster — Distributed Multi-GPU AI Orchestration

> **EN** | [FR](#version-française)
>
> ![Python](https://img.shields.io/badge/python-3.11+-green)
> ![GPUs](https://img.shields.io/badge/GPUs-5x_NVIDIA-76b900)
> ![Docker](https://img.shields.io/badge/docker-10_containers-blue)
> ![Nodes](https://img.shields.io/badge/nodes-3_machines-orange)
>
> Multi-node, multi-GPU distributed AI orchestration system. 9-step dispatch pipeline, 6-axis quality gates, multi-model consensus, cascade failover, auto-improvement, and GPU thermal monitoring.
>
> **Main node**: M1 "La Creatrice" — AMD Ryzen 7 5700X3D | 5 GPUs | 40GB VRAM | Ubuntu 24.04
>
> ---
>
> ## Table of Contents
>
> 1. [Architecture](#architecture)
> 2. 2. [Cluster Nodes](#cluster-nodes)
>    3. 3. [Dispatch Pipeline (9 steps)](#dispatch-pipeline)
>       4. 4. [Quality Gates (6 axes)](#quality-gates)
>          5. 5. [Failover Cascade](#failover-cascade)
>             6. 6. [Multi-Model Consensus](#multi-model-consensus)
>                7. 7. [Auto-Improvement](#auto-improvement)
>                   8. 8. [Docker Containers (10)](#docker-containers)
>                      9. 9. [Systemd Timers (5)](#systemd-timers)
>                         10. 10. [Routing Matrix (17 domains)](#routing-matrix)
>                             11. 11. [Installation](#installation)
>                                 12. 12. [jarvis-ctl Commands](#jarvis-ctl-commands)
>                                     13. 13. [GPU Thermal Monitoring](#gpu-thermal-monitoring)
>                                         14. 14. [Troubleshooting](#troubleshooting)
>                                             15. 15. [Version Française](#version-française)
>                                                
>                                                 16. ---
>                                                
>                                                 17. ## Architecture
>                                                
>                                                 18. ```
> +=====================================================================+
> |                        JARVIS CLUSTER                               |
> |                                                                     |
> |  +---------------------------------------------------------------+  |
> |  |                    DISPATCH ENGINE                            |  |
> |  |  health > classify > memory > optimize > route               |  |
> |  |  > dispatch > quality gates > feedback > events              |  |
> |  +-----------------------------+---------------------------------+  |
> |                                |                                    |
> |              +-----------------+----------------+                   |
> |              |                 |                |                   |
> |              v                 v                v                   |
> |        +-----------+   +-----------+   +-----------+               |
> |        | M1 (local)|   | M2 (LAN)  |   | M3 (LAN)  |              |
> |        | 5 GPUs    |   | reasoning |   | fallback  |               |
> |        | 40GB VRAM |   |           |   |           |               |
> |        +-----------+   +-----------+   +-----------+               |
> |              |                 |                |                   |
> |              v                 v                v                   |
> |        +-----------+   +-----------+   +-----------+               |
> |        |   OL1     |   |  GEMINI   |   |  CLAUDE   |               |
> |        | (Ollama)  |   |  (API)    |   |  (API)    |               |
> |        +-----------+   +-----------+   +-----------+               |
> |                                                                     |
> |  CIRCUIT BREAKER: 3 failures → skip 60s → auto-retry              |
> |  LOAD BALANCER: adaptive scoring (latency + quality)               |
> +=====================================================================+
> ```
>
> ---
>
> ## Cluster Nodes
>
> | Node | Address | Role | VRAM |
> |------|---------|------|------|
> | **M1 "La Creatrice"** | `127.0.0.1:1234` | Deep analysis — 5 GPUs | 40 GB |
> | **M2** | `192.168.1.26:1234` | Fast inference | 24 GB |
> | **M3** | `192.168.1.113:1234` | General inference / fallback | 8 GB |
> | **OL1** | `127.0.0.1:11434` | Cloud inference (Ollama) | Cloud |
>
> ### M1 Specifications
>
> | Component | Detail |
> |-----------|--------|
> | CPU | AMD Ryzen 7 5700X3D — 16 threads |
> | RAM | 46 GB DDR4 + 12 GB ZRAM |
> | GPU 0 | NVIDIA RTX 3080 — 10 GB GDDR6X |
> | GPU 1 | NVIDIA RTX 2060 — 12 GB GDDR6 |
> | GPU 2-4 | 3x NVIDIA GTX 1660 SUPER — 6 GB each |
> | VRAM Total | 40 GB |
>
> ---
>
> ## Dispatch Pipeline
>
> Each request traverses a complete 9-step sequential pipeline:
>
> ```
> [1. HEALTH CHECK]    → Verify all nodes (latency, GPU temp, availability)
>         |
> [2. CLASSIFY]        → Domain classification (17 routing domains)
>         |
> [3. MEMORY ENRICH]   → Context enrichment from episodic memory
>         |
> [4. PROMPT OPTIMIZE] → Prompt optimization before sending
>         |
> [5. ROUTE]           → Optimal node selection (score + latency + specialization)
>         |
> [6. DISPATCH]        → Send to selected node (with timeout + retry)
>         |
> [7. QUALITY GATES]   → Validate on 6 axes
>         |
> [8. FEEDBACK]        → Scoring, learning, adjustment loop
>         |
> [9. EVENT STREAM]    → Broadcast on event bus (WebSocket, logs, metrics)
> ```
>
> ---
>
> ## Quality Gates
>
> Each response is evaluated on 6 axes before validation:
>
> | Axis | Description |
> |------|-------------|
> | **Length** | Response respects expected size |
> | **Structure** | Coherent format (markdown, lists, code) |
> | **Relevance** | Alignment with original request |
> | **Confidence** | Model confidence score |
> | **Latency** | Response time within acceptable thresholds |
> | **Hallucination** | Detection of fabricated or incoherent content |
>
> Failed quality gates trigger automatic re-dispatch to another node.
>
> ---
>
> ## Failover Cascade
>
> ```
> M1 --fail--> M2 --fail--> OL1 --fail--> M3 --fail--> GEMINI --fail--> CLAUDE
> ```
>
> Circuit breaker per node:
> - 3 consecutive failures → node paused for 60 seconds
> - After delay → node automatically restored
> - Each node has its own independent counter
>
> ---
>
> ## Multi-Model Consensus

For critical requests, the system uses weighted voting across multiple models:

```
M1 + M2 + OL1 (+ GEMINI + CLAUDE for consensus pattern)
    |       |       |
    v       v       v
    +-------+-------+
    | CONSENSUS ENGINE |
    | Weighted vote    |
    | → Consolidated   |
    +------------------+
```

Each node contributes with a weight proportional to its historical reliability score.

---

## Auto-Improvement

### 5 Auto-Action Types

| Action | Description |
|--------|-------------|
| `route_shift` | Move routing to better-performing node |
| `temp_adjust` | Adjust model temperature |
| `tokens_adjust` | Modify max token count |
| `gate_tune` | Fine-tune quality gate thresholds |
| `prompt_enhance` | Automatic prompt improvement |

### Self-Reflection (5 axes)
Quality · Performance · Reliability · Efficiency · Growth

---

## Docker Containers

| # | Container | Port | Role |
|---|-----------|------|------|
| 1 | `jarvis-ws` | 9742 | FastAPI WebSocket Hub |
| 2 | `vocal-engine` | — | Wake word + STT pipeline |
| 3 | `pipeline-engine` | — | Dispatch engine |
| 4 | `domino` | — | 444 learned actions |
| 5 | `openclaw-node` | 28789 | Gateway |
| 6 | `cowork-engine` | — | 477 autonomous scripts |
| 7 | `cowork-dispatcher` | — | COWORK router |
| 8 | `vocal-whisper` | 18001 | GPU STT (Whisper) |
| 9 | `domino-mcp` | 8901 | SSE Bridge |
| 10 | `jarvis-telegram` | — | Remote Telegram Bot |

---

## Systemd Timers

| Timer | Frequency | Role |
|-------|-----------|------|
| `jarvis-health` | Every 15 min | Cluster health check |
| `jarvis-backup` | Daily | Data + config backup |
| `jarvis-thermal` | Every 5 min | GPU thermal monitoring |
| `jarvis-log-rotate` | Weekly | Log rotation |
| `jarvis-pipeline-check` | Every 10 min | Pipeline dispatch check |

---

## Routing Matrix

17 domains managed by the adaptive router — each request routed based on: node specialization, measured latency, historical quality score, current GPU load, GPU temperature.

| Domain | Primary Nodes |
|--------|--------------|
| `code_generation` | M1, GEMINI, M2 |
| `reasoning` | M1, M2, OL1 |
| `trading_signal` | OL1, M1, GEMINI |
| `vision` | GEMINI |
| `consensus` | M1, M2, OL1, M3, GEMINI, CLAUDE |
| `web_research` | GEMINI, OL1, M1 |
| `architecture` | GEMINI, CLAUDE, M1 |

---

## Installation

### Prerequisites
- Linux (tested on Ubuntu/Arch)
- - Docker + Docker Compose
  - - NVIDIA drivers + NVIDIA Container Toolkit
    - - Python 3.11+
      - - At least 1 NVIDIA GPU
       
        - ### Quick Start
       
        - ```bash
          git clone https://github.com/Turbo31150/JARVIS-CLUSTER.git
          cd JARVIS-CLUSTER

          # Full installation
          bash projects/linux/install.sh

          # Docker deployment
          cd projects/linux
          docker compose up -d

          # Verify status
          docker compose ps
          ```

          ---

          ## jarvis-ctl Commands

          ```bash
          bash projects/linux/jarvis-ctl.sh start    # Start all services
          bash projects/linux/jarvis-ctl.sh stop     # Stop all services
          bash projects/linux/jarvis-ctl.sh restart  # Restart
          bash projects/linux/jarvis-ctl.sh status   # Cluster state
          bash projects/linux/jarvis-ctl.sh logs     # View logs
          bash projects/linux/jarvis-ctl.sh health   # Full health check
          ```

          ---

          ## GPU Thermal Monitoring

          | Temperature | Status | Action |
          |-------------|--------|--------|
          | < 75°C | Normal | Standard operation |
          | 75-85°C | Warning | Alert, load reduction |
          | > 85°C | Critical | Auto-reroute to cooler node |

          The `jarvis-thermal` timer checks every 5 minutes. On critical overheat, dispatch engine automatically reroutes to a cooler node.

          ---

          ## Troubleshooting

          | Symptom | Solution |
          |---------|----------|
          | Node not responding | `curl -s http://<addr>:<port>/health` then check circuit breaker |
          | GPU temperature too high | `nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader` — system reroutes above 85°C |
          | Container not starting | `docker compose logs <container>` |
          | Pipeline blocked | `bash jarvis-ctl.sh restart` — timer checks every 10 min |
          | OL1 offline | `ollama serve` |

          ---

          ## Related Repos

          | Repo | Description |
          |------|-------------|
          | [jarvis-linux](https://github.com/Turbo31150/jarvis-linux) | Main repo — full OS deployment |
          | [turbo](https://github.com/Turbo31150/turbo) | JARVIS Etoile v12.4 — 602 MCP handlers |
          | [jarvis-cowork](https://github.com/Turbo31150/jarvis-cowork) | 249 autonomous development scripts |

          ---

          *Author: Turbo31150 | Platform: Linux x86_64 | Architecture: Distributed Multi-GPU AI | March 2026*

          ---
          ---

          # Version Française

          > [EN](#jarvis-cluster--distributed-multi-gpu-ai-orchestration) | **FR**
          >
          > ![Python](https://img.shields.io/badge/python-3.11+-green)
          > ![GPUs](https://img.shields.io/badge/GPUs-5x_NVIDIA-76b900)
          > ![Docker](https://img.shields.io/badge/docker-10_conteneurs-blue)
          > ![Noeuds](https://img.shields.io/badge/noeuds-3_machines-orange)
          >
          > Système d'orchestration IA distribué multi-GPU et multi-nœuds. Pipeline de dispatch 9 étapes, quality gates 6 axes, consensus multi-modèle, failover en cascade, auto-amélioration et monitoring thermique GPU.
          >
          > **Nœud principal** : M1 "La Creatrice" — AMD Ryzen 7 5700X3D | 5 GPUs | 40GB VRAM | Ubuntu 24.04
          >
          > ---
          >
          > ## Table des matières FR
          >
          > 1. [Architecture](#architecture-fr)
          > 2. 2. [Nœuds du cluster](#nœuds-du-cluster)
          >    3. 3. [Pipeline de dispatch (9 étapes)](#pipeline-de-dispatch)
          >       4. 4. [Quality Gates (6 axes)](#quality-gates-fr)
          >          5. 5. [Cascade de failover](#cascade-de-failover)
          >             6. 6. [Consensus multi-modèle](#consensus-multi-modèle)
          >                7. 7. [Auto-amélioration](#auto-amélioration)
          >                   8. 8. [Conteneurs Docker (10)](#conteneurs-docker-fr)
          >                      9. 9. [Timers systemd (5)](#timers-systemd)
          >                         10. 10. [Matrice de routage (17 domaines)](#matrice-de-routage)
          >                             11. 11. [Installation](#installation-fr)
          >                                 12. 12. [Commandes jarvis-ctl](#commandes-jarvis-ctl)
          >                                     13. 13. [Monitoring thermique GPU](#monitoring-thermique-gpu)
          >                                         14. 14. [Dépannage](#dépannage)
          >                                            
          >                                             15. ---
          >                                            
          >                                             16. ## Architecture FR
          >                                            
          >                                             17. ```
          > +=====================================================================+
          > |                        JARVIS CLUSTER                               |
          > |                                                                     |
          > |  +---------------------------------------------------------------+  |
          > |  |                    DISPATCH ENGINE                            |  |
          > |  |  santé > classifier > mémoire > optimiser > router           |  |
          > |  |  > dispatcher > quality gates > feedback > événements        |  |
          > |  +-----------------------------+---------------------------------+  |
          > |                                |                                    |
          > |              +-----------------+----------------+                   |
          > |              |                 |                |                   |
          > |        M1 (local)         M2 (LAN)         M3 (LAN)                |
          > |        5 GPUs 40GB        reasoning         fallback                |
          > |              |                 |                |                   |
          > |        OL1 (Ollama)       GEMINI (API)    CLAUDE (API)             |
          > |                                                                     |
          > |  CIRCUIT BREAKER: 3 échecs → pause 60s → retry auto               |
          > |  LOAD BALANCER: scoring adaptatif (latence + qualité)              |
          > +=====================================================================+
          > ```
          >
          > ---
          >
          > ## Nœuds du cluster
          >
          > | Nœud | Adresse | Rôle | VRAM |
          > |------|---------|------|------|
          > | **M1 "La Creatrice"** | `127.0.0.1:1234` | Deep analysis — 5 GPUs | 40 GB |
          > | **M2** | `192.168.1.26:1234` | Inference rapide | 24 GB |
          > | **M3** | `192.168.1.113:1234` | Inference générale / fallback | 8 GB |
          > | **OL1** | `127.0.0.1:11434` | Inference cloud (Ollama) | Cloud |
          >
          > ### Spécifications M1
          >
          > | Composant | Détail |
          > |-----------|--------|
          > | CPU | AMD Ryzen 7 5700X3D — 16 threads |
          > | RAM | 46 GB DDR4 + 12 GB ZRAM |
          > | GPU 0 | NVIDIA RTX 3080 — 10 GB GDDR6X |
          > | GPU 1 | NVIDIA RTX 2060 — 12 GB GDDR6 |
          > | GPU 2-4 | 3x NVIDIA GTX 1660 SUPER — 6 GB chacun |
          > | VRAM Total | 40 GB |
          >
          > ---
          >
          > ## Pipeline de dispatch
          >
          > Chaque requête traverse un pipeline complet en 9 étapes séquentielles :
          >
          > ```
          > [1. HEALTH CHECK]      → Vérification santé de tous les nœuds
          > [2. CLASSIFIER]        → Classification du domaine (17 domaines)
          > [3. MEMORY ENRICH]     → Enrichissement mémoire épisodique
          > [4. PROMPT OPTIMIZE]   → Optimisation du prompt avant envoi
          > [5. ROUTE]             → Sélection du nœud optimal
          > [6. DISPATCH]          → Envoi avec timeout + retry
          > [7. QUALITY GATES]     → Validation sur 6 axes
          > [8. FEEDBACK]          → Boucle scoring, apprentissage, ajustement
          > [9. EVENT STREAM]      → Diffusion bus d'événements (WS, logs, métriques)
          > ```
          >
          > ---
          >
          > ## Quality Gates FR
          >
          > | Axe | Description |
          > |-----|-------------|
          > | **Longueur** | La réponse respecte la taille attendue |
          > | **Structure** | Format cohérent (markdown, listes, code) |
          > | **Pertinence** | Adéquation avec la requête originale |
          > | **Confiance** | Score de confiance du modèle |
          > | **Latence** | Temps de réponse dans les seuils acceptables |
          > | **Hallucination** | Détection de contenu fabriqué ou incohérent |
          >
          > ---
          >
          > ## Cascade de failover
          >
          > ```
          > M1 --échec--> M2 --échec--> OL1 --échec--> M3 --échec--> GEMINI --échec--> CLAUDE
          > ```
          >
          > Circuit breaker par nœud : 3 échecs consécutifs → pause 60s → remise en service auto.
          >
          > ---
          >
          > ## Consensus multi-modèle
          >
          > Pour les requêtes critiques, vote pondéré entre plusieurs modèles. Chaque nœud contribue avec un poids proportionnel à son score de fiabilité historique.
          >
          > ---
          >
          > ## Auto-amélioration
          >
          > ### 5 types d'auto-actions
          >
          > | Action | Description |
          > |--------|-------------|
          > | `route_shift` | Déplacement du routage vers un nœud plus performant |
          > | `temp_adjust` | Ajustement de la température du modèle |
          > | `tokens_adjust` | Modification du nombre de tokens max |
          > | `gate_tune` | Affinage des seuils des quality gates |
          > | `prompt_enhance` | Amélioration automatique des prompts |
          >
          > ---
          >
          > ## Conteneurs Docker FR
          >
          > | # | Conteneur | Port | Rôle |
          > |---|-----------|------|------|
          > | 1 | `jarvis-ws` | 9742 | Hub WebSocket FastAPI |
          > | 2 | `vocal-engine` | — | Wake word + pipeline STT |
          > | 3 | `pipeline-engine` | — | Moteur de dispatch |
          > | 4 | `domino` | — | 444 actions apprises |
          > | 5 | `openclaw-node` | 28789 | Gateway |
          > | 6 | `cowork-engine` | — | 477 scripts autonomes |
          > | 7 | `cowork-dispatcher` | — | Routeur COWORK |
          > | 8 | `vocal-whisper` | 18001 | STT GPU (Whisper) |
          > | 9 | `domino-mcp` | 8901 | Bridge SSE |
          > | 10 | `jarvis-telegram` | — | Bot Telegram distant |
          >
          > ---
          >
          > ## Timers systemd
          >
          > | Timer | Fréquence | Rôle |
          > |-------|-----------|------|
          > | `jarvis-health` | Toutes les 15 min | Vérification santé cluster |
          > | `jarvis-backup` | Quotidien | Sauvegarde données + configs |
          > | `jarvis-thermal` | Toutes les 5 min | Surveillance thermique GPU |
          > | `jarvis-log-rotate` | Hebdomadaire | Rotation des logs |
          > | `jarvis-pipeline-check` | Toutes les 10 min | Vérification pipeline dispatch |
          >
          > ---
          >
          > ## Matrice de routage
          >
          > 17 domaines — routage basé sur : spécialisation, latence mesurée, score qualité historique, charge GPU, température GPU.
          >
          > | Domaine | Nœuds principaux |
          > |---------|-----------------|
          > | `code_generation` | M1, GEMINI, M2 |
          > | `reasoning` | M1, M2, OL1 |
          > | `trading_signal` | OL1, M1, GEMINI |
          > | `vision` | GEMINI |
          > | `consensus` | M1, M2, OL1, M3, GEMINI, CLAUDE |
          > | `web_research` | GEMINI, OL1, M1 |
          >
          > ---
          >
          > ## Installation FR
          >
          > ### Prérequis
          > - Linux (testé sur Ubuntu/Arch)
          > - Docker + Docker Compose
          > - Drivers NVIDIA + NVIDIA Container Toolkit
          > - Python 3.11+
          > - Au moins 1 GPU NVIDIA
          >
          > ### Démarrage rapide
          >
          > ```bash
          > git clone https://github.com/Turbo31150/JARVIS-CLUSTER.git
          > cd JARVIS-CLUSTER
          >
          > # Installation complète
          > bash projects/linux/install.sh
          >
          > # Déploiement Docker
          > cd projects/linux
          > docker compose up -d
          >
          > # Vérifier le statut
          > docker compose ps
          > ```
          >
          > ---
          >
          > ## Commandes jarvis-ctl
          >
          > ```bash
          > bash projects/linux/jarvis-ctl.sh start    # Démarrer tous les services
          > bash projects/linux/jarvis-ctl.sh stop     # Arrêter tous les services
          > bash projects/linux/jarvis-ctl.sh restart  # Redémarrer
          > bash projects/linux/jarvis-ctl.sh status   # État du cluster
          > bash projects/linux/jarvis-ctl.sh logs     # Voir les logs
          > bash projects/linux/jarvis-ctl.sh health   # Health check complet
          > ```
          >
          > ---
          >
          > ## Monitoring thermique GPU
          >
          > | Température | Statut | Action |
          > |-------------|--------|--------|
          > | < 75°C | Normal | Fonctionnement standard |
          > | 75-85°C | Warning | Alerte, réduction de charge |
          > | > 85°C | Critique | Re-routage automatique vers nœud plus froid |
          >
          > ---
          >
          > ## Dépannage
          >
          > | Symptôme | Solution |
          > |----------|----------|
          > | Nœud ne répond pas | `curl -s http://<addr>:<port>/health` + vérifier circuit breaker |
          > | GPU trop chaud | `nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader` |
          > | Container ne démarre pas | `docker compose logs <container>` |
          > | Pipeline bloqué | `bash jarvis-ctl.sh restart` |
          > | OL1 hors ligne | `ollama serve` |
          >
          > ---
          >
          > ## Repos liés
          >
          > | Repo | Description |
          > |------|-------------|
          > | [jarvis-linux](https://github.com/Turbo31150/jarvis-linux) | Repo principal — déploiement OS complet |
          > | [turbo](https://github.com/Turbo31150/turbo) | JARVIS Etoile v12.4 — 602 MCP handlers |
          > | [jarvis-cowork](https://github.com/Turbo31150/jarvis-cowork) | 249 scripts de développement autonome |
          >
          > ---
          >
          > *Auteur : Turbo31150 | Plateforme : Linux x86_64 | Architecture : IA Multi-GPU Distribuée | Mars 2026*
