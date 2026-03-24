# 🏗️ JARVIS CLUSTER — HIGH-PERFORMANCE INFRASTRUCTURE (v12.4)

Ce dépôt est le centre de gestion de l'infrastructure matérielle et distribuée de l'écosystème JARVIS. Il orchestre la puissance de calcul brute à travers le cluster multi-GPU.

---

## 🚀 I. NODES ARCHITECTURE (DISTRIBUTED COMPUTING)
Le cluster est composé de 3 nœuds physiques synchronisés :
- **M1 (Leader)** : `192.168.1.85` — Ryzen 5700X3D + Array de 6 GPUs. Orchestre le Swarm et l'inférence primaire.
- **M2 (Worker Logic)** : Inférence DeepSeek R1 & Analyse cognitive.
- **M3 (Worker Expansion)** : Nœud de calcul additionnel (Offline).

---

## 🐳 II. DOCKER ORCHESTRATION
Toutes les configurations de déploiement sont centralisées dans `infra/docker/`.
- **Réseau Overlay** : Communication sécurisée inter-machine via `jarvis-cluster-net`.
- **Load Balancing** : Distribution dynamique des tâches via `adaptive_load_balancer.py`.

---

## 🧠 III. AI TRAINING & FINE-TUNING
Les briques d'apprentissage profond sont situées dans `core/training/` :
- **Dataset Preparation** : Conversion des logs système en données d'entraînement.
- **Model Merging** : Scripts pour fusionner les poids des modèles locaux.
- **Benchmark Tools** : Mesure de la puissance brute (Teraflops) du cluster.

---

## 🛠️ IV. INFRASTRUCTURE CONTROL
Utilisez les launchers situés dans `infra/boot/` pour démarrer les services :
- `JARVIS_UNIFIED_BOOT.bat` : Lancement coordonné Windows/Linux.
- `pipeline_watchdog.py` : Surveillance et auto-guérison des services Docker.

---
**[Maintained by OMEGA v3.0 — The Muscle of JARVIS OS]**
**,file_path: