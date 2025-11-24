from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    # Ensure data directory exists
    if not os.path.exists('data'):
        os.makedirs('data')
    app.run(host='0.0.0.0', port=5000, debug=True)
