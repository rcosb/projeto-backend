import argparse
import requests
import sys

BASE = 'http://localhost:8000'

def create(args):
    payload = {'titulo': args.title, 'descricao': args.description, 'status': args.status}
    r = requests.post(f'{BASE}/tasks', json=payload)
    if r.status_code == 201:
        print('Tarefa criada:', r.json())
    else:
        print('Erro ao criar:', r.status_code, r.text)

def list_all(args):
    r = requests.get(f'{BASE}/tasks')
    if r.status_code == 200:
        tasks = r.json()
        if not tasks:
            print('Nenhuma tarefa encontrada.')
            return
        for t in tasks:
            print("-------------------")
            print(f"ID:[{t['id']}]")
            print(f"Título:{t['titulo']}")
            print(f"Status:{t['status']}")
            print(f"criado em: {t['criado_em']}")
            if t.get('descricao'):
                print('Descricao:', t['descricao'])
    else:
        print('Erro:', r.status_code, r.text)

def get(args):
    r = requests.get(f'{BASE}/tasks/{args.id}')
    if r.status_code == 200:
        t = r.json()
        print("-------------------")
        print(f"ID:[{t['id']}]")
        print(f"Título:{t['titulo']}")
        print(f"Status:{t['status']}")
        print(f"criado em: {t['criado_em']}")
        if t.get('descricao'):
            print('Descricao:', t['descricao'])
    else:
        print('Erro:', r.status_code, r.text)

def update(args):
    payload = {}
    if args.title: payload['titulo'] = args.title
    if args.description: payload['descricao'] = args.description
    if args.status: payload['status'] = args.status
    if not payload:
        print('Nada para atualizar. Use --title/--description/--status.')
        return
    r = requests.put(f'{BASE}/tasks/{args.id}', json=payload)
    if r.status_code == 200:
        print('Atualizado com sucesso.')
    else:
        print('Erro:', r.status_code, r.text)

def delete(args):
    r = requests.delete(f'{BASE}/tasks/{args.id}')
    if r.status_code == 200:
        print('Deletado com sucesso.')
    else:
        print('Erro:', r.status_code, r.text)

def main():
    parser = argparse.ArgumentParser(description='Cliente CLI para ToDo API')
    sub = parser.add_subparsers(dest='cmd')

    p = sub.add_parser('create')
    p.add_argument('--title', required=True)
    p.add_argument('--description', default='')
    p.add_argument('--status', default='pendente')
    p.set_defaults(func=create)

    p = sub.add_parser('list')
    p.set_defaults(func=list_all)

    p = sub.add_parser('get')
    p.add_argument('id', type=int)
    p.set_defaults(func=get)

    p = sub.add_parser('update')
    p.add_argument('id', type=int)
    p.add_argument('--title')
    p.add_argument('--description')
    p.add_argument('--status')
    p.set_defaults(func=update)

    p = sub.add_parser('delete')
    p.add_argument('id', type=int)
    p.set_defaults(func=delete)

    args = parser.parse_args()
    if not hasattr(args, 'func'):
        parser.print_help()
        sys.exit(1)
    args.func(args)

if __name__ == '__main__':
    main()
