from src.db import init_db, seed_clients_if_empty, seed_demo_tickets

if __name__ == "__main__":
    init_db()
    seed_clients_if_empty()
    seed_demo_tickets()
    print("Banco inicializado com clientes e tickets de demonstração.")
