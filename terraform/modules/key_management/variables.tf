variable "region" {
  type = string
  default = null
}

variable "environment" {
  type = string
  default = null
}

variable "key_administrators" {
  type = list(string)
  default = []
}
