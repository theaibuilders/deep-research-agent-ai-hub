.PHONY: dev-backend dev-frontend dev install-backend install-frontend install

# Start the Python backend server
dev-backend:
	cd services/backend && python3 main.py

# Start the React frontend dev server
dev-frontend:
	cd services/frontend && npm run dev

# Start both services (backend in background, frontend in foreground)
dev:
	@echo "Starting backend..."
	cd services/backend && python3 main.py &
	@echo "Starting frontend..."
	cd services/frontend && npm run dev

# Install backend dependencies
install-backend:
	cd services/backend && pip3 install -r requirements.txt

# Install frontend dependencies
install-frontend:
	cd services/frontend && npm install

# Install all dependencies
install: install-backend install-frontend
