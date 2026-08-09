variable "region" {
  type = string
  default = null
}

variable "environment" {
  type = string
  default = null
}

variable "administrators" {
  type = list(string)
  default = []
}
