# load libraries
library(readxl)
library(writexl)
library(dplyr)
library(stringr)
library(tools)

# input path:
input_folder <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/dataset/"

# output path:
output_folder <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/absolute_frequencies/command_tokens/frequency_tables/"

# get list of all .xlsx files (recursively, if you have subfolders):
file_list <- list.files(
  path = input_folder,
  pattern = "\\.xlsx$",
  full.names = TRUE,
  recursive = TRUE
)

# loop over each file 

for (file_path in file_list) {
  
  # extract file name 
  file_name <- basename(file_path)
  
  # output path
  output_path <- file.path(output_folder, file_name)
  
  # make sure the output folder exists
  dir.create(output_folder, recursive = TRUE, showWarnings = FALSE)
  
  # read Excel
  data <- read_excel(file_path)
  
  # filter for syntax
  # "C" = commands 
  # "O" = operators
  # "V" = variables
  # "N" = numbers
  # "P" = punctuations
  # "S" = strings
  # "D" = data
  # "BASIC" = BASIC
  # "ASSEMBLY" = ASSEMBLY
  data_filtered <- data %>%
    filter(grepl("^S", syntax) & language == "BASIC")
  
  # count token frequencies
  freq_table <- data_filtered %>%
    count(token, name = "frequency") %>%
    arrange(desc(frequency))
  
  # save frequency table
  write_xlsx(freq_table, output_path)
  
  cat("saved:", output_path, "\n")
}
