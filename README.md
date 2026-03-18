# 🧪 webserv-tester

<p align="center">
  <img src="https://media.giphy.com/media/13HgwGsXF0aiGY/giphy.gif" width="250" alt="tester-gif">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.6+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Tests-118-success.svg" alt="Tests">
  <img src="https://img.shields.io/badge/Dependencies-None-lightgrey.svg" alt="Dependencies">
  <img src="https://img.shields.io/badge/42-Project-black.svg" alt="42">
  <img src="https://img.shields.io/badge/Status-Ready_to_break_your_server-red.svg" alt="Status">
</p>

---

## 🚀 Présentation

> Un tester HTTP **complet, automatique et sans pitié** pour le projet **Webserv**.

* 💥 Génère toute l'infrastructure  
* ⚙️ Configure ton serveur automatiquement  
* 🧪 Lance **118 tests** ultra stricts  
* 👉 Objectif : **casser ton serveur avant la moulinette**

---

## ⚡ Features

* 🔥 +100 tests couvrant tout le sujet
* 📦 Setup automatique (zéro configuration)
* 🧠 Détection d'erreurs subtiles
* 🛡️ Tests de sécurité (HTTP smuggling, slowloris…)
* ⚡ Rapide, lisible et efficace

---

## 🖥️ Installation

```bash
git clone https://github.com/Tommfnr/webserv-tester
cd webserv-tester
```

---

## ▶️ Quickstart

```bash
# 1. Génère l'infrastructure et tester.conf
python3 tester.py init

# 2. Lance ton serveur avec la config générée
./webserv tester.conf

# 3. Lance les tests
python3 tester.py run
```

---

## 🧰 Commandes

| Commande | Description |
|----------|-------------|
| `init`   | Génère toute l'infrastructure (`www/`, `logs/`, `tester.conf`) |
| `run`    | Lance tous les tests (vérifie infra + serveur d'abord) |
| `check`  | Vérifie l'état de l'infra et du serveur sans lancer les tests |
| `clean`  | Supprime tous les fichiers générés (repart de zéro) |
| `help`   | Affiche l'aide et la configuration active |

### Options

```bash
python3 tester.py run   --host 127.0.0.1 --port 8080   # valeurs par défaut
python3 tester.py init  --host 127.0.2.1 --port 9090   # config custom
```

---

## 📁 Structure générée

```
webserv-tester/
├── tester.py
├── tester.conf
├── www/
│   ├── index.html
│   ├── contact.html
│   ├── uploads/
│   ├── files/
│   │   └── sample.txt
│   ├── cgi-bin/
│   │   └── hello.py
│   └── errors/
│       ├── 400.html ... 505.html
│       └── error.html
└── logs/
    ├── access.log
    └── error.log
```

---

## ⚙️ Configuration

### localhost — vhost principal

| Route | Méthodes | Notes |
|-------|----------|-------|
| `/` | GET | fichier statique |
| `/contacts` | GET POST DELETE | `client_max_body_size 1MB` |
| `/upload` | POST | stocke dans `www/uploads/` |
| `/upload/delete` | DELETE | supprime les fichiers uploadés |
| `/files` | GET | `autoindex on` — directory listing |
| `/old` | — | `301 → /` |
| `/temp` | — | `302 → /contacts` |
| `/cgi-bin` | GET POST | `.py` exécuté avec `python3` |

### secondary — vhost restreint

| Route | Méthodes | Notes |
|-------|----------|-------|
| `/upload` | POST | `client_max_body_size 1MB` |
| `/delete` | DELETE | `client_max_body_size 0` global |

---

## 🧪 Tests

118 tests répartis en 18 sections :

| Section | Tests | Exigence sujet |
|---------|-------|----------------|
| Valid requests | 10 | GET / POST / DELETE |
| Upload | 5 | *"clients must be able to upload files"* |
| Redirection | 2 | *"HTTP redirection"* |
| Directory listing | 3 | *"enabling/disabling directory listing"* |
| CGI | 3 | *"execution of CGI based on file extension"* |
| Méthodes | 14 | autorisées / interdites / malformées |
| Headers | 20 | malformés, manquants, injectés, trop longs |
| Body | 15 | limites de taille, chunked, Content-Length |
| URI | 14 | traversal, encodage, null bytes, longueur |
| Protocol | 7 | gestion des versions HTTP |
| Request line | 7 | CRLF, espaces, tabs |
| Fichiers statiques | 3 | *"serve a fully static website"* |
| Pages d'erreur | 3 | *"must have default error pages"* |
| Headers de réponse | 3 | Content-Type, Content-Length |
| HTTP Smuggling | 3 | CL-TE, TE obfusqué, chunk overflow |
| Pipelining | 2 | plusieurs requêtes sur une connexion |
| Slowloris / DoS | 2 | *"server must remain available at all times"* |
| Unicode / Encoding | 2 | UTF-8 overlong, double percent-encoding |

---

## 📊 Exemple de sortie

```
══════════════════════════════════════════════════════════════════
  WEBSERV 42 — HTTP TESTER  —  127.0.0.1:8080
══════════════════════════════════════════════════════════════════

  ── VALID REQUESTS ──
  [PASS]  VALID_GET                                     HTTP/1.1 200 OK  (1.2 ms)
  [PASS]  VALID_POST_CONTACTS                           HTTP/1.1 201 Created  (0.8 ms)
  [FAIL]  CHUNKED_VALID                                 got [HTTP/1.1 500 ...]  expected 200|201
  [ERR ]  BODY_TOO_BIG                                  [Errno 104] Connection reset  (expected 413)

  ████████████████████░░░░░░░░░░  98 passed / 4 failed / 1 errors / 103 total
══════════════════════════════════════════════════════════════════
```

---

## 👤 Auteur

**Tommfnr** — [github.com/Tommfnr](https://github.com/Tommfnr)

---

> ⭐ Star le repo si ça t'aide !