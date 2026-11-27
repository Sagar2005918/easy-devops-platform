variable "aws_region" {
  description = "AWS region for the demo EKS cluster."
  type        = string
  default     = "ap-south-1"
}

variable "cluster_name" {
  type    = string
  default = "easy-devops-task-api"
}

variable "kubernetes_version" {
  description = "EKS Kubernetes minor version supported by your AWS region."
  type        = string
  default     = "1.31"
}

variable "allowed_admin_cidrs" {
  description = "Trusted public IPv4 CIDR(s), for example [\"203.0.113.10/32\"]. Required to restrict public EKS API access."
  type        = list(string)
  validation {
    condition     = length(var.allowed_admin_cidrs) > 0
    error_message = "Set at least one trusted CIDR; do not expose the EKS API to every IP."
  }
}
