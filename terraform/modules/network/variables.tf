variable "region" {
  type = string
  default = null
}

variable "environment" {
  type = string
  default = null
}

variable "private_cidrs" {
  type = list(string)
  default = []
}
