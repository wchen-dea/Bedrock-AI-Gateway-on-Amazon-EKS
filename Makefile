SHELL := /bin/bash
IMAGE ?= ai-system:dev
MINIKUBE_DRIVER ?= docker

.PHONY: sync test lint minikube-up minikube-deploy minikube-forward minikube-down helm-lint

sync:
	uv sync
test:
	uv run pytest -q
lint:
	uv run ruff check app
minikube-up:
	minikube start --driver=$(MINIKUBE_DRIVER)
minikube-deploy:
	minikube image build -t $(IMAGE) .
	helm upgrade --install ai-system deploy/helm/ai-system -n ai-system --create-namespace \
		-f deploy/helm/ai-system/values-local.yaml
	kubectl rollout restart deployment/ai-system -n ai-system
	kubectl rollout status deployment/ai-system -n ai-system --timeout=120s
minikube-forward:
	kubectl port-forward -n ai-system svc/ai-system 8080:80
minikube-down:
	-helm uninstall ai-system -n ai-system
	minikube delete
helm-lint:
	helm lint deploy/helm/ai-system -f deploy/helm/ai-system/values-local.yaml
