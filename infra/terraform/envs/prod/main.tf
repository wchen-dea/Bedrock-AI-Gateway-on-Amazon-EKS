data "aws_caller_identity" "current" {}

resource "aws_ecr_repository" "ai_system" {
  name                 = "ai-system"
  image_tag_mutability = "IMMUTABLE"
  image_scanning_configuration { scan_on_push = true }
  encryption_configuration { encryption_type = "AES256" }
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"
  name               = var.cluster_name
  kubernetes_version = "1.34"
  vpc_id             = var.vpc_id
  subnet_ids         = var.private_subnet_ids
  endpoint_public_access  = false
  endpoint_private_access = true
  enable_irsa = true
  eks_managed_node_groups = {
    system = {
      instance_types = ["m7i.large"]
      min_size = 2
      max_size = 6
      desired_size = 2
      labels = { workload = "system" }
    }
    apps = {
      instance_types = ["m7i.xlarge"]
      min_size = 2
      max_size = 20
      desired_size = 2
      labels = { workload = "apps" }
    }
  }
}

resource "aws_iam_role" "bedrock_runtime" {
  name = "${var.cluster_name}-bedrock-runtime"
  assume_role_policy = jsonencode({
    Version = "2012-10-17", Statement = [{
      Effect = "Allow", Principal = { Federated = module.eks.oidc_provider_arn }, Action = "sts:AssumeRoleWithWebIdentity",
      Condition = { StringEquals = { "${module.eks.oidc_provider}:sub" = "system:serviceaccount:ai-system:ai-system" } }
    }]
  })
}
resource "aws_iam_role_policy" "bedrock_runtime" {
  role = aws_iam_role.bedrock_runtime.id
  policy = jsonencode({Version="2012-10-17",Statement=[{
    Effect="Allow",Action=["bedrock:InvokeModel","bedrock:InvokeModelWithResponseStream"],Resource=var.bedrock_model_arns
  }]})
}

output "cluster_name" { value = module.eks.cluster_name }
output "ecr_url" { value = aws_ecr_repository.ai_system.repository_url }
output "bedrock_role_arn" { value = aws_iam_role.bedrock_runtime.arn }
