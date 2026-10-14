{{- define "ai.name" -}}ai-system{{- end }}
{{- define "ai.labels" -}}
app.kubernetes.io/name: {{ include "ai.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
