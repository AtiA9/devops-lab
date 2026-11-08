terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # the state lives in S3, not on your laptop. Create the bucket once by hand, then: terraform init
  backend "s3" {
    bucket = "CHANGE-ME-taskboard-tfstate"
    key    = "taskboard/terraform.tfstate"
    region = "eu-central-1"
  }
}

provider "aws" {
  region = var.region
}
