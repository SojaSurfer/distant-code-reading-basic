# BASIC commands dtm

# load libraries
library(readxl)
library(writexl)
library(dplyr)
library(tidyr)
library(stringr)
library(tools)

# set input path:
input_folder <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/absolute_frequencies/command_tokens/frequency_tables/"

# set output path:
output_file <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/absolute_frequencies/command_tokens/document_term_matrix/DTM.xlsx"

# create list of all .xlsx files
freq_files <- list.files(
  path = input_folder,
  pattern = "\\.xlsx$",
  full.names = TRUE
)

# read files
freq_list <- lapply(freq_files, function(file) {
  df <- read_excel(file)
  
  # skip empty files
  if (nrow(df) == 0) {
    return(NULL)
  }
  
  # add document name
  df$document <- file_path_sans_ext(basename(file))
  
  return(df)
})

# remove empty files
freq_list <- freq_list[!sapply(freq_list, is.null)]

# combine all frequency tables
long_table <- bind_rows(freq_list)

# pivot long table to dtm
dtm <- long_table %>%
  pivot_wider(
    names_from = token,
    values_from = frequency,
    values_fill = list(frequency = 0)
  ) %>%
  arrange(document)

# save dtm
write_xlsx(dtm, output_file)

# add game_id column
# path to metadata
metadata_file <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/metadata.xlsx"

# read metadata
metadata <- read_excel(metadata_file)

# make sure metadata 'name' matches DTM's 'document' column
metadata <- metadata %>%
  mutate(document = file_path_sans_ext(name))

# join dtm with metadata
dtm_with_id <- left_join(dtm, metadata %>% select(document, game_id), by = "document") %>%
                         arrange(game_id) %>% select(game_id, document, everything())

# reorder columns
dtm_with_id <- dtm_with_id %>%
  select(game_id, document, everything())

# save dtm
write_xlsx(dtm_with_id, output_file)

# merge rows by game_id
# read dtm
dtm_with_id <- read_excel(output_file)

# extract common prefix before first digit
extract_common_prefix <- function(docs) {
  # remove everything from first digit onwards
  prefixes <- str_extract(docs, "^[^0-9]+")
  # return most common prefix or first one if they're all the same
  if (length(unique(prefixes)) == 1) {
    return(unique(prefixes))
  } else {
    return(prefixes[1])
  }
}

# group by game_id and sum all token columns
dtm_merged <- dtm_with_id %>%
  # drop document column
  select(-document) %>%
  group_by(game_id) %>%
  summarise(across(everything(), sum), .groups = "drop") %>%
  arrange(game_id)

# set output path
output_file_merged <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/absolute_frequencies/command_tokens/document_term_matrix/DTM_merged.xlsx"

# save merged dtm
write_xlsx(dtm_merged, output_file_merged)

# reattach 'document' row to the corresponding game_id
# read dtm_merged
dtm_with_id <- read_excel(output_file)

# aggregate token counts by game_id
dtm_merged <- dtm_with_id %>%
  select(-document) %>%
  group_by(game_id) %>%
  summarise(across(where(is.numeric), sum), .groups = "drop") %>%
  arrange(game_id)

# read game_id from lookup file
lookup_file <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/game_id.xlsx"
game_lookup <- read_excel(lookup_file) %>%
  mutate(game_id = as.character(game_id))

# join name to the merged dtm
dtm_final <- dtm_merged %>%
  mutate(game_id = as.character(game_id)) %>%
  left_join(game_lookup %>% select(game_id, name), by = "game_id") %>%
  relocate(game_id, name)

# save final dtm
write_xlsx(dtm_final, output_file_merged)