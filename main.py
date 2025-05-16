from app import app

if __name__ == '__main__':
    # Imposta l'ambiente per la connessione
    import os
    os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/postgres')
    app.run(host='0.0.0.0', port=5000, debug=True)
