{{/*
Expand the name of the chart.
*/}}
{{- define "provisioning-agent.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "provisioning-agent.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "provisioning-agent.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels applied to all resources in this chart.
*/}}
{{- define "provisioning-agent.labels" -}}
helm.sh/chart: {{ include "provisioning-agent.chart" . }}
{{ include "provisioning-agent.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels used for pod selection and service routing.
*/}}
{{- define "provisioning-agent.selectorLabels" -}}
app.kubernetes.io/name: {{ include "provisioning-agent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use.
*/}}
{{- define "provisioning-agent.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "provisioning-agent.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Render the immutable or tagged image reference for this release.
*/}}
{{- define "provisioning-agent.image" -}}
{{- if .Values.image.digest }}
{{- printf "%s@%s" .Values.image.repository .Values.image.digest -}}
{{- else -}}
{{- printf "%s:%s" .Values.image.repository (default .Chart.AppVersion .Values.image.tag) -}}
{{- end }}
{{- end }}

{{/*
Resolve image pull policy, allowing the umbrella chart to supply a global default.
*/}}
{{- define "provisioning-agent.imagePullPolicy" -}}
{{- coalesce .Values.image.pullPolicy .Values.global.imagePullPolicy "IfNotPresent" -}}
{{- end }}
