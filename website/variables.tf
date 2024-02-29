variable "read_only" {
    type = bool
    default = false
    description = "If true, the script will generate GPT prompts but not actually send them to ChatGPT."
}