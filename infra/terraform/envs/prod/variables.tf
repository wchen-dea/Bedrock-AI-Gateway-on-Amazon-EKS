variable "aws_region" { type = string }
variable "cluster_name" { type = string }
variable "vpc_id" { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "bedrock_model_arns" { type = list(string) }
