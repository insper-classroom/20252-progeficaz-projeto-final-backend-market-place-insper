from pymongo import MongoClient

def conectar_banco():
    """
    Estabelece conexão com o MongoDB e retorna o banco de dados 'uniride'
    
    Returns:
        Database: Referência para o banco de dados 'uniride'
    """
    try:
        # Conecta ao servidor MongoDB
        # Substitua o URL pela sua string de conexão completa se necessário
        client = MongoClient('mongodb+srv://admin:admin@clustereficaz.j4vdwxj.mongodb.net/')
        
        # Obtém a referência para o banco de dados 'uniride'
        db = client['marketplace']
        
        print("Conexão com o banco de dados 'marketplace' estabelecida com sucesso!")
        
        # Cria uma coleção inicial para garantir que o banco seja criado
        # Você pode remover isto se quiser criar coleções separadamente
        db.usuarios.insert_one({"_id": "inicial", "info": "Documento inicial para criar o banco de dados"})
        
        return db
    
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

# Se este arquivo for executado diretamente (não importado)
if __name__ == "__main__":
    db = conectar_banco()
    if db:
        print("Banco de dados criado e pronto para uso!")
        # Liste as coleções para verificar
        colecoes = db.list_collection_names()
        print(f"Coleções disponíveis: {colecoes}")