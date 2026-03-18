#!/usr/bin/env python3
# ============================================================
#  Webserv 42 — HTTP Parser Tester
#  Config associée : tester.conf
#
#  Vhost default   (Host: localhost)  → port 8080
#    /              GET only
#    /contacts      GET POST DELETE
#
#  Vhost secondary (Host: secondary)  → port 8080
#    /upload        POST only
#    /delete        DELETE only
#
#  Format expected :
#    int         → un seul code accepté
#    (int, ...)  → plusieurs codes acceptés
# ============================================================
import socket
import time
import os
import sys

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080

# Écrasés par --host / --port en ligne de commande
HOST = DEFAULT_HOST
PORT = DEFAULT_PORT

# ─────────────────────────────────────────────
# ANSI
# ─────────────────────────────────────────────
GREEN   = "\033[32m"
RED     = "\033[31m"
YELLOW  = "\033[33m"
CYAN    = "\033[36m"
MAGENTA = "\033[35m"
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"

# ─────────────────────────────────────────────
# AUTO-SETUP : création des fichiers/dossiers
# ─────────────────────────────────────────────

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
WEB_ROOT   = os.path.join(BASE_DIR, "www")
ERRORS_DIR = os.path.join(WEB_ROOT, "errors")
LOGS_DIR   = os.path.join(BASE_DIR, "logs")

def infrastructure_exists():
    """Retourne True si l'infrastructure est déjà entièrement en place."""
    required = [
        WEB_ROOT,
        ERRORS_DIR,
        LOGS_DIR,
        UPLOAD_DIR,
        LISTING_DIR,
        CGI_DIR,
        os.path.join(WEB_ROOT,   "index.html"),
        os.path.join(WEB_ROOT,   "contact.html"),
        os.path.join(ERRORS_DIR, "400.html"),
        os.path.join(ERRORS_DIR, "404.html"),
        os.path.join(ERRORS_DIR, "405.html"),
        os.path.join(ERRORS_DIR, "413.html"),
        os.path.join(ERRORS_DIR, "431.html"),
        os.path.join(ERRORS_DIR, "500.html"),
        os.path.join(ERRORS_DIR, "505.html"),
        os.path.join(ERRORS_DIR, "error.html"),
        os.path.join(LOGS_DIR,   "access.log"),
        os.path.join(LOGS_DIR,   "error.log"),
        os.path.join(CGI_DIR,    "hello.py"),
        os.path.join(BASE_DIR,   "tester.conf"),
    ]
    return all(os.path.exists(p) for p in required)

def server_is_up():
    """Retourne True si le serveur répond sur HOST:PORT."""
    try:
        s = socket.socket()
        s.settimeout(2)
        s.connect((HOST, PORT))
        s.send(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
        data = s.recv(16)
        s.close()
        return len(data) > 0
    except Exception:
        return False

UPLOAD_DIR  = os.path.join(WEB_ROOT, "uploads")
LISTING_DIR = os.path.join(WEB_ROOT, "files")
CGI_DIR     = os.path.join(WEB_ROOT, "cgi-bin")

def setup_environment():
    """Crée tous les fichiers et dossiers requis par tester.conf."""
    print(f"\n{BOLD}{'='*66}{RESET}")
    print(f"{BOLD}  SETUP — Création de l'environnement de test{RESET}")
    print(f"{BOLD}{'='*66}{RESET}")

    created = []
    skipped = []

    def make_dir(path):
        if not os.path.isdir(path):
            try:
                os.makedirs(path, exist_ok=True)
                created.append(f"[DIR]  {path}")
            except PermissionError:
                print(f"  {RED}[ERREUR]{RESET} Permission refusée : {path}")
                print(f"  {YELLOW}→ Relancez avec sudo, ou créez manuellement : sudo mkdir -p {path}{RESET}")
                sys.exit(1)
        else:
            skipped.append(f"[DIR]  {path}")

    def make_file(path, content):
        if not os.path.isfile(path):
            try:
                with open(path, "w") as f:
                    f.write(content)
                created.append(f"[FILE] {path}")
            except PermissionError:
                print(f"  {RED}[ERREUR]{RESET} Permission refusée : {path}")
                print(f"  {YELLOW}→ Relancez avec sudo, ou créez manuellement : sudo touch {path}{RESET}")
                sys.exit(1)
        else:
            skipped.append(f"[FILE] {path}")

    # ── Dossiers ──────────────────────────────
    make_dir(WEB_ROOT)
    make_dir(ERRORS_DIR)
    make_dir(LOGS_DIR)
    make_dir(UPLOAD_DIR)
    make_dir(LISTING_DIR)
    make_dir(CGI_DIR)

    # ── index.html ────────────────────────────
    make_file(os.path.join(WEB_ROOT, "index.html"), """\
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>Webserv - Index</title></head>
<body>
  <h1>Webserv 42</h1>
  <p>Serveur opérationnel.</p>
</body>
</html>
""")

    # ── contact.html ──────────────────────────
    make_file(os.path.join(WEB_ROOT, "contact.html"), """\
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>Webserv - Contacts</title></head>
<body>
  <h1>Contacts</h1>
  <p>Page de contacts.</p>
</body>
</html>
""")

    # ── Fichier dans listing_dir (pour tester le directory listing) ──
    make_file(os.path.join(LISTING_DIR, "sample.txt"), "sample file for directory listing\n")

    # ── CGI script Python ─────────────────────
    make_file(os.path.join(CGI_DIR, "hello.py"), """\
#!/usr/bin/env python3
import os
print("Content-Type: text/plain\\r")
print("\\r")
print("Hello from CGI")
print("METHOD=" + os.environ.get("REQUEST_METHOD", ""))
""")
    try:
        os.chmod(os.path.join(CGI_DIR, "hello.py"), 0o755)
    except Exception:
        pass

    # ── Pages d'erreur ────────────────────────
    error_pages = {
        "400.html":   ("400 Bad Request",                     "La requête est invalide ou mal formée."),
        "403.html":   ("403 Forbidden",                       "Accès refusé à cette ressource."),
        "404.html":   ("404 Not Found",                       "La ressource demandée est introuvable."),
        "405.html":   ("405 Method Not Allowed",              "La méthode HTTP utilisée n'est pas autorisée."),
        "413.html":   ("413 Content Too Large",               "Le corps de la requête dépasse la limite autorisée."),
        "431.html":   ("431 Request Header Fields Too Large", "Les en-têtes de la requête sont trop volumineux."),
        "500.html":   ("500 Internal Server Error",           "Une erreur interne est survenue sur le serveur."),
        "505.html":   ("505 HTTP Version Not Supported",      "La version HTTP utilisée n'est pas supportée."),
        "error.html": ("Erreur",                              "Une erreur est survenue lors du traitement de la requête."),
    }

    for filename, (title, desc) in error_pages.items():
        make_file(os.path.join(ERRORS_DIR, filename), f"""\
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>Webserv - {title}</title></head>
<body>
  <h1>{title}</h1>
  <p>{desc}</p>
</body>
</html>
""")

    # ── tester.conf (généré automatiquement) ──
    conf_path = os.path.join(BASE_DIR, "tester.conf")
    make_file(conf_path, f"""\
# ── Vhost principal : localhost ───────────────────────────────
server
{{
    listen {HOST}:{PORT};
    server_name localhost webserv.local www.webserv.local;
    root {WEB_ROOT};
    index index.html;
    allowed_methods GET;
    client_max_body_size 1048576;
    access_log {LOGS_DIR}/access.log;
    error_log {LOGS_DIR}/error.log;

    # Route racine — GET uniquement
    location /
    {{
    }}

    # Route contacts — GET POST DELETE
    location /contacts
    {{
        index contact.html;
        allowed_methods GET POST DELETE;
        client_max_body_size 1048576;
    }}

    # Upload de fichiers — POST uniquement, stockage dans uploads/
    location /upload
    {{
        allowed_methods POST;
        client_max_body_size 1048576;
        root {UPLOAD_DIR};
    }}

    # Suppression de fichiers uploadés — DELETE uniquement
    location /upload/delete
    {{
        allowed_methods DELETE;
        root {UPLOAD_DIR};
    }}

    # Directory listing activé
    location /files
    {{
        allowed_methods GET;
        autoindex on;
        root {WEB_ROOT};
    }}

    # Redirection HTTP 301
    location /old
    {{
        return 301 /;
    }}

    # Redirection HTTP 302
    location /temp
    {{
        return 302 /contacts;
    }}

    # CGI Python
    location /cgi-bin
    {{
        allowed_methods GET POST;
        root {WEB_ROOT};
        cgi_extension .py /usr/bin/python3;
    }}

    error_page 400 {WEB_ROOT}/errors/400.html;
    error_page 403 {WEB_ROOT}/errors/403.html;
    error_page 404 {WEB_ROOT}/errors/404.html;
    error_page 405 {WEB_ROOT}/errors/405.html;
    error_page 413 {WEB_ROOT}/errors/413.html;
    error_page 431 {WEB_ROOT}/errors/431.html;
    error_page 500 {WEB_ROOT}/errors/500.html;
    error_page 505 {WEB_ROOT}/errors/505.html;
}}

# ── Vhost secondaire : secondary ──────────────────────────────
server
{{
    listen {HOST}:{PORT};
    server_name secondary;
    root {WEB_ROOT};
    index index.html;
    allowed_methods GET;
    client_max_body_size 0;
    access_log {LOGS_DIR}/access.log;
    error_log {LOGS_DIR}/error.log;

    location /upload
    {{
        allowed_methods POST;
        client_max_body_size 1048576;
        root {UPLOAD_DIR};
    }}

    location /delete
    {{
        allowed_methods DELETE;
    }}

    error_page 400 404 405 {WEB_ROOT}/errors/error.html;
    error_page 413 {WEB_ROOT}/errors/error.html;
    error_page 500 {WEB_ROOT}/errors/error.html;
}}
""")

    # ── Fichiers de log ───────────────────────
    make_file(os.path.join(LOGS_DIR, "access.log"), "")
    make_file(os.path.join(LOGS_DIR, "error.log"),  "")

    # ── Rapport ───────────────────────────────
    if created:
        print(f"  {GREEN}Éléments créés :{RESET}")
        for item in created:
            print(f"    {GREEN}+{RESET} {item}")
    if skipped:
        print(f"  {DIM}Déjà présents ({len(skipped)}) :{RESET}")
        for item in skipped:
            print(f"    {DIM}· {item}{RESET}")

    print(f"\n  {GREEN}{BOLD}Environnement prêt.{RESET}")
    print(f"  {DIM}Config générée : {conf_path}{RESET}")


# ─────────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────────

tests = [
    # ══════════════════════════════════════════════════════
    # VALID REQUESTS — sujet : GET POST DELETE obligatoires
    # ══════════════════════════════════════════════════════

    # GET racine → index.html → 200
    ("VALID_GET",
     200,
     "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # GET avec query string → ignorée par le serveur → 200 ou 404
    ("VALID_GET_QUERY_STRING",
     (200, 404),
     "GET /search?q=hello&page=1 HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # GET URI percent-encodée → 200 ou 404
    ("VALID_GET_ENCODED_URI",
     (200, 404),
     "GET /path%20with%20spaces HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # GET avec plusieurs headers → 200
    ("VALID_GET_MULTIPLE_HEADERS",
     200,
     "GET / HTTP/1.1\r\nHost: localhost\r\nAccept: text/html\r\nAccept-Language: fr-FR\r\nConnection: keep-alive\r\n\r\n"),

    # POST /contacts → 200 ou 201
    ("VALID_POST_CONTACTS",
     (200, 201),
     "POST /contacts HTTP/1.1\r\nHost: localhost\r\nContent-Length: 5\r\n\r\nhello"),

    # POST /contacts body vide → 200 ou 201
    ("VALID_POST_CONTACTS_EMPTY_BODY",
     (200, 201),
     "POST /contacts HTTP/1.1\r\nHost: localhost\r\nContent-Length: 0\r\n\r\n"),

    # DELETE /contacts → 200, 204 ou 404
    ("VALID_DELETE_CONTACTS",
     (200, 204, 404),
     "DELETE /contacts HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # ── vhost secondary ────────────────────────────────────
    ("VALID_POST_UPLOAD_SECONDARY",
     (200, 201),
     "POST /upload HTTP/1.1\r\nHost: secondary\r\nContent-Type: application/octet-stream\r\nContent-Length: 4\r\n\r\ndata"),

    ("VALID_DELETE_SECONDARY",
     (200, 204, 404),
     "DELETE /delete HTTP/1.1\r\nHost: secondary\r\n\r\n"),

    ("VALID_GET_SECONDARY",
     200,
     "GET / HTTP/1.1\r\nHost: secondary\r\n\r\n"),

    # ══════════════════════════════════════════════════════
    # UPLOAD — sujet : "clients must be able to upload files"
    # ══════════════════════════════════════════════════════

    # Upload binaire simple → 200 ou 201
    ("UPLOAD_BINARY_FILE",
     (200, 201),
     "POST /upload HTTP/1.1\r\nHost: localhost\r\n"
     "Content-Type: application/octet-stream\r\nContent-Length: 8\r\n\r\n\x89PNG\r\n\x1a\n"),

    # Upload multipart/form-data → 200 ou 201
    ("UPLOAD_MULTIPART_FORM",
     (200, 201),
     "POST /upload HTTP/1.1\r\nHost: localhost\r\n"
     "Content-Type: multipart/form-data; boundary=boundary123\r\n"
     "Content-Length: 118\r\n\r\n"
     "--boundary123\r\n"
     "Content-Disposition: form-data; name=\"file\"; filename=\"test.txt\"\r\n"
     "Content-Type: text/plain\r\n\r\n"
     "hello world\r\n"
     "--boundary123--\r\n"),

    # Upload sur route non autorisée → 405
    ("UPLOAD_ON_FORBIDDEN_ROUTE",
     405,
     "POST / HTTP/1.1\r\nHost: localhost\r\nContent-Length: 4\r\n\r\ndata"),

    # Upload dépassant client_max_body_size → 413
    ("UPLOAD_EXCEEDS_MAX_BODY",
     413,
     "POST /upload HTTP/1.1\r\nHost: localhost\r\n"
     "Content-Length: 2000000\r\n\r\n" + "A" * 2000000),

    # Upload chunked → 200 ou 201
    ("UPLOAD_CHUNKED",
     (200, 201),
     "POST /upload HTTP/1.1\r\nHost: localhost\r\n"
     "Content-Type: application/octet-stream\r\n"
     "Transfer-Encoding: chunked\r\n\r\n"
     "4\r\ndata\r\n0\r\n\r\n"),

    # ══════════════════════════════════════════════════════
    # REDIRECTION — sujet : "HTTP redirection"
    # ══════════════════════════════════════════════════════

    # 301 Moved Permanently
    ("REDIRECT_301",
     301,
     "GET /old HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # 302 Found
    ("REDIRECT_302",
     302,
     "GET /temp HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # ══════════════════════════════════════════════════════
    # DIRECTORY LISTING — sujet : "enabling/disabling directory listing"
    # ══════════════════════════════════════════════════════

    # Listing activé sur /files → 200 avec contenu HTML
    ("LISTING_ENABLED",
     200,
     "GET /files HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # Listing sur dossier inexistant → 404
    ("LISTING_DIR_NOT_FOUND",
     404,
     "GET /files/nonexistent_subdir/ HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # Listing désactivé (route /) → 200 ou 403 (pas d'autoindex → pas de listing)
    ("LISTING_DISABLED_ON_ROOT",
     (200, 403),
     "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # ══════════════════════════════════════════════════════
    # CGI — sujet : "execution of CGI based on file extension"
    # ══════════════════════════════════════════════════════

    # GET sur script CGI Python → 200
    ("CGI_GET_PYTHON",
     200,
     "GET /cgi-bin/hello.py HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # POST sur script CGI avec body → 200
    ("CGI_POST_PYTHON",
     (200, 201),
     "POST /cgi-bin/hello.py HTTP/1.1\r\nHost: localhost\r\n"
     "Content-Length: 5\r\n\r\nhello"),

    # CGI inexistant → 404
    ("CGI_NOT_FOUND",
     404,
     "GET /cgi-bin/notexist.py HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # ══════════════════════════════════════════════════════
    # MÉTHODES — sujet : "at least GET, POST, DELETE"
    # ══════════════════════════════════════════════════════

    # POST sur route GET only → 405
    ("METHOD_POST_ON_ROOT_NOT_ALLOWED",
     405,
     "POST / HTTP/1.1\r\nHost: localhost\r\nContent-Length: 5\r\n\r\nhello"),

    # DELETE sur route GET only → 405
    ("METHOD_DELETE_ON_ROOT_NOT_ALLOWED",
     405,
     "DELETE / HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # POST /upload sur mauvais vhost → 404 ou 405
    ("METHOD_POST_UPLOAD_WRONG_VHOST",
     (404, 405),
     "POST /upload HTTP/1.1\r\nHost: localhost\r\nContent-Length: 4\r\n\r\ndata"),

    # HEAD → non requis par le sujet → 405 (ou 200 si implémenté)
    ("METHOD_HEAD",
     (200, 405),
     "HEAD / HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # PUT → non requis → 405
    ("METHOD_PUT_NOT_SUPPORTED",
     405,
     "PUT / HTTP/1.1\r\nHost: localhost\r\nContent-Length: 4\r\n\r\ndata"),

    # OPTIONS → non requis → 405
    ("METHOD_OPTIONS_NOT_SUPPORTED",
     405,
     "OPTIONS / HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # PATCH → non requis → 405
    ("METHOD_PATCH_NOT_SUPPORTED",
     405,
     "PATCH / HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # TRACE → non requis → 405
    ("METHOD_TRACE_NOT_SUPPORTED",
     405,
     "TRACE / HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # CONNECT → non requis → 405
    ("METHOD_CONNECT_NOT_SUPPORTED",
     405,
     "CONNECT / HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # DELETE sur /upload secondary → 405
    ("METHOD_DELETE_ON_UPLOAD_NOT_ALLOWED",
     405,
     "DELETE /upload HTTP/1.1\r\nHost: secondary\r\n\r\n"),

    # GET sur /delete secondary → 405
    ("METHOD_GET_ON_DELETE_NOT_ALLOWED",
     405,
     "GET /delete HTTP/1.1\r\nHost: secondary\r\n\r\n"),

    # Méthode inconnue → 405
    ("INVALID_METHOD_UNKNOWN",
     405,
     "HELLO / HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # Méthode en minuscules → 400 (malformé)
    ("INVALID_METHOD_LOWERCASE",
     400,
     "get / HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # Méthode mixte → 400 (malformé)
    ("INVALID_METHOD_MIXEDCASE",
     400,
     "Get / HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # Méthode très longue → 400 ou 405
    ("METHOD_TOO_LONG",
     (400, 405),
     "AVERYLONGMETHODNAME / HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # ══════════════════════════════════════════════════════
    # HEADERS
    # ══════════════════════════════════════════════════════

    # Host manquant → 400
    ("MISSING_HOST",
     400,
     "GET / HTTP/1.1\r\n\r\n"),

    # Header sans deux-points → 400
    ("BROKEN_HEADER_NO_COLON",
     400,
     "GET / HTTP/1.1\r\nHost localhost\r\n\r\n"),

    # Host dupliqué → 400
    ("DOUBLE_HOST",
     400,
     "GET / HTTP/1.1\r\nHost: localhost\r\nHost: localhost\r\n\r\n"),

    # Header sans valeur → 400
    ("HEADER_NO_VALUE",
     400,
     "GET / HTTP/1.1\r\nHost:\r\n\r\n"),

    # Header valeur espaces seulement → 400
    ("HEADER_ONLY_SPACES",
     400,
     "GET / HTTP/1.1\r\nHost:    \r\n\r\n"),

    # CR dans valeur header → 400
    ("HEADER_CR_IN_VALUE",
     400,
     "GET / HTTP/1.1\r\nHost: local\rhost\r\n\r\n"),

    # Null byte dans valeur → 400
    ("HEADER_NULL_BYTE_IN_VALUE",
     400,
     "GET / HTTP/1.1\r\nHost: local\x00host\r\n\r\n"),

    # Header folding obsolète → 400
    ("HEADER_FOLDING_OBSOLETE",
     400,
     "GET / HTTP/1.1\r\nHost: localhost\r\nX-Folded: value\r\n  continuation\r\n\r\n"),

    # Trop de headers → 431
    ("TOO_MANY_HEADERS",
     431,
     "GET / HTTP/1.1\r\nHost: localhost\r\n"
     + "".join(f"X-Header-{i}: value\r\n" for i in range(200)) + "\r\n"),

    # Nom de header très long → 431 ou 400
    ("VERY_LONG_HEADER_NAME",
     (431, 400),
     "GET / HTTP/1.1\r\nHost: localhost\r\n" + "X-" + "A" * 9000 + ": value\r\n\r\n"),

    # Valeur de header très longue → 431 ou 400
    ("VERY_LONG_HEADER_VALUE",
     (431, 400),
     "GET / HTTP/1.1\r\nHost: localhost\r\nX-Custom: " + "A" * 9000 + "\r\n\r\n"),

    # Host avec port → 200
    ("HOST_WITH_PORT",
     200,
     f"GET / HTTP/1.1\r\nHost: localhost:{PORT}\r\n\r\n"),

    # Host en IP → 200
    ("HOST_AS_IP",
     200,
     f"GET / HTTP/1.1\r\nHost: {HOST}\r\n\r\n"),

    # Whitespace avant les deux-points → 400 (RFC 7230 §3.2.4)
    ("HEADER_SPACE_BEFORE_COLON",
     400,
     "GET / HTTP/1.1\r\nHost : localhost\r\n\r\n"),

    # Tab dans le nom du header → 400
    ("HEADER_TAB_IN_NAME",
     400,
     "GET / HTTP/1.1\r\nHos\tt: localhost\r\n\r\n"),

    # Caractère non-ASCII dans le nom du header → 400
    ("HEADER_NON_ASCII_NAME",
     400,
     "GET / HTTP/1.1\r\nHost: localhost\r\nX-Héader: value\r\n\r\n"),

    # Header avec nom vide → 400
    ("HEADER_EMPTY_NAME",
     400,
     "GET / HTTP/1.1\r\nHost: localhost\r\n: value\r\n\r\n"),

    # Null byte dans le nom du header → 400
    ("HEADER_NULL_BYTE_IN_NAME",
     400,
     "GET / HTTP/1.1\r\nHost: localhost\r\nX-\x00Bad: value\r\n\r\n"),

    # Transfer-Encoding inconnu sans CL → 400
    ("HEADER_TE_UNKNOWN_NO_CL",
     400,
     "POST /contacts HTTP/1.1\r\nHost: localhost\r\nTransfer-Encoding: gzip\r\n\r\nhello"),

    # POST avec Content-Type mais sans CL ni TE → 400
    ("HEADER_CONTENT_TYPE_NO_BODY",
     400,
     "POST /contacts HTTP/1.1\r\nHost: localhost\r\nContent-Type: text/plain\r\n\r\n"),

    # Host avec caractères invalides → 400
    ("HEADER_HOST_INVALID_CHARS",
     400,
     "GET / HTTP/1.1\r\nHost: local<host>\r\n\r\n"),

    # Host avec port invalide → 400
    ("HEADER_HOST_INVALID_PORT",
     400,
     "GET / HTTP/1.1\r\nHost: localhost:abc\r\n\r\n"),

    # Host inconnu → 400 ou 404 (serveur peut rejeter ou renvoyer sur default)
    ("HEADER_HOST_UNKNOWN_VHOST",
     (400, 404),
     "GET / HTTP/1.1\r\nHost: unknown.vhost.xyz\r\n\r\n"),

    # ══════════════════════════════════════════════════════
    # BODY — sujet : "maximum allowed size for client request bodies"
    # ══════════════════════════════════════════════════════

    # Body > client_max_body_size → 413
    ("BODY_TOO_BIG",
     413,
     "POST /contacts HTTP/1.1\r\nHost: localhost\r\nContent-Length: 2000000\r\n\r\n" + "A" * 2000000),

    # client_max_body_size 0 sur vhost secondary → 413
    ("BODY_BLOCKED_ON_SECONDARY",
     413,
     "POST / HTTP/1.1\r\nHost: secondary\r\nContent-Length: 5\r\n\r\nhello"),

    # Body exact à la limite → 200 ou 201
    ("BODY_EXACT_MAX_SIZE",
     (200, 201),
     "POST /contacts HTTP/1.1\r\nHost: localhost\r\nContent-Length: 1048576\r\n\r\n" + "A" * 1048576),

    # Content-Length déclaré mais body trop court → 400
    ("BODY_SHORTER_THAN_CL",
     400,
     "POST /contacts HTTP/1.1\r\nHost: localhost\r\nContent-Length: 100\r\n\r\nhello"),

    # Body plus long que CL → comportement variable
    ("BODY_LONGER_THAN_CL",
     (200, 201, 400),
     "POST /contacts HTTP/1.1\r\nHost: localhost\r\nContent-Length: 3\r\n\r\nhello"),

    # Double Content-Length → 400
    ("DOUBLE_CONTENT_LENGTH",
     400,
     "POST /contacts HTTP/1.1\r\nHost: localhost\r\nContent-Length: 5\r\nContent-Length: 10\r\n\r\nhello"),

    # Content-Length négatif → 400
    ("NEGATIVE_CONTENT_LENGTH",
     400,
     "POST /contacts HTTP/1.1\r\nHost: localhost\r\nContent-Length: -1\r\n\r\nhello"),

    # Content-Length non numérique → 400
    ("CONTENT_LENGTH_STRING",
     400,
     "POST /contacts HTTP/1.1\r\nHost: localhost\r\nContent-Length: abc\r\n\r\nhello"),

    # Content-Length flottant → 400
    ("CONTENT_LENGTH_FLOAT",
     400,
     "POST /contacts HTTP/1.1\r\nHost: localhost\r\nContent-Length: 3.5\r\n\r\nhello"),

    # POST sans Content-Length → 400
    ("POST_WITHOUT_CONTENT_LENGTH",
     400,
     "POST /contacts HTTP/1.1\r\nHost: localhost\r\n\r\nhello"),

    # GET avec body → toléré ou 400
    ("GET_WITH_BODY",
     (200, 400),
     "GET / HTTP/1.1\r\nHost: localhost\r\nContent-Length: 5\r\n\r\nhello"),

    # Content-Length 0 sur GET → 200
    ("BODY_CL_ZERO_ON_GET",
     200,
     "GET / HTTP/1.1\r\nHost: localhost\r\nContent-Length: 0\r\n\r\n"),

    # CL très grand sans body → 400 ou 413
    ("BODY_CL_HUGE_NO_BODY",
     (400, 413),
     "POST /contacts HTTP/1.1\r\nHost: localhost\r\nContent-Length: 99999999\r\n\r\n"),

    # DELETE avec body → toléré ou 400
    ("BODY_DELETE_WITH_BODY",
     (200, 204, 400, 404),
     "DELETE /contacts HTTP/1.1\r\nHost: localhost\r\nContent-Length: 5\r\n\r\nhello"),

    # ── Chunked — sujet : "for chunked requests, server needs to un-chunk them"
    # Chunked valide → 200 ou 201
    ("CHUNKED_VALID",
     (200, 201),
     "POST /contacts HTTP/1.1\r\nHost: localhost\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n0\r\n\r\n"),

    # Chunked multi-chunks → 200 ou 201
    ("CHUNKED_MULTI_CHUNK",
     (200, 201),
     "POST /contacts HTTP/1.1\r\nHost: localhost\r\nTransfer-Encoding: chunked\r\n\r\n3\r\nfoo\r\n3\r\nbar\r\n0\r\n\r\n"),

    # Chunked + Content-Length → 400
    ("CHUNKED_AND_CONTENT_LENGTH",
     400,
     "POST /contacts HTTP/1.1\r\nHost: localhost\r\nTransfer-Encoding: chunked\r\nContent-Length: 5\r\n\r\n5\r\nhello\r\n0\r\n\r\n"),

    # Chunked avec extension de chunk → 200/201 ou 400
    ("CHUNKED_WITH_EXTENSION",
     (200, 201, 400),
     "POST /contacts HTTP/1.1\r\nHost: localhost\r\nTransfer-Encoding: chunked\r\n\r\n5;ext=val\r\nhello\r\n0\r\n\r\n"),

    # Chunk size négatif → 400
    ("CHUNKED_NEGATIVE_SIZE",
     400,
     "POST /contacts HTTP/1.1\r\nHost: localhost\r\nTransfer-Encoding: chunked\r\n\r\n-1\r\nhello\r\n0\r\n\r\n"),

    # Chunk size non-hex → 400
    ("CHUNKED_NON_HEX_SIZE",
     400,
     "POST /contacts HTTP/1.1\r\nHost: localhost\r\nTransfer-Encoding: chunked\r\n\r\nZZ\r\nhello\r\n0\r\n\r\n"),

    # Chunk données trop courtes → 400
    ("CHUNKED_TRUNCATED_DATA",
     400,
     "POST /contacts HTTP/1.1\r\nHost: localhost\r\nTransfer-Encoding: chunked\r\n\r\na\r\nhi\r\n0\r\n\r\n"),

    # Chunk sans terminal → 400
    ("CHUNKED_NO_TERMINAL_CHUNK",
     400,
     "POST /contacts HTTP/1.1\r\nHost: localhost\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n"),

    # ══════════════════════════════════════════════════════
    # URI
    # ══════════════════════════════════════════════════════

    # URI trop longue → 414
    ("LONG_URI",
     414,
     "GET /" + "A" * 8000 + " HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # URI vide → 400
    ("EMPTY_URI",
     400,
     "GET  HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # Fragment dans l'URI → 400
    ("URI_WITH_FRAGMENT",
     400,
     "GET /page#section HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # Path traversal → 400 (sujet : sécurité basique attendue)
    ("URI_PATH_TRAVERSAL",
     400,
     "GET /../../../etc/passwd HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # Double slash → 400
    ("URI_DOUBLE_SLASH",
     400,
     "GET //etc/passwd HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # Null byte dans l'URI → 400
    ("URI_NULL_BYTE",
     400,
     "GET /path\x00/hidden HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # Espace non encodé → 400
    ("URI_SPACE_UNENCODED",
     400,
     "GET /path with spaces HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # % incomplet → 400
    ("URI_PERCENT_INCOMPLETE",
     400,
     "GET /path%2 HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # URI avec backslash → 400
    ("URI_BACKSLASH",
     400,
     "GET /path\\to\\file HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # URI avec %00 encodé → 400
    ("URI_ENCODED_NULL",
     400,
     "GET /path%00hidden HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # URI avec caractère de contrôle → 400
    ("URI_CONTROL_CHAR",
     400,
     "GET /path\x01file HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # URI avec query string vide → 200 ou 404
    ("URI_EMPTY_QUERY_STRING",
     (200, 404),
     "GET /? HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # Double encoding de slash → 400 ou 404
    ("URI_DOUBLE_ENCODED_SLASH",
     (400, 404),
     "GET /etc%252Fpasswd HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # ══════════════════════════════════════════════════════
    # PROTOCOL — sujet : "HTTP response status codes must be accurate"
    # ══════════════════════════════════════════════════════

    # Version inconnue → 505
    ("BAD_HTTP_VERSION",
     505,
     "GET / HTTP/9.9\r\nHost: localhost\r\n\r\n"),

    # HTTP/2.0 → 505
    ("HTTP_2_0_NOT_SUPPORTED",
     505,
     "GET / HTTP/2.0\r\nHost: localhost\r\n\r\n"),

    # HTTP/1.0 → 200 ou 505 selon implémentation (sujet ne l'exige pas)
    ("HTTP_1_0",
     (200, 505),
     "GET / HTTP/1.0\r\nHost: localhost\r\n\r\n"),

    # Version en minuscules → 400
    ("LOWERCASE_HTTP_VERSION",
     400,
     "GET / http/1.1\r\nHost: localhost\r\n\r\n"),

    # Pas de version → 400
    ("NO_HTTP_VERSION",
     400,
     "GET /\r\nHost: localhost\r\n\r\n"),

    # Version sans chiffre mineur → 400
    ("HTTP_VERSION_NO_MINOR",
     400,
     "GET / HTTP/1.\r\nHost: localhost\r\n\r\n"),

    # Espace dans la version → 400
    ("HTTP_VERSION_WITH_SPACE",
     400,
     "GET / HTTP/ 1.1\r\nHost: localhost\r\n\r\n"),

    # ══════════════════════════════════════════════════════
    # REQUEST LINE FORMAT
    # ══════════════════════════════════════════════════════

    # Requête vide → 400
    ("EMPTY_REQUEST",
     400,
     "\r\n"),

    # Request line manquante → 400
    ("MISSING_REQUEST_LINE",
     400,
     "\r\nHost: localhost\r\n\r\n"),

    # Espaces supplémentaires → 400
    ("EXTRA_SPACE_IN_REQUEST_LINE",
     400,
     "GET  /  HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # LF seul sans CR → 400
    ("REQUEST_LINE_ONLY_LF",
     400,
     "GET / HTTP/1.1\nHost: localhost\n\n"),

    # CR sans LF → 400
    ("CR_WITHOUT_LF",
     400,
     "GET / HTTP/1.1\rHost: localhost\r\r"),

    # Tab comme séparateur → 400
    ("REQUEST_LINE_TAB_SEPARATOR",
     400,
     "GET\t/\tHTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # CRLF en début → 400 ou 200 selon tolérance
    ("REQUEST_LEADING_CRLF",
     (200, 400),
     "\r\n\r\nGET / HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # ══════════════════════════════════════════════════════
    # FICHIERS STATIQUES — sujet : "serve a fully static website"
    # ══════════════════════════════════════════════════════

    # Fichier inexistant → 404
    ("STATIC_NOT_FOUND",
     404,
     "GET /this_does_not_exist.html HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # Index par défaut → 200
    ("STATIC_INDEX",
     200,
     "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # Fichier statique existant → 200
    ("STATIC_EXISTING_FILE",
     200,
     "GET /index.html HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # ══════════════════════════════════════════════════════
    # PAGES D'ERREUR — sujet : "must have default error pages"
    # Body non vide obligatoire
    # ══════════════════════════════════════════════════════

    ("DEFAULT_ERROR_PAGE_404",
     404,
     "GET /nonexistent HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    ("DEFAULT_ERROR_PAGE_405",
     405,
     "PUT / HTTP/1.1\r\nHost: localhost\r\nContent-Length: 4\r\n\r\ndata"),

    ("DEFAULT_ERROR_PAGE_400",
     400,
     "GET / HTTP/1.1\r\n\r\n"),

    # ══════════════════════════════════════════════════════
    # HEADERS DE RÉPONSE — sujet : "status codes must be accurate"
    # ══════════════════════════════════════════════════════

    ("RESPONSE_HAS_CONTENT_TYPE",
     200,
     "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    ("RESPONSE_HAS_CONTENT_LENGTH_OR_CHUNKED",
     200,
     "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    ("RESPONSE_ERROR_HAS_CONTENT_TYPE",
     404,
     "GET /nonexistent HTTP/1.1\r\nHost: localhost\r\n\r\n"),

    # ══════════════════════════════════════════════════════
    # INJECTION / SÉCURITÉ
    # ══════════════════════════════════════════════════════

    # CRLF injection dans valeur header → 400
    ("HEADER_INJECTION_CRLF",
     400,
     "GET / HTTP/1.1\r\nHost: localhost\r\nX-Evil: val\r\nInjected: header\r\n\r\n"),
]

# ─────────────────────────────────────────────
# Sections
# ─────────────────────────────────────────────
SECTION_PREFIXES = {
    "VALID":                "VALID REQUESTS",
    "UPLOAD":               "UPLOAD",
    "REDIRECT":             "REDIRECTION",
    "LISTING":              "DIRECTORY LISTING",
    "CGI":                  "CGI",
    "METHOD":               "MÉTHODES",
    "INVALID_METHOD":       "MÉTHODES",
    "MISSING_HOST":         "HEADERS",
    "BROKEN":               "HEADERS",
    "DOUBLE_HOST":          "HEADERS",
    "HEADER":               "HEADERS",
    "TOO":                  "HEADERS",
    "VERY_LONG_HEADER":     "HEADERS",
    "HOST":                 "HEADERS",
    "BODY":                 "BODY",
    "POST_WITHOUT":         "BODY",
    "GET_WITH":             "BODY",
    "DOUBLE_CONTENT":       "BODY",
    "NEGATIVE":             "BODY",
    "CONTENT":              "BODY",
    "CHUNKED":              "BODY",
    "LONG_URI":             "URI",
    "EMPTY_URI":            "URI",
    "URI":                  "URI",
    "BAD_HTTP":             "PROTOCOL",
    "HTTP":                 "PROTOCOL",
    "LOWERCASE_HTTP":       "PROTOCOL",
    "NO_HTTP":              "PROTOCOL",
    "EMPTY_REQUEST":        "REQUEST LINE FORMAT",
    "MISSING_REQUEST":      "REQUEST LINE FORMAT",
    "EXTRA":                "REQUEST LINE FORMAT",
    "REQUEST":              "REQUEST LINE FORMAT",
    "CR":                   "REQUEST LINE FORMAT",
    "STATIC":               "FICHIERS STATIQUES",
    "DEFAULT_ERROR":        "PAGES D'ERREUR",
    "RESPONSE":             "HEADERS DE RÉPONSE",
    "SMUGGLE":              "HTTP SMUGGLING",
    "PIPELINE":             "PIPELINING",
    "SLOW":                 "SLOWLORIS / DoS",
    "UNICODE":              "UNICODE / ENCODING",
}

def get_section(name):
    for prefix, section in sorted(SECTION_PREFIXES.items(), key=lambda x: -len(x[0])):
        if name.startswith(prefix):
            return section
    return "OTHER"

passed = 0
failed = 0
errors = 0

def _fmt(expected):
    if isinstance(expected, tuple):
        return "|".join(str(c) for c in expected)
    return str(expected)

def _matches(got, expected):
    if isinstance(expected, tuple):
        return got in expected
    return got == expected

def _pass(name, detail):
    global passed; passed += 1
    print(f"  [{GREEN}PASS{RESET}]  {name:<45} {detail}")

def _fail(name, detail):
    global failed; failed += 1
    print(f"  [{RED}FAIL{RESET}]  {name:<45} {detail}")

def _err(name, expected, detail):
    global errors; errors += 1
    print(f"  [{YELLOW}ERR {RESET}]  {name:<45} {YELLOW}{detail}{RESET}  {DIM}(expected {_fmt(expected)}){RESET}")

def _print_result(name, expected, got_code, got_str, duration):
    exp_label = f"{DIM}expected {BOLD}{_fmt(expected)}{RESET}"
    if _matches(got_code, expected):
        _pass(name, f"{got_str}  {DIM}({duration:.1f} ms){RESET}")
    else:
        _fail(name, f"got [{RED}{got_str}{RESET}]  {exp_label}  ({duration:.1f} ms)")

def send_test(name, expected, request):
    try:
        s = socket.socket()
        s.settimeout(5)
        start = time.time()
        s.connect((HOST, PORT))
        s.send(request.encode(errors="surrogateescape"))
        response = s.recv(4096)
        duration = (time.time() - start) * 1000
        s.close()

        if not response:
            _print_result(name, expected, None, "NO RESPONSE", duration)
            return

        raw       = response.decode(errors="ignore")
        first_line = raw.split("\r\n")[0]
        parts      = first_line.split(" ", 2)
        got_code   = int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else None
        headers_raw = raw.split("\r\n\r\n", 1)[0].lower()

        # ── Directory listing : body doit contenir du HTML avec des liens ──
        if name == "LISTING_ENABLED" and _matches(got_code, expected):
            body_content = raw.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in raw else ""
            if "<a " in body_content.lower() or "<li>" in body_content.lower() or "sample.txt" in body_content:
                _pass(name, f"{first_line} — listing HTML présent  {DIM}({duration:.1f} ms){RESET}")
            else:
                _fail(name, f"got [{first_line}] mais pas de listing dans le body  ({duration:.1f} ms)")
            return

        # ── Redirection : vérifier header Location ──
        if name.startswith("REDIRECT_") and _matches(got_code, expected):
            if "location:" in headers_raw:
                _pass(name, f"{first_line} — Location présent  {DIM}({duration:.1f} ms){RESET}")
            else:
                _fail(name, f"got [{first_line}] mais header Location absent  ({duration:.1f} ms)")
            return

        # ── CGI : body doit contenir la sortie du script ──
        if name == "CGI_GET_PYTHON" and _matches(got_code, expected):
            body_content = raw.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in raw else ""
            if "Hello from CGI" in body_content or len(body_content.strip()) > 0:
                _pass(name, f"{first_line} — CGI output présent  {DIM}({duration:.1f} ms){RESET}")
            else:
                _fail(name, f"got [{first_line}] mais CGI body vide  ({duration:.1f} ms)")
            return

        if name == "RESPONSE_HAS_CONTENT_TYPE":
            if "content-type:" in headers_raw:
                _pass(name, f"{first_line} — Content-Type présent  {DIM}({duration:.1f} ms){RESET}")
            else:
                _fail(name, f"got [{first_line}] mais Content-Type absent  ({duration:.1f} ms)")
            return

        if name == "RESPONSE_HAS_CONTENT_LENGTH_OR_CHUNKED":
            has_cl = "content-length:" in headers_raw
            has_te = "transfer-encoding: chunked" in headers_raw
            if has_cl or has_te:
                which = "Content-Length" if has_cl else "Transfer-Encoding: chunked"
                _pass(name, f"{first_line} — {which} présent  {DIM}({duration:.1f} ms){RESET}")
            else:
                _fail(name, f"got [{first_line}] mais ni Content-Length ni Transfer-Encoding  ({duration:.1f} ms)")
            return

        if name == "RESPONSE_ERROR_HAS_CONTENT_TYPE":
            if _matches(got_code, expected) and "content-type:" in headers_raw:
                _pass(name, f"{first_line} — Content-Type présent sur erreur  {DIM}({duration:.1f} ms){RESET}")
            elif not _matches(got_code, expected):
                _fail(name, f"got [{RED}{first_line}{RESET}]  {DIM}expected {BOLD}{_fmt(expected)}{RESET}  ({duration:.1f} ms)")
            else:
                _fail(name, f"got [{first_line}] mais Content-Type absent sur réponse d'erreur  ({duration:.1f} ms)")
            return

        # ── Pages d'erreur : body non vide ──
        if name.startswith("DEFAULT_ERROR") and _matches(got_code, expected):
            body = raw
            content = body.split("\r\n\r\n", 1)[1].strip() if "\r\n\r\n" in body else ""
            if content:
                _pass(name, f"{first_line} + body présent  {DIM}({duration:.1f} ms){RESET}")
            else:
                _fail(name, f"got [{first_line}] mais body vide — page d'erreur manquante  ({duration:.1f} ms)")
            return

        _print_result(name, expected, got_code, first_line, duration)

    except Exception as e:
        err_str = str(e)
        if expected == "TIMEOUT" and "timed out" in err_str:
            _pass(name, "timed out as expected")
        else:
            _err(name, expected, err_str)

# ─────────────────────────────────────────────
# COMPLEX TESTS
# ─────────────────────────────────────────────

def test_smuggle_cl_te():
    """TE + CL ensemble → 400"""
    name, expected = "SMUGGLE_CL_TE", 400
    payload = (
        "POST /contacts HTTP/1.1\r\nHost: localhost\r\n"
        "Content-Length: 11\r\nTransfer-Encoding: chunked\r\n\r\n"
        "0\r\n\r\nG"
    )
    try:
        s = socket.socket(); s.settimeout(3); start = time.time()
        s.connect((HOST, PORT)); s.send(payload.encode())
        resp = b""
        while True:
            chunk = s.recv(4096)
            if not chunk: break
            resp += chunk
        duration = (time.time() - start) * 1000; s.close()
        fl = resp.decode(errors="ignore").split("\r\n")[0]
        p  = fl.split(" ", 2)
        _print_result(name, expected, int(p[1]) if len(p)>=2 and p[1].isdigit() else None, fl, duration)
    except Exception as e: _err(name, expected, str(e))

def test_smuggle_te_obfuscated():
    """TE obfusqué (xchunked) → 400"""
    name, expected = "SMUGGLE_TE_OBFUSCATED", 400
    payload = (
        "POST /contacts HTTP/1.1\r\nHost: localhost\r\n"
        "Transfer-Encoding: xchunked\r\nContent-Length: 5\r\n\r\nhello"
    )
    try:
        s = socket.socket(); s.settimeout(3); start = time.time()
        s.connect((HOST, PORT)); s.send(payload.encode())
        resp = s.recv(4096); duration = (time.time() - start) * 1000; s.close()
        fl = resp.decode(errors="ignore").split("\r\n")[0]
        p  = fl.split(" ", 2)
        _print_result(name, expected, int(p[1]) if len(p)>=2 and p[1].isdigit() else None, fl, duration)
    except Exception as e: _err(name, expected, str(e))

def test_smuggle_chunk_overflow():
    """Chunk size overflow → 400"""
    name, expected = "SMUGGLE_CHUNK_OVERFLOW", 400
    payload = (
        "POST /contacts HTTP/1.1\r\nHost: localhost\r\n"
        "Transfer-Encoding: chunked\r\n\r\n"
        "FFFFFFFFFFFFFFFF\r\nhello\r\n0\r\n\r\n"
    )
    try:
        s = socket.socket(); s.settimeout(3); start = time.time()
        s.connect((HOST, PORT)); s.send(payload.encode())
        resp = s.recv(4096); duration = (time.time() - start) * 1000; s.close()
        fl = resp.decode(errors="ignore").split("\r\n")[0]
        p  = fl.split(" ", 2)
        _print_result(name, expected, int(p[1]) if len(p)>=2 and p[1].isdigit() else None, fl, duration)
    except Exception as e: _err(name, expected, str(e))

def test_pipeline_two_gets():
    """Pipelining : 2 GET dans un seul write → 2 × 200"""
    name, expected = "PIPELINE_TWO_GETS", 200
    payload = (
        "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
        "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
    )
    try:
        s = socket.socket(); s.settimeout(3); start = time.time()
        s.connect((HOST, PORT)); s.send(payload.encode())
        resp = b""
        while True:
            try:
                chunk = s.recv(4096)
                if not chunk: break
                resp += chunk
            except socket.timeout: break
        duration = (time.time() - start) * 1000; s.close()
        responses = [l for l in resp.decode(errors="ignore").split("\r\n") if l.startswith("HTTP/")]
        count_200 = sum(1 for r in responses if "200" in r)
        if count_200 >= 2:
            _pass(name, f"got {count_200}× 200 OK  ({duration:.1f} ms)")
        else:
            _fail(name, f"got {responses}  expected 2× 200 OK  ({duration:.1f} ms)")
    except Exception as e: _err(name, expected, str(e))

def test_pipeline_post_then_get():
    """Pipelining : POST /contacts + GET / → 2 réponses"""
    name, expected = "PIPELINE_POST_THEN_GET", (200, 201)
    payload = (
        "POST /contacts HTTP/1.1\r\nHost: localhost\r\nContent-Length: 5\r\n\r\nhello"
        "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
    )
    try:
        s = socket.socket(); s.settimeout(3); start = time.time()
        s.connect((HOST, PORT)); s.send(payload.encode())
        resp = b""
        while True:
            try:
                chunk = s.recv(4096)
                if not chunk: break
                resp += chunk
            except socket.timeout: break
        duration = (time.time() - start) * 1000; s.close()
        responses = [l for l in resp.decode(errors="ignore").split("\r\n") if l.startswith("HTTP/")]
        if len(responses) >= 2:
            _pass(name, f"got {len(responses)} réponses  ({duration:.1f} ms)")
        else:
            _fail(name, f"got seulement {len(responses)} réponse(s): {responses}  ({duration:.1f} ms)")
    except Exception as e: _err(name, expected, str(e))

def test_slow_body():
    """Slow body — sujet: 'never hang indefinitely' → 408"""
    name, expected = "SLOW_BODY_INCOMPLETE", 408
    headers = "POST /contacts HTTP/1.1\r\nHost: localhost\r\nContent-Length: 100\r\n\r\n"
    try:
        s = socket.socket(); s.settimeout(10); start = time.time()
        s.connect((HOST, PORT))
        s.send(headers.encode())
        s.send(b"A" * 10)
        time.sleep(4)
        resp = s.recv(4096); duration = (time.time() - start) * 1000; s.close()
        fl = resp.decode(errors="ignore").split("\r\n")[0]
        p  = fl.split(" ", 2)
        got = int(p[1]) if len(p)>=2 and p[1].isdigit() else None
        if got == 408:
            _pass(name, f"{fl}  ({duration:.1f} ms)")
        else:
            _fail(name, f"got [{fl}]  {DIM}expected {BOLD}408{RESET}  ({duration:.1f} ms)")
    except socket.timeout:
        _fail(name, "server never responded — VULNERABLE au slow-body DoS")
    except Exception as e: _err(name, expected, str(e))

def test_slow_many_connections():
    """50 conns half-open + 1 légitime — sujet: 'remains available at all times'"""
    name, expected = "SLOW_CONNECTION_EXHAUSTION", 200
    N = 50
    sockets = []
    incomplete = "GET / HTTP/1.1\r\nHost: localhost\r\nX-Padding: " + "A" * 100
    for _ in range(N):
        try:
            s = socket.socket(); s.settimeout(2)
            s.connect((HOST, PORT)); s.send(incomplete.encode())
            sockets.append(s)
        except Exception: break
    try:
        s = socket.socket(); s.settimeout(3); start = time.time()
        s.connect((HOST, PORT))
        s.send(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
        resp = s.recv(4096); duration = (time.time() - start) * 1000; s.close()
        fl = resp.decode(errors="ignore").split("\r\n")[0]
        p  = fl.split(" ", 2)
        got = int(p[1]) if len(p)>=2 and p[1].isdigit() else None
        _print_result(name, expected, got, f"{fl} (après {len(sockets)} conns lentes)", duration)
    except Exception as e: _err(name, expected, str(e))
    finally:
        for s in sockets:
            try: s.close()
            except Exception: pass

def test_unicode_traversal():
    """Double percent-encoding '../' → 400 ou 404"""
    name, expected = "UNICODE_DOUBLE_PERCENT_TRAVERSAL", (400, 404)
    payload = b"GET /%252e%252e%252fetc%252fpasswd HTTP/1.1\r\nHost: localhost\r\n\r\n"
    try:
        s = socket.socket(); s.settimeout(3); start = time.time()
        s.connect((HOST, PORT)); s.send(payload)
        resp = s.recv(4096); duration = (time.time() - start) * 1000; s.close()
        fl = resp.decode(errors="ignore").split("\r\n")[0]
        p  = fl.split(" ", 2)
        got = int(p[1]) if len(p)>=2 and p[1].isdigit() else None
        _print_result(name, expected, got, fl, duration)
    except Exception as e: _err(name, expected, str(e))

def test_unicode_overlong_slash():
    """Overlong UTF-8 de '/' → 400"""
    name, expected = "UNICODE_OVERLONG_SLASH", 400
    payload = b"GET /\xc0\xafetc\xc0\xafpasswd HTTP/1.1\r\nHost: localhost\r\n\r\n"
    try:
        s = socket.socket(); s.settimeout(3); start = time.time()
        s.connect((HOST, PORT)); s.send(payload)
        resp = s.recv(4096); duration = (time.time() - start) * 1000; s.close()
        fl = resp.decode(errors="ignore").split("\r\n")[0]
        p  = fl.split(" ", 2)
        got = int(p[1]) if len(p)>=2 and p[1].isdigit() else None
        _print_result(name, expected, got, fl, duration)
    except Exception as e: _err(name, expected, str(e))

# ─────────────────────────────────────────────
# CLI COMMANDS
# ─────────────────────────────────────────────

def cmd_help(args=None):
    print(f"""
{BOLD}{'='*66}{RESET}
{BOLD}  WEBSERV 42 — HTTP TESTER  —  usage{RESET}
{BOLD}{'='*66}{RESET}

  {BOLD}python3 tester.py {CYAN}<commande>{RESET} {DIM}[--host HOST] [--port PORT]{RESET}

  {CYAN}{BOLD}Commandes :{RESET}

    {BOLD}{GREEN}init{RESET}
        Crée l'infrastructure de test (www/, logs/, pages HTML,
        tester.conf). À lancer une seule fois avant de démarrer
        le serveur. Ne recrée pas les fichiers déjà présents.
        Le tester.conf généré utilise le host et le port fournis.

    {BOLD}{GREEN}run{RESET}
        Lance tous les tests HTTP contre le serveur.
        Vérifie d'abord que l'infrastructure existe et que le
        serveur répond sur le host:port cible.

    {BOLD}{GREEN}check{RESET}
        Vérifie si l'infrastructure est en place et si le
        serveur est joignable. N'exécute aucun test.

    {BOLD}{GREEN}clean{RESET}
        Supprime toute l'infrastructure générée (www/, logs/,
        tester.conf). Utile pour repartir de zéro.

    {BOLD}{GREEN}help{RESET}
        Affiche ce message.

  {CYAN}{BOLD}Options :{RESET}

    {BOLD}--host{RESET} {CYAN}ADDR{RESET}   Adresse IP du serveur  {DIM}(défaut : {DEFAULT_HOST}){RESET}
    {BOLD}--port{RESET} {CYAN}PORT{RESET}   Port du serveur        {DIM}(défaut : {DEFAULT_PORT}){RESET}

  {CYAN}{BOLD}Exemples :{RESET}

    python3 tester.py {GREEN}init{RESET}
    python3 tester.py {GREEN}run{RESET}
    python3 tester.py {GREEN}run{RESET}  --port 9090
    python3 tester.py {GREEN}run{RESET}  --host 127.0.2.1 --port 8080
    python3 tester.py {GREEN}init{RESET} --host 127.0.2.1 --port 9090
    python3 tester.py {GREEN}check{RESET} --port 9090
    python3 tester.py {GREEN}clean{RESET}

  {CYAN}{BOLD}Workflow typique :{RESET}

    {DIM}1.{RESET}  python3 tester.py {GREEN}init{RESET} {DIM}[--host X] [--port Y]{RESET}
    {DIM}2.{RESET}  ./webserv tester.conf
    {DIM}3.{RESET}  python3 tester.py {GREEN}run{RESET}  {DIM}[--host X] [--port Y]{RESET}

  {CYAN}{BOLD}Configuration active :{RESET}

    Host    : {BOLD}{HOST}{RESET}
    Port    : {BOLD}{PORT}{RESET}
    Racine  : {BOLD}{WEB_ROOT}{RESET}
    Logs    : {BOLD}{LOGS_DIR}{RESET}
    Config  : {BOLD}{os.path.join(BASE_DIR, 'tester.conf')}{RESET}

{BOLD}{'='*66}{RESET}
""")

def cmd_init(args=None):
    if infrastructure_exists():
        print(f"\n{BOLD}{'='*66}{RESET}")
        print(f"{BOLD}  INIT — Infrastructure{RESET}")
        print(f"{BOLD}{'='*66}{RESET}")
        print(f"  {YELLOW}L'infrastructure est déjà en place.{RESET}")
        print(f"  {DIM}Aucun fichier écrasé. Utilisez {BOLD}clean{RESET}{DIM} pour repartir de zéro.{RESET}")
        print(f"{BOLD}{'='*66}{RESET}\n")
        return
    setup_environment()
    print(f"\n{BOLD}{'='*66}{RESET}")
    print(f"  {GREEN}{BOLD}Infrastructure prête.{RESET}")
    print(f"  Lance ton serveur avec :")
    print(f"  {BOLD}    ./webserv {os.path.join(BASE_DIR, 'tester.conf')}{RESET}")
    print(f"  puis : {BOLD}python3 tester.py run{RESET}")
    print(f"{BOLD}{'='*66}{RESET}\n")

def cmd_check(args=None):
    print(f"\n{BOLD}{'='*66}{RESET}")
    print(f"{BOLD}  CHECK — État de l'environnement{RESET}")
    print(f"{BOLD}{'='*66}{RESET}")

    infra_ok = infrastructure_exists()
    print(f"  Infrastructure  : ", end="")
    if infra_ok:
        print(f"{GREEN}OK{RESET}")
    else:
        print(f"{RED}MANQUANTE{RESET}  {DIM}→ lance : python3 tester.py init{RESET}")

    print(f"  Serveur {HOST}:{PORT} : ", end="", flush=True)
    if server_is_up():
        print(f"{GREEN}OK{RESET}")
    else:
        print(f"{RED}injoignable{RESET}  {DIM}→ lance : ./webserv tester.conf{RESET}")

    print(f"{BOLD}{'='*66}{RESET}\n")

def cmd_clean(args=None):
    import shutil
    print(f"\n{BOLD}{'='*66}{RESET}")
    print(f"{BOLD}  CLEAN — Suppression de l'infrastructure{RESET}")
    print(f"{BOLD}{'='*66}{RESET}")

    targets = [
        os.path.join(BASE_DIR, "tester.conf"),
        WEB_ROOT,
        LOGS_DIR,
    ]
    removed = []
    missing = []

    for path in targets:
        if os.path.exists(path):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                removed.append(path)
            except Exception as e:
                print(f"  {RED}[ERREUR]{RESET} Impossible de supprimer {path} : {e}")
        else:
            missing.append(path)

    if removed:
        print(f"  {RED}Supprimés :{RESET}")
        for p in removed:
            print(f"    {RED}-{RESET} {p}")
    if missing:
        print(f"  {DIM}Déjà absents :{RESET}")
        for p in missing:
            print(f"    {DIM}· {p}{RESET}")

    print(f"\n  {GREEN}Clean terminé.{RESET}")
    print(f"{BOLD}{'='*66}{RESET}\n")

def cmd_run(args=None):
    # Vérifie l'infrastructure
    if not infrastructure_exists():
        print(f"\n  {RED}{BOLD}Infrastructure manquante.{RESET}")
        print(f"  {YELLOW}Lance d'abord :{RESET} {BOLD}python3 tester.py init{RESET}\n")
        sys.exit(1)

    # Vérifie le serveur
    print(f"\n{BOLD}{'='*66}{RESET}")
    print(f"{BOLD}  RUN — Vérification du serveur{RESET}")
    print(f"{BOLD}{'='*66}{RESET}")
    print(f"  Connexion à {HOST}:{PORT} ...", end=" ", flush=True)
    if not server_is_up():
        print(f"{RED}injoignable{RESET}")
        print(f"\n  {RED}{BOLD}Le serveur ne répond pas.{RESET}")
        print(f"  {YELLOW}Lance ton serveur avec :{RESET} {BOLD}./webserv {os.path.join(BASE_DIR, 'tester.conf')}{RESET}")
        print(f"{BOLD}{'='*66}{RESET}\n")
        sys.exit(1)
    print(f"{GREEN}OK{RESET}")

    # Lance les tests
    print(f"\n{BOLD}{'='*66}{RESET}")
    print(f"{BOLD}  WEBSERV 42 — HTTP TESTER  —  {HOST}:{PORT}{RESET}")
    print(f"{BOLD}  Config : tester.conf{RESET}")
    print(f"{BOLD}  Vhost default   → /  /contacts{RESET}")
    print(f"{BOLD}  Vhost secondary → /upload  /delete{RESET}")
    print(f"{BOLD}  expected X|Y = plusieurs codes acceptés{RESET}")
    print(f"{BOLD}{'='*66}{RESET}")

    current_section = None
    for name, expected, request in tests:
        section = get_section(name)
        if section != current_section:
            current_section = section
            print(f"\n  {CYAN}{BOLD}── {section} ──{RESET}")
        send_test(name, expected, request)

    complex_tests = [
        ("HTTP SMUGGLING",     [test_smuggle_cl_te, test_smuggle_te_obfuscated, test_smuggle_chunk_overflow]),
        ("PIPELINING",         [test_pipeline_two_gets, test_pipeline_post_then_get]),
        ("SLOWLORIS / DoS",    [test_slow_body, test_slow_many_connections]),
        ("UNICODE / ENCODING", [test_unicode_traversal, test_unicode_overlong_slash]),
    ]
    for section_name, fns in complex_tests:
        print(f"\n  {MAGENTA}{BOLD}── {section_name} (COMPLEX) ──{RESET}")
        for fn in fns:
            fn()

    total  = passed + failed + errors
    bar_w  = 30
    p_fill = int(bar_w * passed / total) if total else 0
    f_fill = int(bar_w * failed / total) if total else 0
    e_fill = bar_w - p_fill - f_fill
    bar    = f"{GREEN}{'█'*p_fill}{RED}{'█'*f_fill}{YELLOW}{'█'*e_fill}{RESET}"

    print(f"\n{BOLD}{'='*66}{RESET}")
    print(f"  {bar}  {BOLD}{GREEN}{passed} passed{RESET} / {RED}{failed} failed{RESET} / {YELLOW}{errors} errors{RESET} / {total} total")
    print(f"{BOLD}{'='*66}{RESET}\n")

# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

import argparse

COMMANDS = {
    "init":  cmd_init,
    "run":   cmd_run,
    "check": cmd_check,
    "clean": cmd_clean,
    "help":  cmd_help,
}

parser = argparse.ArgumentParser(
    prog="tester.py",
    add_help=False,   # on gère help nous-mêmes
)
parser.add_argument("command", nargs="?", default=None,
                    choices=list(COMMANDS.keys()),
                    metavar="commande",
                    help="init | run | check | clean | help")
parser.add_argument("--host", default=DEFAULT_HOST,
                    metavar="ADDR",
                    help=f"Adresse IP du serveur (défaut : {DEFAULT_HOST})")
parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                    metavar="PORT",
                    help=f"Port du serveur (défaut : {DEFAULT_PORT})")

args, unknown = parser.parse_known_args()

if unknown:
    print(f"\n  {RED}Option(s) inconnue(s) : {' '.join(unknown)}{RESET}")
    print(f"  {DIM}→ python3 tester.py help{RESET}\n")
    sys.exit(1)

# Applique host/port globalement
HOST = args.host
PORT = args.port

# Dispatch
if args.command is None:
    if not infrastructure_exists():
        cmd_init()
    else:
        cmd_run()
else:
    COMMANDS[args.command](args)