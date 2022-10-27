export DOCKER_USERNAME ?= salant
export DOCKER_HOSTNAME ?= github.ibm.com
export DOCKER_PASSWORD ?= XXXXX
# FOR github.com - i.e. docker khostname ghcr.io
# export DOCKER_PASSWORD ?= XXXXX
export DOCKER_NAMESPACE ?= salant
export DOCKER_TAGNAME ?= v1

export HELM_TAGNAME ?= 0.0.1
export HELM_TOKEN ?= XXXXX
export HELM_USERNAME ?= elsalant
export HELM_HOSTNAME ?= ghcr.io

export REPO_HOSTNAME ?= ghcr.io
export REPO_USERNAME ?= elsalant

DOCKER_IMG_NAME ?= kafka-to-s3
PRODUCER_DOCKER_IMG_NAME ?= kafka-producer
CHART_IMG_NAME ?= kafka-to-s3-chart
DOCKER_FILE ?= Dockerfile
PRODUCER_DOCKER_FILE ?= Dockerfile.producer
DOCKER_CONTEXT ?= .
DOCKER_LOCATION ?= build
APP_IMG ?= ${REPO_HOSTNAME}/${REPO_USERNAME}/${DOCKER_IMG_NAME}:${DOCKER_TAGNAME}
PRODUCER_APP_IMG ?= ${REPO_HOSTNAME}/${REPO_USERNAME}/${PRODUCER_DOCKER_IMG_NAME}:${DOCKER_TAGNAME}
CHART_IMG ?= ${REPO_HOSTNAME}/${REPO_USERNAME}/${CHART_IMG_NAME}:${HELM_TAGNAME}
CHART ?= ${DOCKER_IMG_NAME}

.PHONY: docker-all
docker-all: docker-build docker-push

.PHONY: docker-build
docker-build:
	DOCKER_BUILDKIT=1 docker build $(DOCKER_CONTEXT) -t ${APP_IMG} -f $(DOCKER_LOCATION)/$(DOCKER_FILE)

.PHONY: docker-build-producer
docker-build-producer:
	docker build $(DOCKER_CONTEXT) -t ${PRODUCER_APP_IMG} -f $(DOCKER_LOCATION)/$(PRODUCER_DOCKER_FILE)

.PHONY: docker-push
docker-push:
	docker login --username ${DOCKER_USERNAME} --password ${DOCKER_PASSWORD} ghcr.io/elsalant
	docker push ${APP_IMG}

.PHONY: docker-push-producer
docker-push-producer:
	docker push ${PRODUCER_APP_IMG}

.PHONY: docker-rmi
docker-rmi:
	docker rmi ${APP_IMG} || true

HELM_VALUES ?= 

CHART := ${DOCKER_HOSTNAME}/${DOCKER_IMG_NAME}
HELM_RELEASE ?= rel1-${DOCKER_IMG_NAME}
TEMP := /tmp

export HELM_EXPERIMENTAL_OCI=1
export GODEBUG=x509ignoreCN=0

.PHONY: helm-login
helm-login: 
ifneq (${HELM_PASSWORD},)
	helm registry login -u "${HELM_USERNAME}" -p "${HELM_PASSWORD}" ${HELM_HOSTNAME}
endif
.PHONY: helm-verify
helm-verify: 
	helm lint ${CHART}
	helm install ${HELM_RELEASE} ${CHART} ${HELM_VALUES}

.PHONY: helm-uninstall
helm-uninstall: 
	helm uninstall ${HELM_RELEASE} || true

.PHONY: helm-install
helm-install: 
	helm install ${HELM_RELEASE} ${CHART} ${HELM_VALUES}

.PHONY: helm-chart-push
helm-chart-push: helm-login 
	helm chart save ${CHART} ${CHART_IMG}
	helm chart list ${CHART_IMG}
	helm chart push ${CHART_IMG}
	helm chart remove ${CHART_IMG}
	helm uninstall ${HELM_RELEASE} || true

.PHONY: helm-chart-pull
helm-chart-pull: helm-login 
	helm chart pull ${CHART_IMG}
	helm chart list

.PHONY: helm-chart-list
helm-chart-list: 
	helm chart list

.PHONY: helm-chart-install
helm-chart-install: 
	helm chart export --destination=${TEMP} ${CHART_IMG}
	helm install ${HELM_RELEASE} ${TEMP}/${CHART} ${HELM_VALUES}
	helm list

.PHONY: helm-template
helm-template: 
	helm template ${HELM_RELEASE} ${CHART} ${HELM_VALUES}

.PHONY: helm-debug
helm-debug: helm
	helm template ${HELM_RELEASE} ${CHART} ${HELM_VALUES} --debug

.PHONY: helm-actions
helm-actions:
	helm show values ${CHART} | yq -y -r .actions

.PHONY: helm-all
