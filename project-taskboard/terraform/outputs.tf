output "public_ip" {
  description = "Open http://<public_ip>:5000/health"
  value       = aws_instance.taskboard.public_ip
}
