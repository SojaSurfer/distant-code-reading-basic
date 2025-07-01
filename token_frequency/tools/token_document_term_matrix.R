# load libraries
library(readxl)
library(writexl)
library(dplyr)
library(tidyr)
library(stringr)
library(tools)

# define input + output folders

# input path:
input_folder <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/absolute_frequencies/command_tokens/frequency_tables/"

# output path:
output_file <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/absolute_frequencies/command_tokens/document_term_matrix/DTM.xlsx"

# define freq_files as all files ending in ".xlsx"

freq_files <- list.files(
  path = input_folder,
  pattern = "\\.xlsx$",
  full.names = TRUE
)

# read each file

freq_list <- lapply(freq_files, function(file) {
  
  # read file
  df <- read_excel(file)
  
  # if file is empty, skip it
  if (nrow(df) == 0) {
    message(paste("Skipping empty file:", basename(file)))
    return(NULL)
  }
  
  # standardize column names (lowercase)
  names(df) <- tolower(names(df))
  
  # check columns
  if (!"token" %in% names(df)) {
    stop(paste("Missing 'token' column in file:", basename(file)))
  }
  if (!"frequency" %in% names(df)) {
    stop(paste("Missing 'frequency' column in file:", basename(file)))
  }
  
  # add document name
  df$document <- file_path_sans_ext(basename(file))
  
  return(df)
})

# remove empty files
freq_list <- freq_list[!sapply(freq_list, is.null)]

# combine all frequency tables into one

long_table <- bind_rows(freq_list)

# optional: inspect
cat("Long table preview:\n")
print(head(long_table))

# pivot wider: long table to DTM

dtm <- long_table %>%
  pivot_wider(
    names_from = token,
    values_from = frequency,
    values_fill = list(frequency = 0)
  ) %>%
  arrange(document)

# optional: inspect DTM
cat("DTM preview:\n")
print(head(dtm))

# save DTM as xlsx-file

write_xlsx(dtm, output_file)

cat(paste("DTM saved to:", output_file, "\n"))

### FOLLOW-UP: Add game_id column to DTM ###

# Path to metadata spreadsheet
metadata_file <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/metadata.xlsx"

# Read metadata (expects columns: name, game_id)
metadata <- read_excel(metadata_file)
names(metadata) <- tolower(names(metadata))  # standardize names

# Make sure metadata 'name' matches DTM's 'document' column
metadata <- metadata %>%
  mutate(document = file_path_sans_ext(name))  # strip file extensions

# Join DTM with metadata to get game_id
dtm_with_id <- left_join(dtm, metadata %>% select(document, game_id), by = "document") %>%
  arrange(game_id) %>% # sorts by game_id
  select(game_id, document, everything())

# Reorder columns: game_id, document, tokens...
dtm_with_id <- dtm_with_id %>%
  select(game_id, document, everything())

# Save final version
output_file_with_id <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/absolute_frequencies/command_tokens/document_term_matrix/DTM.xlsx"
write_xlsx(dtm_with_id, output_file_with_id)

cat(paste("DTM with game_id column saved to:", output_file_with_id, "\n"))


### FINAL STEP: Merge rows by game_id (DTM_merged with readable names) ###

# Read the saved DTM with game_id
dtm_with_id <- read_excel(output_file_with_id)

# Helper: extract common prefix before first digit
extract_common_prefix <- function(docs) {
  # Remove everything from first digit onwards
  prefixes <- str_extract(docs, "^[^0-9]+")
  # Return the most common prefix (or first one if they're all the same)
  if (length(unique(prefixes)) == 1) {
    return(unique(prefixes))
  } else {
    return(prefixes[1])
  }
}

# Group by game_id and sum all token columns
dtm_merged <- dtm_with_id %>%
  select(-document) %>%                 # drop document column (not useful in merge)
  group_by(game_id) %>%
  summarise(across(everything(), sum), .groups = "drop") %>%
  arrange(game_id)

# Define output path
output_file_merged <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/absolute_frequencies/command_tokens/document_term_matrix/DTM_merged.xlsx"

# Save merged DTM
write_xlsx(dtm_merged, output_file_merged)

cat(paste("Merged DTM with readable names saved to:", output_file_merged, "\n"))

# Read the DTM with game_id
dtm_with_id <- read_excel(output_file_with_id)

# Aggregate token counts by game_id
dtm_merged <- dtm_with_id %>%
  select(-document) %>%               # drop document since we merge all positions
  group_by(game_id) %>%
  summarise(across(where(is.numeric), sum), .groups = "drop") %>%
  arrange(game_id)

# Read game_id table
lookup_file <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/game_id.xlsx"
game_lookup <- read_excel(lookup_file) %>%
  mutate(game_id = as.character(game_id))  # make sure types match

# join the game_name to the merged DTM
dtm_final <- dtm_merged %>%
  mutate(game_id = as.character(game_id)) %>%
  left_join(game_lookup, by = "game_id") %>%
  relocate(game_id, name)  # put names at front for convenience

# Save final merged + named DTM
output_file_final <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/absolute_frequencies/command_tokens/document_term_matrix/DTM_merged.xlsx"
write_xlsx(dtm_final, output_file_final)

cat(paste("Merged DTM with game names saved to:", output_file_final, "\n"))
