# ============================================================================
# 多智能体应用开发系统 - Makefile
# ============================================================================

# 变量
PYTHON = python3
PIP = pip
DOCKER = docker
DOCKER_COMPOSE = docker-compose
DOCKER_COMPOSE_DEV = docker-compose -f docker-compose.dev.yml

# 颜色
GREEN = \033[0;32m]
YELLOW = \033[0;33m]
RED = \033[0;31m]
NC = \033[0m] # No Color

# ============================================================================
# 帮助命令
# ============================================================================

.PHONY: help
help: ## 显示帮助信息
	@echo "$(GREEN)多智能体应用开发系统$(NC)"
	@echo "=========================="
	@echo ""
	@echo "$(YELLOW)使用方法:$(NC)"
	@echo "  make [command]"
	@echo ""
	@echo "$(YELLOW)可用命令:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# ============================================================================
# 开发命令
# ============================================================================

.PHONY: install
install: ## 安装依赖
	$(PIP) install -r requirements.txt

.PHONY: install-dev
install-dev: ## 安装开发依赖
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt

.PHONY: setup
setup: ## 初始化项目设置
	cp -n .env.example .env || true
	mkdir -p data/states logs config
	@echo "$(GREEN)项目初始化完成!$(NC)"
	@echo "$(YELLOW)请编辑 .env 文件配置您的 API Key$(NC)"

# ============================================================================
# 运行命令
# ============================================================================

.PHONY: run
run: ## 运行应用
	$(PYTHON) main.py

.PHONY: run-dev
run-dev: ## 运行应用 (开发模式)
	$(PYTHON) main.py --interactive

.PHONY: run-example
run-example: ## 运行示例
	$(PYTHON) examples/requirements_example.py

# ============================================================================
# 测试命令
# ============================================================================

.PHONY: test
test: ## 运行所有测试
	pytest

.PHONY: test-verbose
test-verbose: ## 运行所有测试 (详细输出)
	pytest -v

.PHONY: test-coverage
test-coverage: ## 运行测试并生成覆盖率报告
	pytest --cov=agents --cov-report=html --cov-report=term

.PHONY: test-unit
test-unit: ## 运行单元测试
	pytest tests/unit

.PHONY: test-integration
test-integration: ## 运行集成测试
	pytest tests/integration

# ============================================================================
# 代码质量命令
# ============================================================================

.PHONY: lint
lint: ## 运行代码检查
	flake8 agents/ utils/ config/ tests/
	mypy agents/ utils/ config/

.PHONY: format
format: ## 格式化代码
	black agents/ utils/ config/ tests/ examples/
	isort agents/ utils/ config/ tests/ examples/

.PHONY: check
check: lint ## 检查代码质量
	@echo "$(GREEN)代码质量检查完成!$(NC)"

# ============================================================================
# Docker 命令 (生产环境)
# ============================================================================

.PHONY: docker-build
docker-build: ## 构建 Docker 镜像
	$(DOCKER_COMPOSE) build

.PHONY: docker-up
docker-up: ## 启动所有服务
	$(DOCKER_COMPOSE) up -d

.PHONY: docker-down
docker-down: ## 停止所有服务
	$(DOCKER_COMPOSE) down

.PHONY: docker-restart
docker-restart: ## 重启所有服务
	$(DOCKER_COMPOSE) restart

.PHONY: docker-logs
docker-logs: ## 查看日志
	$(DOCKER_COMPOSE) logs -f

.PHONY: docker-ps
docker-ps: ## 查看运行中的容器
	$(DOCKER_COMPOSE) ps

.PHONY: docker-clean
docker-clean: ## 清理 Docker 资源
	$(DOCKER_COMPOSE) down -v --rmi local
	@echo "$(GREEN)Docker 资源已清理!$(NC)"

# ============================================================================
# Docker 命令 (开发环境)
# ============================================================================

.PHONY: dev-build
dev-build: ## 构建开发环境镜像
	$(DOCKER_COMPOSE_DEV) build

.PHONY: dev-up
dev-up: ## 启动开发环境
	$(DOCKER_COMPOSE_DEV) up -d

.PHONY: dev-down
dev-down: ## 停止开发环境
	$(DOCKER_COMPOSE_DEV) down

.PHONY: dev-restart
dev-restart: ## 重启开发环境
	$(DOCKER_COMPOSE_DEV) restart

.PHONY: dev-logs
dev-logs: ## 查看开发环境日志
	$(DOCKER_COMPOSE_DEV) logs -f

.PHONY: dev-ps
dev-ps: ## 查看开发环境容器
	$(DOCKER_COMPOSE_DEV) ps

.PHONY: dev-shell
dev-shell: ## 进入应用容器
	$(DOCKER_COMPOSE_DEV) exec app bash

.PHONY: dev-db
dev-db: ## 连接数据库
	$(DOCKER_COMPOSE_DEV) exec postgres psql -U postgres -d multi_agent_dev

.PHONY: dev-redis
dev-redis: ## 连接 Redis
	$(DOCKER_COMPOSE_DEV) exec redis redis-cli

# ============================================================================
# 数据库命令
# ============================================================================

.PHONY: db-migrate
db-migrate: ## 运行数据库迁移
	alembic upgrade head

.PHONY: db-revision
db-revision: ## 创建新的迁移
	alembic revision --autogenerate -m "$(message)"

.PHONY: db-rollback
db-rollback: ## 回滚数据库迁移
	alembic downgrade -1

.PHONY: db-reset
db-reset: ## 重置数据库
	alembic downgrade base
	alembic upgrade head

# ============================================================================
# 清理命令
# ============================================================================

.PHONY: clean
clean: ## 清理临时文件
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache/ .mypy_cache/ .coverage htmlcov/
	rm -rf logs/*.log
	@echo "$(GREEN)临时文件已清理!$(NC)"

.PHONY: clean-all
clean-all: clean docker-clean ## 清理所有临时文件和Docker资源
	@echo "$(GREEN)所有清理完成!$(NC)"

# ============================================================================
# 文档命令
# ============================================================================

.PHONY: docs
docs: ## 生成文档
	mkdocs build

.PHONY: docs-serve
docs-serve: ## 启动文档服务器
	mkdocs serve

# ============================================================================
# 部署命令
# ============================================================================

.PHONY: deploy-staging
deploy-staging: ## 部署到预发布环境
	@echo "$(YELLOW)部署到预发布环境...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.staging.yml up -d

.PHONY: deploy-production
deploy-production: ## 部署到生产环境
	@echo "$(RED)部署到生产环境...$(NC)"
	@echo "$(YELLOW)请确认!$(NC)"
	@read -p "继续? [y/N]: " confirm && [ "$$confirm" = "y" ] || exit 1
	$(DOCKER_COMPOSE) -f docker-compose.yml up -d

# ============================================================================
# 监控命令
# ============================================================================

.PHONY: monitor
monitor: ## 打开监控面板
	@echo "$(GREEN)Grafana: http://localhost:3000$(NC)"
	@echo "$(GREEN)Prometheus: http://localhost:9090$(NC)"
	@echo "$(GREEN)Flower: http://localhost:5555$(NC)"
	@echo "$(GREEN)Adminer: http://localhost:8080$(NC)"

# ============================================================================
# 备份命令
# ============================================================================

.PHONY: backup-db
backup-db: ## 备份数据库
	@mkdir -p backups
	$(DOCKER_COMPOSE) exec postgres pg_dump -U postgres multi_agent > backups/db_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)数据库备份完成!$(NC)"

.PHONY: restore-db
restore-db: ## 恢复数据库
	$(DOCKER_COMPOSE) exec -T postgres psql -U postgres multi_agent < $(file)
	@echo "$(GREEN)数据库恢复完成!$(NC)"

# ============================================================================
# 快捷命令
# ============================================================================

.PHONY: start
start: setup dev-up ## 快速启动项目
	@echo "$(GREEN)项目已启动!$(NC)"
	@echo "$(GREEN)应用: http://localhost:8000$(NC)"
	@echo "$(GREEN)Adminer: http://localhost:8080$(NC)"
	@echo "$(GREEN)Redis Commander: http://localhost:8081$(NC)"

.PHONY: stop
stop: dev-down ## 停止项目
	@echo "$(GREEN)项目已停止!$(NC)"

.PHONY: restart
restart: dev-restart ## 重启项目
	@echo "$(GREEN)项目已重启!$(NC)"

.PHONY: status
status: dev-ps ## 查看项目状态
