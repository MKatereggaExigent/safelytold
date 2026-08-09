variable "region" {
  type = string
  default = null
}

variable "environment" {
  type = string
  default = null
}

variable "database_names" {
  type = list(string)
  default = []
}
