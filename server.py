
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import json
import sqlite3
import urllib.parse
from datetime import datetime

DB = 'tasks.db'

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        descricao TEXT,
        status TEXT NOT NULL DEFAULT 'pendente',
        criado_em TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

class SimpleHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', content_type + '; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def parse_path(self):
        parsed = urllib.parse.urlparse(self.path)
        parts = [p for p in parsed.path.split('/') if p]
        if len(parts) == 0:
            return (None, None)
        if parts[0] != 'tasks':
            return (parts[0], parts[1] if len(parts) > 1 else None)
        if len(parts) == 1:
            return ('tasks', None)
        # tentar converter id para inteiro
        try:
            tid = int(parts[1])
        except:
            return ('tasks', 'invalid')  # id inválido
        return ('tasks', tid)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.end_headers()

    def do_GET(self):
        resource, tid = self.parse_path()
        if resource != 'tasks':
            self._set_headers(404)
            self.wfile.write(json.dumps({'error':'Rota não encontrada'}).encode('utf-8'))
            return
        if tid == 'invalid':
            self._set_headers(400)
            self.wfile.write(json.dumps({'error':'ID inválido'}).encode('utf-8'))
            return

        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        if tid is None:
            cur.execute('SELECT id, titulo, descricao, status, criado_em FROM tasks')
            rows = cur.fetchall()
            tasks = [{'id': r[0], 'titulo': r[1], 'descricao': r[2], 'status': r[3], 'criado_em': r[4]} for r in rows]
            self._set_headers(200)
            self.wfile.write(json.dumps(tasks, ensure_ascii=False).encode('utf-8'))
        else:
            cur.execute('SELECT id, titulo, descricao, status, criado_em FROM tasks WHERE id=?', (tid,))
            r = cur.fetchone()
            if r:
                task = {'id': r[0], 'titulo': r[1], 'descricao': r[2], 'status': r[3], 'criado_em': r[4]}
                self._set_headers(200)
                self.wfile.write(json.dumps(task, ensure_ascii=False).encode('utf-8'))
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({'error': 'Tarefa não encontrada'}).encode('utf-8'))
        conn.close()

    def do_POST(self):
        resource, tid = self.parse_path()
        if resource != 'tasks' or tid is not None:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error':'Rota não encontrada'}).encode('utf-8'))
            return
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len)
        try:
            data = json.loads(body.decode('utf-8'))
            titulo = data.get('titulo')
            descricao = data.get('descricao')
            status = data.get('status', 'pendente')
            if not titulo:
                raise ValueError('campo "titulo" é obrigatório')
        except Exception as e:
            self._set_headers(400)
            self.wfile.write(json.dumps({'error': 'JSON inválido ou campo faltando', 'details': str(e)}).encode('utf-8'))
            return

        criado_em = datetime.now().isoformat()
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute('INSERT INTO tasks (titulo, descricao, status, criado_em) VALUES (?,?,?,?)',
                    (titulo, descricao, status, criado_em))
        conn.commit()
        task_id = cur.lastrowid
        conn.close()
        self._set_headers(201)
        self.wfile.write(json.dumps({'id': task_id, 'titulo': titulo, 'descricao': descricao, 'status': status, 'criado_em': criado_em}, ensure_ascii=False).encode('utf-8'))

    def do_PUT(self):
        resource, tid = self.parse_path()
        if resource != 'tasks' or isinstance(tid, str) and tid != 'invalid' and tid is None:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error':'Rota não encontrada'}).encode('utf-8'))
            return
        if tid == 'invalid' or tid is None:
            self._set_headers(400)
            self.wfile.write(json.dumps({'error':'ID inválido ou faltando'}).encode('utf-8'))
            return
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len)
        try:
            data = json.loads(body.decode('utf-8'))
        except Exception as e:
            self._set_headers(400)
            self.wfile.write(json.dumps({'error':'JSON inválido', 'details': str(e)}).encode('utf-8'))
            return

        allowed = ['titulo', 'descricao', 'status']
        updates = []
        values = []
        for key in allowed:
            if key in data:
                updates.append(f"{key} = ?")
                values.append(data[key])
        if not updates:
            self._set_headers(400)
            self.wfile.write(json.dumps({'error':'Nenhum campo para atualizar'}).encode('utf-8'))
            return
        values.append(tid)

        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute('SELECT id FROM tasks WHERE id=?', (tid,))
        if not cur.fetchone():
            self._set_headers(404)
            self.wfile.write(json.dumps({'error':'Tarefa não encontrada'}).encode('utf-8'))
            conn.close()
            return
        sql = 'UPDATE tasks SET ' + ', '.join(updates) + ' WHERE id=?'
        cur.execute(sql, tuple(values))
        conn.commit()
        conn.close()
        self._set_headers(200)
        self.wfile.write(json.dumps({'message': 'Atualizado com sucesso'}).encode('utf-8'))

    def do_DELETE(self):
        resource, tid = self.parse_path()
        if resource != 'tasks' or tid is None or tid == 'invalid':
            self._set_headers(404)
            self.wfile.write(json.dumps({'error':'Rota não encontrada ou ID inválido'}).encode('utf-8'))
            return
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute('SELECT id FROM tasks WHERE id=?', (tid,))
        if not cur.fetchone():
            self._set_headers(404)
            self.wfile.write(json.dumps({'error':'Tarefa não encontrada'}).encode('utf-8'))
            conn.close()
            return
        cur.execute('DELETE FROM tasks WHERE id=?', (tid,))
        conn.commit()
        conn.close()
        self._set_headers(200)
        self.wfile.write(json.dumps({'message':'Deletado com sucesso'}).encode('utf-8'))

def run(port=8000):
    init_db()
    server_address = ('', port)
    httpd = ThreadingHTTPServer(server_address, SimpleHandler)
    print(f"Servidor rodando em http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando servidor")
        httpd.server_close()

if __name__ == '__main__':
    run()
