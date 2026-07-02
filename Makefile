.PHONY: help install run run-backend run-dashboard docker-up docker-down clean logs lint test docs

# ─── Colores ─────────────────────────────────────────────────
GREEN  := \033[0;32m
YELLOW := \033[1;33m
RED    := \033[0;31m
CYAN   := \033[0;36m
NC     := \033[0m

help: ## 🆘 Muestra esta ayuda
	@echo "$(CYAN)MayordomIA v1.0 - Comandos disponibles$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# ─── Instalación ──────────────────────────────────────────────

install: install-backend install-dashboard ## 📦 Instala todas las dependencias

install-backend: ## 📦 Instala dependencias del backend
	@echo "$(YELLOW)📦 Instalando dependencias Python...$(NC)"
	cd backend && pip install -r requirements.txt
	@echo "$(GREEN)✅ Backend listo$(NC)"

install-dashboard: ## 📦 Instala dependencias del dashboard
	@echo "$(YELLOW)📦 Instalando dependencias Node...$(NC)"
	cd dashboard && npm install
	@echo "$(GREEN)✅ Dashboard listo$(NC)"

# ─── Ejecución ─────────────────────────────────────────────────

run: ## 🚀 Ejecuta backend y dashboard en paralelo
	@echo "$(CYAN)🚀 Iniciando MayordomIA...$(NC)"
	@echo "  Backend → http://localhost:8000"
	@echo "  Dashboard → http://localhost:3000"
	@trap 'kill 0' EXIT; \
	(cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000) & \
	(cd dashboard && npm run dev) & \
	wait

run-backend: ## 🐍 Ejecuta solo el backend
	@echo "$(CYAN)🐍 Iniciando backend → http://localhost:8000$(NC)"
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-dashboard: ## 🖥 Ejecuta solo el dashboard
	@echo "$(CYAN)🖥 Iniciando dashboard → http://localhost:3000$(NC)"
	cd dashboard && npm run dev

# ─── Docker ───────────────────────────────────────────────────

docker-up: ## 🐳 Levanta todo con Docker
	@echo "$(CYAN)🐳 Levantando servicios...$(NC)"
	docker compose up -d
	@echo "$(GREEN)✅ Servicios corriendo$(NC)"
	@echo "  Backend → http://localhost:8000"
	@echo "  Dashboard → http://localhost:3000"

docker-down: ## 🐳 Detiene todos los servicios
	docker compose down

docker-logs: ## 📋 Ver logs de Docker
	docker compose logs -f

docker-rebuild: ## 🔄 Reconstruye las imágenes Docker
	docker compose build --no-cache
	docker compose up -d

# ─── Firebase ─────────────────────────────────────────────────

firestore-deploy-rules: ## 🔒 Despliega reglas de Firestore
	firebase deploy --only firestore:rules

firestore-deploy-indexes: ## 📇 Despliega índices de Firestore
	firebase deploy --only firestore:indexes

# ─── Calidad ──────────────────────────────────────────────────

lint-backend: ## 🔍 Linting del backend
	cd backend && python -m ruff check app/ || echo "ruff no instalado"
	cd backend && python -m mypy app/ --ignore-missing-imports || echo "mypy no instalado"

lint-dashboard: ## 🔍 Linting del dashboard
	cd dashboard && npm run lint || echo "ESLint no configurado aún"

lint: lint-backend lint-dashboard ## 🔍 Linting completo

# ─── Limpieza ─────────────────────────────────────────────────

clean: ## 🧹 Limpia archivos temporales
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dashboard/.next 2>/dev/null || true
	rm -rf dashboard/node_modules/.cache 2>/dev/null || true
	@echo "$(GREEN)✅ Limpieza completa$(NC)"

# ─── Información ──────────────────────────────────────────────

info: ## ℹ️ Información del proyecto
	@echo "$(CYAN)MayordomIA v1.0$(NC)"
	@echo "  Lema: No está diseñado para almacenar datos, sino para"
	@echo "  comprender la actividad financiera del usuario, aprender"
	@echo "  de ella y ayudarle a tomar mejores decisiones."
	@echo ""
	@echo "$(YELLOW)Rutas:$(NC)"
	@echo "  API Docs → http://localhost:8000/docs"
	@echo "  Health   → http://localhost:8000/health"
	@echo "  Dashboard → http://localhost:3000"

docs: ## 📚 Abre documentación (README)
	@echo "$(CYAN)📚 Abriendo README.md...$(NC)"
	@cat README.md | head -80
