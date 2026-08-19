import sqlite3
import csv
import os

def export_to_csv():
    """Exporta os dados da tabela de produtos do SQLite para um arquivo CSV."""
    # Caminho do banco de dados (ajustar conforme estrutura do projeto)
    db_path = 'data/farmacia.db'
    export_dir = 'data/exports'
    
    # Cria o diretório de exportação se não existir
    os.makedirs(export_dir, exist_ok=True)
    
    # Conecta ao banco de dados SQLite
    # Verifica se o arquivo existe para evitar erro
    if not os.path.exists(db_path):
        print(f"Banco de dados não encontrado em {db_path}. Execute a aplicação primeiro para criar o banco de dados.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Pega todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table_name in tables:
            table_name = table_name[0]
            # Extrai os dados da tabela
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            if not rows:
                continue
                
            # Extrai o nome das colunas
            col_names = [description[0] for description in cursor.description]
            
            # Exporta para CSV
            csv_path = os.path.join(export_dir, f"{table_name}.csv")
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(col_names)
                writer.writerows(rows)
            print(f"Exportado: {table_name} -> {csv_path}")
            
    except Exception as e:
        print(f"Erro ao exportar dados: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    export_to_csv()
    print("Processo de exportação finalizado.")
