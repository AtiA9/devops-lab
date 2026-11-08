variable "region" {
  description = "AWS region"
  type        = string
  default     = "eu-central-1"
}

variable "instance_type" {
  description = "Free tier instance size"
  type        = string
  default     = "t3.micro"
}

variable "image" {
  description = "The image pushed by the pipeline, e.g. ghcr.io/atia9/taskboard:<commit sha>"
  type        = string
}

variable "my_ip_cidr" {
  description = "Your public IP for SSH, as x.x.x.x/32 (curl -s ifconfig.me)"
  type        = string

  validation {
    condition     = can(regex("^\\d+\\.\\d+\\.\\d+\\.\\d+/32$", var.my_ip_cidr))
    error_message = "my_ip_cidr must be a single IP: x.x.x.x/32."
  }
}

variable "key_name" {
  description = "Name of an existing EC2 key pair for SSH"
  type        = string
}
