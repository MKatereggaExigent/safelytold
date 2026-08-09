{{- define "safelytold.name" -}}safelytold{{- end -}}
{{- define "safelytold.labels" -}}
app.kubernetes.io/part-of: {{ include "safelytold.name" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}
