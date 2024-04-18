variable "read_only" {
    type = bool
    default = false
    description = "If true, the script will generate LLM prompts but not actually send them to the LLM."
}