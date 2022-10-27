export HELM_TAGNAME ?= 0.0.1
export HELM_TOKEN ?= XXXXXXXXXXX
export HELM_USERNAME ?= elsalant
export HELM_HOSTNAME ?= ghcr.io
export HELM_INSTALL_NAME ?= kafka-to-s3
export HELM_PRODUCER_INSTALL_NAME ?= kakfka-producer

export REPO_USERNAME ?= elsalant
export HELM_REPO ?= oci://ghcr.io/$(REPO_USERNAME)

CHART_IMG_NAME ?= kafka-to-s3-chart
HELM_PRODUCER_CHART_NAME ?= kafka-producer-chart
CHART_IMG ?= ${REPO_HOSTNAME}/${REPO_USERNAME}/${CHART_IMG_NAME}-${HELM_TAGNAME}
CHART ?= ${CHART_IMG_NAME}

HELM_VALUES ?= 

HELM_RELEASE ?= ${HELM_INSTALL_NAME}
TEMP := /tmp

export HELM_EXPERIMENTAL_OCI=1
export GODEBUG=x509ignoreCN=0

.PHONY: helm-login
helm-login: 
	ifneq (${HELM_PASSWORD},)
		helm registry login -u "${HELM_USERNAME}" -p "${HELM_PASSWORD}" ${HELM_HOSTNAME}
	endif

.PHONY: helm-uninstall
helm-uninstall: 
	helm uninstall ${HELM_RELEASE} || true

.PHONY: helm-package
helm-package:
	helm package $(HELM_INSTALL_NAME) -d $(TEMP) 

.PHONY: helm-package-producer
helm-package-producer: 
	helm package $(HELM_PRODUCER_CHART_NAME) -d $(TEMP)

.PHONY: helm-push
helm-push:
	helm push ${TEMP}/${CHART_IMG_NAME}-${HELM_TAGNAME}.tgz ${HELM_REPO}

.PHONY: helm-push-producer
helm-push-producer:
	helm push ${TEMP}/${PRODUCER_CHART_IMG_NAME}-${HELM_TAGNAME}.tgz ${HELM_REPO}

.PHONY: helm-install
helm-install:
	helm install $(HELM_RELEASE) ${HELM_REPO}/${CHART_IMG_NAME}

.PHONY: helm-install-producer
helm-install-producer:
	helm install $(HELM_RELEASE) ${HELM_REPO}/${PRODUCER_CHART_IMG_NAME}
