# Stage 5 - TaskBoard on one EC2 instance in the default VPC
# (the default VPC is enough for a single public instance; a dedicated VPC comes with private subnets)

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

resource "aws_security_group" "taskboard" {
  name        = "taskboard"
  description = "TaskBoard API and SSH from my IP only"

  ingress {
    description = "TaskBoard API"
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH from my IP only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# No IAM role: the instance only pulls a public image, it does not call other AWS services.
resource "aws_instance" "taskboard" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.taskboard.id]

  user_data = templatefile("${path.module}/user_data.sh", { image = var.image })

  tags = {
    Name = "taskboard"
  }
}
