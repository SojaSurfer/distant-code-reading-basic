# BASIC commands absolute frequency tables

# load libraries
library(readxl)
library(writexl)
library(dplyr)
library(stringr)
library(tools)

# set input path
input_folder <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/dataset/"

# set output path
output_folder <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/absolute_frequencies/frequency_tables"

# create list of all .xlsx files
file_list <- list.files(
  path = input_folder,
  pattern = "\\.xlsx$",
  full.names = TRUE,
  recursive = TRUE
)

# loop over each file
for (file_path in file_list) {
  
  # get file name
  file_name <- basename(file_path)
  
  # set output path
  output_path <- file.path(output_folder, file_name)
  
  # create output folder
  dir.create(output_folder,
             recursive = TRUE,
             showWarnings = FALSE)
  
  # read xlsx file
  data <- read_excel(file_path)
  
  # filter data for BASIC command tokens in row "syntax"
  # "C" = commands
  # "BASIC" = BASIC
  data_filtered <- data %>%
  filter(grepl("C", syntax) & language == "BASIC")
  
  # count frequency of tokens
  freq_table <- data_filtered %>%
    count(token, name = "frequency") %>%
    arrange(desc(frequency))
  
  # save frequency table
  write_xlsx(freq_table, output_path)
}