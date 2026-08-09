variable "region" {
  description = "Deployment region."
  type        = string
}

variable "environment" {
  description = "Environment name."
  type        = string
  default     = "dev"
}
