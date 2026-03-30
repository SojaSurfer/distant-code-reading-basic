# Global line frequency merged
# Load libraries
library(readxl)
library(writexl)
library(dplyr)
library(tools)

# Set input path
input_folder <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/tokens_per_line/frequency_tables/"

# Set output path for the total line counts
output_file <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/tokens_per_line/global_line_counts.xlsx"

# Create list of all .xlsx files (one for each game)
freq_files <- list.files(
  path = input_folder,
  pattern = "\\.xlsx$",
  full.names = TRUE
)

# Read and process all files, extracting the line count for each game
line_counts <- lapply(freq_files, function(file) {
  # Read the file
  df <- read_excel(file)
  
  # If the file is not empty, process it
  if (nrow(df) > 0) {
    # Extract game name from file name (without extension)
    document <- file_path_sans_ext(basename(file))
    
    # Take the single value from the 'lines' column (it's the only value in the file)
    line_count <- df$lines[1]  # Assumes 'lines' column has a single value
    
    # Return the result as a data frame
    return(data.frame(document = document, line_count = line_count))
  }
  return(NULL)
})

# Remove any NULL entries from the list (in case some files were empty)
line_counts <- line_counts[!sapply(line_counts, is.null)]

# Combine the individual game summaries into one data frame
line_counts_table <- do.call(rbind, line_counts)

# Save the summary table with game names and line counts
write_xlsx(line_counts_table, output_file)

# Print the result
print(line_counts_table)

# add game_id column
# path to metadata
metadata_file <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/metadata.xlsx"

# read metadata
metadata <- read_excel(metadata_file)

# make sure metadata 'name' matches the 'document' column
metadata <- metadata %>%
  mutate(document = file_path_sans_ext(name))

# join dtm with metadata
line_counts_table_with_id <- left_join(line_counts_table, metadata %>% select(document, game_id), by = "document") %>%
  arrange(game_id) %>% select(game_id, document, everything())

# reorder columns
line_counts_table_with_id <- line_counts_table_with_id %>%
  select(game_id, document, everything())

# save dtm
write_xlsx(line_counts_table_with_id, output_file)

# merge rows by game_id
# read dtm
line_counts_table_with_id <- read_excel(output_file)

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
line_counts_table_merged <- line_counts_table_with_id %>%
  # drop document column
  select(-document) %>%
  group_by(game_id) %>%
  summarise(across(everything(), sum), .groups = "drop") %>%
  arrange(game_id)

# set output path
output_file_merged <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/tokens_per_line/global_line_counts_table_merged.xlsx"

# save merged dtm
write_xlsx(line_counts_table_merged, output_file_merged)
