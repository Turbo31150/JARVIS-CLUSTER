
<img src="assets/gemini-generated-1.png" alt="JARVIS-CLUSTER" width="800">
```
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
     ██║███████║██████╔╝██║   ██║██║███████╗
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
           C  L  U  S  T  E  R
    Orchestration Multi-GPU Distribuee
```

<p align="center">
  <img src="https://img.shields.io/badge/Plateforme-Linux-blue?style=for-the-badge&logo=linux&logoColor=white" />
  <img src="https://img.shields.io/badge/GPU_VRAM-40_GB-green?style=for-the-badge&logo=nvidia&logoColor=white" />
  <img src="https://img.shields.io/badge/Noeuds-4-orange?style=for-the-badge&logo=serverless&logoColor=white" />
  <img src="https://img.shields.io/badge/Containers-10-blueviolet?style=for-the-badge&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/Pipeline-9_etapes-red?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Licence-Privee-lightgrey?style=for-the-badge" />
</p>

<p align="center">
  <strong>Systeme d'orchestration IA distribue multi-GPU et multi-noeuds.<br/>
  Dispatch engine 9 etapes, quality gates 6 axes, consensus multi-modele,<br/>
  failover en cascade, auto-amelioration et monitoring thermique GPU.</strong>
</p>

---



## Cluster Architecture

```mermaid
graph TB
    subgraph M1[M1 Master — 6 GPUs]
        RTX3080[RTX 3080 10GB]
        RTX2060[RTX 2060 12GB]
        GTX1660[4x GTX 1660S 24GB]
    end
    subgraph M2[M2 Detector]
        M2GPU[3 GPUs 24GB]
    end
    subgraph M3[M3 Orchestrator]
        M3GPU[Remote LMStudio]
    end
    M1 <-->|Sync| M2
    M1 <-->|Sync| M3
    M2 <-->|Failover| M3
```

## Table des matieres

- [Presentation](#presentation)
- [Architecture du cluster](#architecture-du-cluster)
- [Noeuds du cluster](#noeuds-du-cluster)
- [Pipeline de dispatch (9 etapes)](#pipeline-de-dispatch-9-etapes)
- [Quality Gates (6 axes)](#quality-gates-6-axes)
- [Cascade de failover](#cascade-de-failover)
- [Consensus multi-modele](#consensus-multi-modele)
- [Auto-amelioration](#auto-amelioration)
- [Containers Docker (10)](#containers-docker-10)
- [Reseau Docker](#reseau-docker)
- [Timers systemd (5)](#timers-systemd-5)
- [Matrice de routage (17 domaines)](#matrice-de-routage-17-domaines)
- [Arborescence du depot](#arborescence-du-depot)
- [Installation](#installation)
- [Commandes jarvis-ctl](#commandes-jarvis-ctl)
- [Monitoring thermique GPU](#monitoring-thermique-gpu)
- [Depannage](#depannage)
- [Licence](#licence)

---

## Presentation

**JARVIS Cluster** est le systeme d'orchestration IA distribue multi-GPU et multi-noeuds. Ce depot contient l'infrastructure cluster, le moteur de dispatch, le vote par consensus et l'orchestration multi-modele.

Le systeme repartit intelligemment les requetes sur un parc de GPUs heterogenes en tenant compte de la charge, de la latence, de la temperature et de la specialisation de chaque noeud — avec failover automatique et circuit breaker integres.

---

## Architecture du cluster

```
+=====================================================================+
|                        JARVIS CLUSTER                               |
|                                                                     |
|  +---------------------------------------------------------------+  |
|  |                    DISPATCH ENGINE                             |  |
|  |  health --> classify --> memory --> optimize --> route          |  |
|  |       --> dispatch --> quality gates --> feedback --> events    |  |
|  +-----------------------------+---------------------------------+  |
|                                |                                    |
|            +-------------------+-------------------+                |
|            |                   |                   |                |
|            v                   v                   v                |
|     +-----------+      +-----------+       +-----------+           |
|     | M1 (local)|      | M2 (LAN)  |       | M3 (LAN)  |          |
|     | 5 GPUs    |      | fast      |       | general   |          |
|     | 40GB VRAM |      | inference |       | inference |          |
|     | deep      |      |           |       | reasoning |          |
|     | analysis  |      |           |       | fallback  |          |
|     +-----------+      +-----------+       +-----------+           |
|            |                                                        |
|            v                                                        |
|     +-----------+      +-----------+       +-----------+           |
|     | OL1       |      | GEMINI    |       | CLAUDE    |           |
|     | (Ollama)  |      | (API)     |       | (API)     |           |
|     | cloud     |      | fallback  |       | fallback  |           |
|     | inference |      |           |       |           |           |
|     +-----------+      +-----------+       +-----------+           |
|                                                                     |
|  +---------------------------------------------------------------+  |
|  |            CIRCUIT BREAKER (par noeud)                         |  |
|  |          3 echecs --> skip 60s --> retry auto                  |  |
|  +---------------------------------------------------------------+  |
|                                                                     |
|  +---------------------------------------------------------------+  |
|  |         LOAD BALANCER (scoring par noeud)                      |  |
|  |       Routage adaptatif : latence + score qualite              |  |
|  +---------------------------------------------------------------+  |
+=====================================================================+
```

---

## Noeuds du cluster

| Noeud | Adresse | Role | GPUs | VRAM |
|-------|---------|------|------|------|
| **M1** "La Creatrice" | `127.0.0.1:1234` | `deep_analysis` | RTX 3080 (10GB), RTX 2060 (12GB), 3x GTX 1660 SUPER (6GB) | **40 GB** |
| **M2** | `192.168.1.26:1234` | `fast_inference` | — | — |
| **M3** | `192.168.1.113:1234` | `general_inference` (reasoning fallback) | — | — |
| **OL1** | `127.0.0.1:11434` | `cloud_inference` (Ollama) | — | — |

### Specifications M1

| Composant | Detail |
|-----------|--------|
| CPU | AMD Ryzen 7 5700X3D — 16 threads |
| RAM | 46 GB DDR4 + 12 GB ZRAM |
| GPU 0 | NVIDIA RTX 3080 — 10 GB GDDR6X |
| GPU 1 | NVIDIA RTX 2060 — 12 GB GDDR6 |
| GPU 2 | NVIDIA GTX 1660 SUPER — 6 GB GDDR6 |
| GPU 3 | NVIDIA GTX 1660 SUPER — 6 GB GDDR6 |
| GPU 4 | NVIDIA GTX 1660 SUPER — 6 GB GDDR6 |
| **VRAM totale** | **40 GB** |

---

## Pipeline de dispatch (9 etapes)

Chaque requete traverse un pipeline complet en 9 etapes sequentielles :

```
  +===============+
  | 1. HEALTH     |  Verification sante de tous les noeuds
  |    CHECK      |  (latence, GPU temp, disponibilite)
  +======+========+
         |
         v
  +===============+
  | 2. CLASSIFY   |  Classification du domaine de la requete
  |               |  (17 domaines de routage)
  +======+========+
         |
         v
  +===============+
  | 3. MEMORY     |  Enrichissement via memoire contextuelle
  |  ENRICHMENT   |  (historique, patterns, preferences)
  +======+========+
         |
         v
  +===============+
  | 4. PROMPT     |  Optimisation du prompt avant envoi
  |  OPTIMIZE     |  (reformulation, ajout contexte)
  +======+========+
         |
         v
  +===============+
  | 5. ROUTE      |  Selection du noeud optimal
  |               |  (score, latence, specialisation)
  +======+========+
         |
         v
  +===============+
  | 6. DISPATCH   |  Envoi au noeud selectionne
  |               |  (avec timeout et retry)
  +======+========+
         |
         v
  +===============+
  | 7. QUALITY    |  Validation sur 6 axes
  |    GATES      |  (longueur, structure, pertinence,
  |               |   confiance, latence, hallucination)
  +======+========+
         |
         v
  +===============+
  | 8. FEEDBACK   |  Boucle de retour
  |               |  (scoring, apprentissage, ajustement)
  +======+========+
         |
         v
  +===============+
  | 9. EVENT      |  Diffusion sur le bus d'evenements
  |    STREAM     |  (WebSocket, logs, metriques)
  +===============+
```

---

## Quality Gates (6 axes)

Chaque reponse est evaluee sur 6 axes avant d'etre validee :

| Axe | Description |
|-----|-------------|
| **Longueur** | La reponse respecte la taille attendue |
| **Structure** | Format coherent (markdown, listes, code) |
| **Pertinence** | Adequation avec la requete originale |
| **Confiance** | Score de confiance du modele |
| **Latence** | Temps de reponse dans les seuils acceptables |
| **Hallucination** | Detection de contenu fabrique ou incoherent |

Si une reponse echoue aux quality gates, le dispatch engine relance la requete vers un autre noeud via la cascade de failover.

---

## Cascade de failover

En cas d'echec ou de quality gate non satisfait, les requetes suivent cette cascade :

```
  M1 --fail--> M2 --fail--> OL1 --fail--> M3 --fail--> GEMINI --fail--> CLAUDE
  |            |             |             |             |                |
  deep         fast          cloud         general       API              API
  analysis     inference     inference     inference     fallback         fallback
```

Le **circuit breaker** protege chaque noeud individuellement :
- **3 echecs consecutifs** : le noeud est mis en pause pendant **60 secondes**
- Apres le delai, le noeud est automatiquement remis en service
- Chaque noeud a son propre compteur independant

---

## Consensus multi-modele

Pour les requetes critiques, le systeme utilise un **vote pondere** entre plusieurs modeles :

```
  +---------+     +---------+     +---------+
  |   M1    |     |   M2    |     |   OL1   |
  |         |     |         |     |         |
  +----+----+     +----+----+     +----+----+
       |               |               |
       v               v               v
  +------------------------------------------+
  |         CONSENSUS ENGINE                  |
  |   Vote pondere M1 + M2 + OL1             |
  |   --> Reponse consolidee                  |
  +------------------------------------------+
```

Chaque noeud contribue avec un poids proportionnel a son score de fiabilite historique.

---

## Auto-amelioration

### 5 types d'auto-actions

Le systeme s'ameliore en continu via 5 mecanismes automatiques :

| Action | Description |
|--------|-------------|
| `route_shift` | Deplacement du routage vers un noeud plus performant |
| `temp_adjust` | Ajustement de la temperature du modele |
| `tokens_adjust` | Modification du nombre de tokens max |
| `gate_tune` | Affinage des seuils des quality gates |
| `prompt_enhance` | Amelioration automatique des prompts |

### Moteur de reflexion (5 axes)

Le systeme evalue sa propre performance sur 5 axes :

| Axe | Ce qu'il mesure |
|-----|-----------------|
| **Qualite** | Score moyen des quality gates |
| **Performance** | Latence et debit |
| **Fiabilite** | Taux de succes, uptime |
| **Efficience** | Utilisation des ressources GPU/RAM |
| **Croissance** | Evolution des patterns et apprentissage |

### Evolution des patterns

Le systeme detecte automatiquement les lacunes dans ses connaissances et cree de nouveaux patterns pour y repondre.

---

## Containers Docker (10)

| # | Container | Role | Port |
|---|-----------|------|------|
| 1 | `jarvis-ws` | Hub WebSocket FastAPI | `9742` |
| 2 | `vocal-engine` | Wake word + pipeline STT | — |
| 3 | `pipeline-engine` | Moteur de dispatch | — |
| 4 | `domino` | Actions apprises | — |
| 5 | `openclaw-node` | Gateway | `28789` |
| 6 | `cowork-engine` | 477 scripts autonomes | — |
| 7 | `cowork-dispatcher` | Routeur cowork | — |
| 8 | `vocal-whisper` | STT GPU (Whisper) | `18001` |
| 9 | `domino-mcp` | Bridge SSE | `8901` |
| 10 | `jarvis-telegram` | Bot Telegram distant | — |

---

## Reseau Docker

```
+======================== jarvis-network ==========================+
|                                                                   |
|  +--------------+   +--------------+   +--------------+          |
|  |  jarvis-ws   |<--|  pipeline-   |-->|  vocal-      |          |
|  |  :9742       |   |  engine      |   |  engine      |          |
|  +------+-------+   +------+-------+   +--------------+          |
|         |                  |                                      |
|         |           +------+-------+   +--------------+          |
|         |           |   domino     |   |  vocal-      |          |
|         |           |              |   |  whisper     |          |
|         |           +--------------+   |  :18001      |          |
|         |                              +--------------+          |
|         |                                                        |
|  +------+-------+   +--------------+   +--------------+          |
|  |  openclaw-   |   |  cowork-     |-->|  cowork-     |          |
|  |  node        |   |  dispatcher  |   |  engine      |          |
|  |  :28789      |   +--------------+   +--------------+          |
|  +--------------+                                                |
|                                                                   |
|  +--------------+   +--------------+                              |
|  |  domino-mcp  |   |  jarvis-     |                              |
|  |  :8901       |   |  telegram    |                              |
|  +--------------+   +--------------+                              |
|                                                                   |
+=================================================================+
```

---

## Timers systemd (5)

| Timer | Frequence | Role |
|-------|-----------|------|
| `jarvis-health` | Toutes les 15 min | Verification sante du cluster |
| `jarvis-backup` | Quotidien | Sauvegarde des donnees et configs |
| `jarvis-thermal` | Toutes les 5 min | Surveillance thermique GPU |
| `jarvis-log-rotate` | Hebdomadaire | Rotation des logs |
| `jarvis-pipeline-check` | Toutes les 10 min | Verification du pipeline de dispatch |

---

## Matrice de routage (17 domaines)

Le routeur adaptatif gere **17 domaines** pour diriger chaque requete vers le noeud le plus adapte, en tenant compte de :

- La specialisation du noeud pour le domaine
- La latence mesuree
- Le score de qualite historique
- La charge GPU actuelle
- La temperature GPU

---

## Arborescence du depot

```
JARVIS-CLUSTER/
|-- src/                    # Modules source
|-- canvas/                 # Interface UI avec proxy
|-- cowork/                 # Scripts autonomes
|-- docker/                 # Deploiement Docker
|-- electron/               # Application desktop
|-- scripts/                # Utilitaires cluster
|-- data/                   # Bases de donnees
|-- n8n_workflows/          # Automatisation workflows
|-- plugins/                # Plugins Claude Code
|-- projects/               # Deploiement Linux
|   +-- linux/
|       |-- install.sh          # Script d'installation
|       |-- docker-compose.yml  # Orchestration containers
|       +-- jarvis-ctl.sh       # Controle du cluster
|-- main.py                 # Point d'entree
|-- requirements.txt        # Dependances Python
|-- pyproject.toml          # Configuration projet
+-- README.md               # Ce fichier
```

---

## Installation

### Prerequis

- Linux (teste sur Ubuntu/Arch)
- Docker + Docker Compose
- NVIDIA drivers + NVIDIA Container Toolkit
- Python 3.11+
- Au moins 1 GPU NVIDIA

### Installation rapide

```bash
# Cloner le depot
git clone https://github.com/Turbo31150/JARVIS-CLUSTER.git
cd JARVIS-CLUSTER

# Lancer l'installation
bash projects/linux/install.sh
```

### Deploiement Docker

```bash
# Lancer tous les containers
cd projects/linux
docker compose up -d

# Verifier le statut
docker compose ps
```

### Controle avec jarvis-ctl

```bash
# Demarrer le cluster
bash projects/linux/jarvis-ctl.sh start

# Statut du cluster
bash projects/linux/jarvis-ctl.sh status

# Arreter le cluster
bash projects/linux/jarvis-ctl.sh stop
```

---

## Commandes jarvis-ctl

```bash
jarvis-ctl.sh start       # Demarrer tous les services
jarvis-ctl.sh stop        # Arreter tous les services
jarvis-ctl.sh restart     # Redemarrer
jarvis-ctl.sh status      # Etat du cluster
jarvis-ctl.sh logs        # Voir les logs
jarvis-ctl.sh health      # Check sante complet
```

---

## Monitoring thermique GPU

Le systeme surveille en continu la temperature des 5 GPUs de M1 :

| Seuil | Temperature | Action |
|-------|-------------|--------|
| Normal | < 75 C | Operation normale |
| Warning | >= 75 C | Alerte, reduction de charge |
| Critique | >= 85 C | Reroutage automatique vers un autre noeud |

Le timer `jarvis-thermal` verifie toutes les 5 minutes. En cas de surchauffe critique, le dispatch engine reroute automatiquement les requetes vers un noeud plus froid.

---

## Depannage

### Un noeud ne repond pas

```bash
# Verifier la connectivite
curl -s http://<adresse>:<port>/health

# Verifier le circuit breaker
bash projects/linux/jarvis-ctl.sh status
```

Le circuit breaker met automatiquement le noeud en pause apres 3 echecs et reessaie apres 60 secondes.

### Temperature GPU trop elevee

```bash
# Verifier les temperatures
nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader

# Le systeme reroute automatiquement au-dessus de 85 C
```

### Container Docker qui ne demarre pas

```bash
# Voir les logs du container
docker compose -f projects/linux/docker-compose.yml logs <container>

# Redemarrer un container specifique
docker compose -f projects/linux/docker-compose.yml restart <container>
```

### Pipeline bloque

```bash
# Le timer jarvis-pipeline-check verifie toutes les 10 min
# Relancer manuellement :
bash projects/linux/jarvis-ctl.sh restart
```

### OL1 (Ollama) hors ligne

```bash
# Redemarrer Ollama
ollama serve

# Verifier le statut
curl -s http://127.0.0.1:11434/api/tags
```

---

## Licence

**Projet prive** — Tous droits reserves.

Ce depot est un projet personnel. Aucune licence open source n'est accordee.

---

<p align="center">
  <strong>JARVIS Cluster</strong> — Orchestration IA distribuee multi-GPU<br/>
  Concu et maintenu par <a href="https://github.com/Turbo31150">Turbo</a>
</p>


---



---

## What is La Creatrice?

**La Creatrice** is the name of the home-built GPU cluster at the heart of JARVIS. It is a multi-machine setup running **21 AI models** across **3 physical machines**, with a total of **46 GB VRAM** capable of running multiple LLMs simultaneously with automatic failover.

The cluster was designed from scratch with consumer-grade hardware -- no cloud, no rented GPUs. It handles everything from fast inference (gemma-3-4b at 0.4s response time) to deep reasoning (deepseek-r1) to code generation (deepseek-coder), all orchestrated by the 9-stage dispatch pipeline described above.

**Why "La Creatrice"?** Because this machine creates -- it generates code, writes documentation, analyzes markets, composes responses, and orchestrates 600+ agents. It is not just a server; it is the creative engine of the entire JARVIS ecosystem.

## Cost Comparison

| | Cloud GPU (A100 80GB) | La Creatrice (Home Cluster) |
|---|---|---|
| **Hardware** | Rented | Owned (RTX 3080 + RTX 2060 + 3x GTX 1660S) |
| **VRAM** | 80 GB | 46 GB (across 6 GPUs) |
| **Monthly cost** | ~2.50 EUR/h = **~1,800 EUR/month** (24/7) | **~30 EUR/month** (electricity only) |
| **Initial investment** | 0 EUR | ~800 EUR (used GPUs + hardware) |
| **Break-even** | Never -- recurring cost | **< 3 months** |
| **Data privacy** | Data leaves your network | **100% local** -- nothing leaves the house |
| **Availability** | Subject to provider quotas | **Always available** -- your hardware, your rules |
| **Annual cost** | **~21,600 EUR** | **~360 EUR** |

> **ROI: 3 months.** After that, every month of running La Creatrice saves ~1,770 EUR compared to cloud GPU rental.




---

## GPU Allocation Table

Real-time hardware allocation across the cluster:

| GPU | Model Loaded | VRAM Used | Node | Avg Response | Use Case |
|-----|-------------|-----------|------|-------------|----------|
| RTX 3080 10GB | deepseek-r1-qwen3-8b | 9.6 GB | M1 | 7-12s | Complex reasoning, code generation |
| RTX 2060 12GB | qwen3.5-9b | 8.1 GB | M1 | 2-5s | General queries, balanced performance |
| GTX 1660S #1 | gemma-3-4b | 4.2 GB | M1 | 0.5-2s | Fast responses, simple tasks |
| GTX 1660S #2 | nomic-embed-text | 3.8 GB | M1 | <0.5s | Embeddings, semantic search |
| GTX 1660S #3 | whisper-large-v3 | 4.8 GB | M1 | real-time | Voice transcription (Lumen) |
| GTX 1660S #4 | *(available)* | 0.1 GB | M1 | — | Hot-swap slot |

### Node Benchmarks

```
Benchmark: 100 queries × 3 complexity levels (2026-03-27)

M3 (deepseek-r1-qwen3-8b) — CHAMPION
  Simple:   1.8s avg | 100% success | Quality: 9.2/10
  Medium:   4.5s avg | 100% success | Quality: 9.0/10
  Complex: 11.2s avg | 100% success | Quality: 8.7/10
  → Reliability: 100% (0 failures in 300 queries)

M1 (gemma-3-4b) — FASTEST
  Simple:   0.4s avg |  99% success | Quality: 7.8/10
  Medium:   1.1s avg |  98% success | Quality: 7.5/10
  Complex:  2.8s avg |  95% success | Quality: 6.9/10
  → Best for: latency-sensitive tasks

OL1 (qwen2.5:1.5b) — LIGHTWEIGHT
  Simple:   0.9s avg |  97% success | Quality: 6.5/10
  Medium:   2.3s avg |  94% success | Quality: 5.8/10
  Complex:  5.1s avg |  88% success | Quality: 5.2/10
  → Best for: fallback, simple classification
```

### Quick Benchmark Script

```python
import asyncio, time, httpx

NODES = {
    "M1": "http://127.0.0.1:1234/v1/chat/completions",
    "M3": "http://192.168.1.113:1234/v1/chat/completions",
    "OL1": "http://127.0.0.1:11434/api/chat",
}

async def benchmark_node(name, url, prompt="Explain quicksort in 3 sentences."):
    async with httpx.AsyncClient(timeout=30) as client:
        start = time.perf_counter()
        if "ollama" in url or "11434" in url:
            payload = {"model": "qwen2.5:1.5b", "messages": [{"role": "user", "content": prompt}]}
        else:
            payload = {"model": "default", "messages": [{"role": "user", "content": prompt}]}
        resp = await client.post(url, json=payload)
        elapsed = time.perf_counter() - start
        print(f"{name}: {elapsed:.2f}s | Status: {resp.status_code}")

async def main():
    await asyncio.gather(*[benchmark_node(n, u) for n, u in NODES.items()])

asyncio.run(main())
# Output:
# M1:  0.42s | Status: 200
# M3:  3.18s | Status: 200
# OL1: 1.05s | Status: 200
```

### Failover Cascade

```
Primary path: M3 → OL1 → M1 → M2 → GEMINI → CLAUDE

When a node fails:
1. Detect timeout (>30s) or HTTP error
2. Log failure + increment error counter
3. Route to next node in cascade
4. If GPU temp > 85°C → skip node entirely
5. If all local nodes down → escalate to cloud (Gemini → Claude)

Recovery: failed nodes auto-retry every 60s
```


## License

MIT License — Free for personal and commercial use.

## Author

**Franck Delmas** — AI Systems Architect
- [GitHub](https://github.com/Turbo31150) · [Portfolio](https://turbo31150.github.io/franckdelmas.dev/) · [LinkedIn](https://linkedin.com/in/franck-hlb-80bb231b1) · [Codeur](https://codeur.com/-6666zlkh)

Part of [JARVIS OS](https://github.com/Turbo31150/jarvis-linux) ecosystem.
