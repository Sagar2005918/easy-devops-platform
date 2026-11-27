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
  description = "Your trusted public IPv4 CIDR(s), for example [\"203.0.113.10/32\"]. Set these before applying."
  type        = list(string)
  default     = []
}
